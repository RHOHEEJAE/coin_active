# -*- coding: utf-8 -*-
"""최대 보유자(1위) 보유량 저장 및 변동 감지."""

import json
import logging
import os
from typing import Dict, Optional, Tuple

from config import COINS
from fetchers.base import HolderInfo

logger = logging.getLogger(__name__)


def _raw_to_human(balance_raw: str, symbol: str) -> str:
    """원시 보유량을 소수점 적용한 읽기 쉬운 값으로 변환 (예: PEPE 18자리 → 56,116,400,381,117.46)."""
    try:
        decimals = COINS.get(symbol, {}).get("decimals", 18)
        n = int(balance_raw)
        if n == 0:
            return "0"
        div = 10 ** decimals
        whole = n // div
        frac = n % div
        frac_str = str(frac).zfill(decimals).rstrip("0") or "0"
        return f"{whole:,}.{frac_str}" if frac_str != "0" else f"{whole:,}"
    except (ValueError, TypeError):
        return balance_raw

# 기본 저장 경로: 프로젝트 내 state.json
DEFAULT_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")


def _load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load state: %s", e)
        return {}


def _save_state(path: str, state: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Failed to save state: %s", e)


def save_top_holders(
    symbol: str,
    holders: list,
    state_path: str = DEFAULT_STATE_PATH,
) -> None:
    """상위 보유자 목록 전체를 state에 저장 (예: PEPE 10명)."""
    if not holders:
        return
    state = _load_state(state_path)
    key = f"{symbol}_top_holders"
    state[key] = [
        {
            "rank": h.rank,
            "wallet_address": h.wallet_address,
            "balance_raw": h.balance_raw,
            "balance_human": _raw_to_human(h.balance_raw, symbol),
        }
        for h in holders
    ]
    _save_state(state_path, state)


def get_top_holder(holders: list) -> Optional[HolderInfo]:
    """상위 보유자 목록에서 1위만 반환."""
    for h in holders:
        if h.rank == 1:
            return h
    return holders[0] if holders else None


def check_and_update_max_holder(
    symbol: str,
    current_holders: list,
    state_path: str = DEFAULT_STATE_PATH,
) -> Tuple[Optional[str], Optional[str]]:
    """
    현재 1위 보유자와 저장된 이전 보유량을 비교해 변동 시 알럿 타입 반환 및 상태 저장.

    Returns:
        (alert_type, wallet_address): "buy" | "sell" | None, 1위 지갑 주소
    """
    top = get_top_holder(current_holders)
    if not top:
        return None, None

    state = _load_state(state_path)
    key_max = f"{symbol}_max"
    prev = state.get(key_max)  # { "wallet": "...", "balance_raw": "..." }

    # 최초 기록
    if not prev:
        state[key_max] = {
            "wallet_address": top.wallet_address,
            "balance_raw": top.balance_raw,
            "balance_human": _raw_to_human(top.balance_raw, symbol),
        }
        _save_state(state_path, state)
        return None, top.wallet_address

    prev_balance = prev.get("balance_raw") or "0"
    curr_balance = top.balance_raw or "0"

    # 동일 지갑이 1위 유지 → 보유량 변동만 비교
    if prev.get("wallet_address") == top.wallet_address:
        try:
            prev_val = int(prev_balance)
            curr_val = int(curr_balance)
        except (TypeError, ValueError):
            prev_val = float(prev_balance) if prev_balance else 0
            curr_val = float(curr_balance) if curr_balance else 0

        if curr_val > prev_val:
            state[key_max] = {
                "wallet_address": top.wallet_address,
                "balance_raw": curr_balance,
                "balance_human": _raw_to_human(curr_balance, symbol),
            }
            _save_state(state_path, state)
            return "buy", top.wallet_address
        if curr_val < prev_val:
            state[key_max] = {
                "wallet_address": top.wallet_address,
                "balance_raw": curr_balance,
                "balance_human": _raw_to_human(curr_balance, symbol),
            }
            _save_state(state_path, state)
            return "sell", top.wallet_address

        return None, top.wallet_address

    # 1위 지갑이 바뀜 → 새 1위로 갱신만 하고 알럿은 하지 않음 (최대 보유자 "보유량 변동"에만 알럿)
    state[key_max] = {
        "wallet_address": top.wallet_address,
        "balance_raw": top.balance_raw,
        "balance_human": _raw_to_human(top.balance_raw, symbol),
    }
    _save_state(state_path, state)
    return None, top.wallet_address
