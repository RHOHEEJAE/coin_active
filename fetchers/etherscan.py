# -*- coding: utf-8 -*-
"""Etherscan API v2로 ERC-20 토큰 상위 보유자 조회 (SHIB 등). tokenholderlist는 PRO 플랜 필요."""

import logging
from typing import List

import requests

from config import ETHERSCAN_API_KEY
from .base import HolderInfo

logger = logging.getLogger(__name__)

ETHERSCAN_V2_BASE = "https://api.etherscan.io/v2/api"


def fetch_etherscan_top_holders(
    contract_address: str,
    limit: int = 100,
    symbol: str = "",
    chain_id: int = 1,
) -> List[HolderInfo]:
    """
    Etherscan v2 tokenholderlist 로 상위 보유자 조회.
    PRO 플랜에서만 사용 가능. API 키 없으면 빈 리스트 반환.
    """
    if not ETHERSCAN_API_KEY:
        logger.info("%s: Etherscan 조회를 위해 ETHERSCAN_API_KEY 설정 필요 (PRO 플랜 시 토큰 홀더 조회 가능)", symbol or "ERC20")
        return []

    params = {
        "chainid": chain_id,
        "module": "token",
        "action": "tokenholderlist",
        "contractaddress": contract_address,
        "page": 1,
        "offset": limit,
        "apikey": ETHERSCAN_API_KEY,
    }
    try:
        r = requests.get(ETHERSCAN_V2_BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Etherscan token holders request failed for %s: %s", symbol or contract_address, e)
        return []

    if str(data.get("status")) != "1":
        msg = data.get("message", "Unknown error")
        logger.warning("Etherscan API %s: %s (tokenholderlist는 PRO 플랜 필요할 수 있음)", symbol or contract_address, msg)
        return []

    result_data = data.get("result")
    if not isinstance(result_data, list):
        logger.warning("Etherscan invalid result for %s: %s", symbol or contract_address, data.get("message", "unknown"))
        return []

    result = []
    for i, row in enumerate(result_data[:limit], start=1):
        if not isinstance(row, dict):
            continue
        addr = row.get("TokenHolderAddress") or row.get("address")
        value = row.get("TokenHolderQuantity") or row.get("value")
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
