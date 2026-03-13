# -*- coding: utf-8 -*-
"""Blockchair API로 네이티브 코인 상위 보유자 조회 (DOGE, BTC, XRP 등)."""

import logging
from typing import List

import requests

from config import BLOCKCHAIR_API_KEY
from .base import HolderInfo

logger = logging.getLogger(__name__)

# Bitcoin-like: bitcoin, dogecoin 등. Ripple은 응답 구조가 다를 수 있음.
BLOCKCHAIR_CHAINS_WITH_ADDRESSES = ("bitcoin", "dogecoin", "litecoin", "dash", "bitcoin-cash", "bitcoin-sv", "groestlcoin", "zcash")


def fetch_blockchair_top_holders(
    chain: str,
    limit: int = 5,
    symbol: str = "",
) -> List[HolderInfo]:
    """
    Blockchair addresses API로 상위 보유자 조회.
    https://api.blockchair.com/{chain}/addresses?limit=5
    기본 정렬이 balance 내림차순인 경우 사용.
    """
    url = f"https://api.blockchair.com/{chain}/addresses"
    params = {"limit": limit}
    if BLOCKCHAIR_API_KEY:
        params["key"] = BLOCKCHAIR_API_KEY

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 430:
            logger.warning(
                "Blockchair %s: 430 (API 제한). .env에 BLOCKCHAIR_API_KEY를 넣으면 DOGE/BTC/XRP 조회 가능.",
                symbol or chain,
            )
        else:
            logger.warning("Blockchair %s top holders request failed: %s", symbol or chain, e)
        return []
    except Exception as e:
        logger.warning("Blockchair %s top holders request failed: %s", symbol or chain, e)
        return []

    # 응답: { "data": [ { "address", "balance", ... } ], "context": { ... } }
    rows = data.get("data") or []
    result = []
    for i, row in enumerate(rows[:limit], start=1):
        addr = row.get("address") or row.get("id")
        balance = row.get("balance")
        if addr is None:
            continue
        if balance is None:
            balance = 0
        result.append(
            HolderInfo(
                wallet_address=str(addr),
                balance_raw=str(int(balance)),
                rank=i,
            )
        )
    return result
