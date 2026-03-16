# -*- coding: utf-8 -*-
"""
PEPE, WETH 등 상위 100명 보유자 조회 및 전원 보유량 변동 추적(매수/매도 알럿).
"""

import logging
import sys
import time

import schedule

from config import COINS, CHECK_INTERVAL_SECONDS
from fetchers.base import fetch_top_holders
from storage import save_top_holders, _raw_to_human
from db import init_db, upsert_top_holders, check_and_record_alerts_for_all
from alert import send_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def run_check():
    """
    5분 주기:
    1단계) PEPE → WETH → XRP 상위 100명 저장 (연속)
    2단계) 코인별 알럿 업데이트 및 발송
    """
    saved_holders = {}  # symbol -> holders (2단계에서 사용)

    # 1단계: 코인별 상위 100명 보유자만 저장
    for symbol in COINS:
        try:
            logger.info("수집 시작: %s", symbol)
            holders = fetch_top_holders(symbol)
            if not holders:
                logger.info("%s: 조회된 보유자 없음 (API 확인 또는 키 설정 필요)", symbol)
                continue
            save_top_holders(symbol, holders)
            upsert_top_holders(symbol, holders, lambda raw, s=symbol: _raw_to_human(raw, s))
            saved_holders[symbol] = holders
            logger.info("%s 상위 %d명 보유자 저장 완료 (state + DB)", symbol, len(holders))
        except Exception as e:
            logger.exception("Error checking %s: %s", symbol, e)
        time.sleep(2)

    # 2단계: 저장된 기준으로 알럿 업데이트 및 발송
    for symbol in COINS:
        if symbol not in saved_holders:
            continue
        try:
            holders = saved_holders[symbol]
            alerts = check_and_record_alerts_for_all(symbol, holders)
            coin_name = COINS.get(symbol, {}).get("name", symbol)
            to_send = alerts[:10]
            for alert_type, wallet, rank, _before, _after in to_send:
                msg = f"{coin_name} 상위 {rank}위 지갑 보유량 변동"
                send_alert(symbol, alert_type, wallet, msg)
            if alerts:
                logger.info("%s 알럿 %d건 발송%s", symbol, len(to_send), f" (총 {len(alerts)}건 중)" if len(alerts) > 10 else "")
        except Exception as e:
            logger.exception("Error alerts %s: %s", symbol, e)


def main():
    logger.info("PEPE/WETH/XRP 상위 100명 보유자 변동 감지 시작 (5분 주기)")
    init_db()
    # 즉시 1회 실행
    run_check()
    # 주기적 실행
    schedule.every(CHECK_INTERVAL_SECONDS).seconds.do(run_check)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
