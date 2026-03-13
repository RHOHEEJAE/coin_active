# -*- coding: utf-8 -*-
"""Moralis API로 ERC-20 토큰 상위 보유자 조회 (SHIB 등). 무료 tier에서 사용 가능."""

import logging
from typing import List

import requests

from config import MORALIS_API_KEY
from .base import HolderInfo

logger = logging.getLogger(__name__)

MORALIS_BASE = "https://deep-index.moralis.io/api/v2.2/erc20"


def fetch_moralis_top_holders(
    contract_address: str,
    limit: int = 100,
    symbol: str = "",
    chain: str = "eth",
) -> List[HolderInfo]:
    """
    Moralis token owners API로 상위 보유자 조회.
    무료 tier에서 사용 가능 (요청당 50 CU).
    """
    if not MORALIS_API_KEY:
        logger.info("%s: Moralis 조회를 위해 MORALIS_API_KEY 설정 필요 (https://moralis.io)", symbol or "ERC20")
        return []

    url = f"{MORALIS_BASE}/{contract_address}/owners"
    params = {"chain": chain, "order": "DESC", "limit": min(limit, 100)}
    headers = {"X-API-Key": MORALIS_API_KEY}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Moralis token holders request failed for %s: %s", symbol or contract_address, e)
        return []

    result_data = data.get("result")
    if not isinstance(result_data, list):
        logger.warning("Moralis invalid result for %s: %s", symbol or contract_address, data)
        return []

    result = []
    for i, row in enumerate(result_data[:limit], start=1):
        if not isinstance(row, dict):
            continue
        addr = row.get("owner_address")
        value = row.get("balance")
        if not addr:
            continue
        result.append(
            HolderInfo(
                wallet_address=str(addr),
                balance_raw=str(value) if value is not None else "0",
                rank=i,
            )
        )
    return result
