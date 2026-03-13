# -*- coding: utf-8 -*-
"""
PostgreSQL 저장: 상위 보유자(symbol+rank PK), 지갑별 직전 보유량, 매수/매도 알럿 이력.
상위 100명 전원 보유량 변동 추적 → 매수/매도 알럿 기록.
"""

import logging
from contextlib import contextmanager
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values

from config import DATABASE_URL
from fetchers.base import HolderInfo

logger = logging.getLogger(__name__)

# 알럿 한 건: (alert_type, wallet_address, rank, balance_before, balance_after)
AlertRecord = Tuple[str, str, int, str, str]


@contextmanager
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """테이블 생성 (없을 때만)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 상위 보유자: symbol + rank 를 PK로 매 회차 업데이트
            cur.execute("""
                CREATE TABLE IF NOT EXISTS top_holders (
                    symbol VARCHAR(20) NOT NULL,
                    rank INT NOT NULL,
                    wallet_address TEXT NOT NULL,
                    balance_raw TEXT NOT NULL,
                    balance_human TEXT,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (symbol, rank)
                );
            """)
            # 1위 보유자 스냅샷 (변동 감지 비교용)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS holder_max (
                    symbol VARCHAR(20) PRIMARY KEY,
                    wallet_address TEXT NOT NULL,
                    balance_raw TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            # 매수/매도 알럿 이력 (Grafana 표출용). rank = 해당 시점 순위.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS holder_alerts (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    alert_type VARCHAR(10) NOT NULL,
                    wallet_address TEXT NOT NULL,
                    rank INT,
                    balance_before TEXT,
                    balance_after TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            # 상위 100명 지갑별 "직전 보유량" (변동 감지용)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS holder_last_balance (
                    symbol VARCHAR(20) NOT NULL,
                    wallet_address TEXT NOT NULL,
                    balance_raw TEXT NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (symbol, wallet_address)
                );
            """)
            # 기존 holder_alerts에 rank 컬럼 없으면 추가
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'holder_alerts' AND column_name = 'rank'
                    ) THEN
                        ALTER TABLE holder_alerts ADD COLUMN rank INT;
                    END IF;
                END $$;
            """)
    logger.info("DB 테이블 확인/생성 완료: top_holders, holder_max, holder_alerts, holder_last_balance")


def upsert_top_holders(symbol: str, holders: List[HolderInfo], balance_human_fn) -> None:
    """상위 보유자 10명을 symbol+rank 기준으로 upsert (PK로 계속 업데이트)."""
    if not holders:
        return
    rows = [
        (
            symbol,
            h.rank,
            h.wallet_address,
            h.balance_raw,
            balance_human_fn(h.balance_raw),
        )
        for h in holders
    ]
    with get_connection() as conn:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO top_holders (symbol, rank, wallet_address, balance_raw, balance_human)
                VALUES %s
                ON CONFLICT (symbol, rank)
                DO UPDATE SET
                    wallet_address = EXCLUDED.wallet_address,
                    balance_raw = EXCLUDED.balance_raw,
                    balance_human = EXCLUDED.balance_human,
                    updated_at = NOW();
                """,
                rows,
            )
    logger.info("DB upsert top_holders %s %d명", symbol, len(holders))


def get_holder_max(symbol: str) -> Optional[Tuple[str, str]]:
    """1위 보유자 (wallet_address, balance_raw). 없으면 None."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT wallet_address, balance_raw FROM holder_max WHERE symbol = %s",
                (symbol,),
            )
            row = cur.fetchone()
    return (row[0], row[1]) if row else None


def update_holder_max(symbol: str, wallet_address: str, balance_raw: str) -> None:
    """1위 보유자 갱신."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO holder_max (symbol, wallet_address, balance_raw, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (symbol)
                DO UPDATE SET
                    wallet_address = EXCLUDED.wallet_address,
                    balance_raw = EXCLUDED.balance_raw,
                    updated_at = NOW();
                """,
                (symbol, wallet_address, balance_raw),
            )


def get_holder_last_balance(symbol: str, wallet_address: str) -> Optional[str]:
    """지갑의 직전 보유량. 없으면 None."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT balance_raw FROM holder_last_balance WHERE symbol = %s AND wallet_address = %s",
                (symbol, wallet_address),
            )
            row = cur.fetchone()
    return row[0] if row else None


def update_holder_last_balance(symbol: str, wallet_address: str, balance_raw: str) -> None:
    """지갑 직전 보유량 갱신."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO holder_last_balance (symbol, wallet_address, balance_raw, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (symbol, wallet_address)
                DO UPDATE SET balance_raw = EXCLUDED.balance_raw, updated_at = NOW();
                """,
                (symbol, wallet_address, balance_raw),
            )


def insert_holder_alert(
    symbol: str,
    alert_type: str,
    wallet_address: str,
    balance_before: Optional[str] = None,
    balance_after: Optional[str] = None,
    rank: Optional[int] = None,
) -> None:
    """매수/매도 알럿 이력 저장 (Grafana에서 조회)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO holder_alerts (symbol, alert_type, wallet_address, rank, balance_before, balance_after)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (symbol, alert_type, wallet_address, rank, balance_before, balance_after),
            )
    logger.info("DB 알럿 기록: %s %s rank=%s %s", symbol, alert_type, rank, wallet_address[:16])


def check_and_record_alerts_for_all(
    symbol: str, holders: List[HolderInfo]
) -> List[AlertRecord]:
    """
    상위 100명 전원에 대해 직전 보유량과 비교해, 변동 시 holder_last_balance 갱신 + holder_alerts 삽입.
    Returns:
        [(alert_type, wallet_address, rank, balance_before, balance_after), ...]
    """
    results: List[AlertRecord] = []
    for h in holders:
        wallet = h.wallet_address
        curr_balance = h.balance_raw or "0"
        prev_balance = get_holder_last_balance(symbol, wallet)

        if prev_balance is None:
            update_holder_last_balance(symbol, wallet, curr_balance)
            continue

        prev_balance = prev_balance or "0"
        try:
            prev_val = int(prev_balance)
            curr_val = int(curr_balance)
        except (TypeError, ValueError):
            prev_val = float(prev_balance) if prev_balance else 0
            curr_val = float(curr_balance) if curr_balance else 0

        if curr_val > prev_val:
            update_holder_last_balance(symbol, wallet, curr_balance)
            insert_holder_alert(symbol, "buy", wallet, prev_balance, curr_balance, rank=h.rank)
            results.append(("buy", wallet, h.rank, prev_balance, curr_balance))
        elif curr_val < prev_val:
            update_holder_last_balance(symbol, wallet, curr_balance)
            insert_holder_alert(symbol, "sell", wallet, prev_balance, curr_balance, rank=h.rank)
            results.append(("sell", wallet, h.rank, prev_balance, curr_balance))
        else:
            update_holder_last_balance(symbol, wallet, curr_balance)

    return results
