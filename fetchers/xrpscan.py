# -*- coding: utf-8 -*-
"""XRPSCAN 무료 API로 XRP(Ledger) 상위 보유자 조회. API 키 불필요."""

import logging
from typing import List

import requests

from .base import HolderInfo

logger = logging.getLogger(__name__)

XRPSCAN_BALANCES_URL = "https://api.xrpscan.com/api/v1/balances"


def fetch_xrpscan_top_holders(limit: int = 100, symbol: str = "XRP") -> List[HolderInfo]:
    """
    XRPSCAN Balances API (XRP rich list). 상위 계정이 balance 내림차순으로 반환됨.
    balance 단위: drops (1 XRP = 1_000_000 drops).
    데이터는 매일 갱신됨. API 키 불필요.
    """
    try:
        r = requests.get(XRPSCAN_BALANCES_URL, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("XRPSCAN balances request failed for %s: %s", symbol, e)
        return []

    if not isinstance(data, list):
        logger.warning("XRPSCAN invalid result for %s: expected list", symbol)
        return []

    result = []
    for i, item in enumerate(data[:limit], start=1):
        if not isinstance(item, dict):
            continue
        account = item.get("account")
        balance = item.get("balance")
        if not account:
            continue
        # balance는 drops (정수)
        balance_raw = str(int(balance)) if balance is not None else "0"
        result.append(
            HolderInfo(
                wallet_address=str(account),
                balance_raw=balance_raw,
                rank=i,
            )
        )
    return result
