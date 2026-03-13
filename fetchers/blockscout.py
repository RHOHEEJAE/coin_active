# -*- coding: utf-8 -*-
"""Blockscout API로 ERC-20 토큰 상위 보유자 조회 (PEPE 등)."""

import logging
from typing import List

import requests

from config import BLOCKSCOUT_API_KEY
from .base import HolderInfo

logger = logging.getLogger(__name__)


def fetch_blockscout_top_holders(
    contract_address: str,
    base_url: str = "https://eth.blockscout.com/api",
    limit: int = 5,
    symbol: str = "",
) -> List[HolderInfo]:
    """
    Blockscout getTokenHolders 로 상위 보유자 조회.
    module=token&action=getTokenHolders&contractaddress=0x...&offset=5
    (일반적으로 1페이지가 보유량 순이면 상위 5명)
    """
    url = base_url.rstrip("/") + "/"
    params = {
        "module": "token",
        "action": "getTokenHolders",
        "contractaddress": contract_address,
        "page": 1,
        "offset": limit,
    }
    if BLOCKSCOUT_API_KEY:
        params["apikey"] = BLOCKSCOUT_API_KEY

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.warning("Blockscout token holders request failed for %s: %s", symbol or contract_address, e)
        return []

    result_data = data.get("result")
    if not isinstance(result_data, list):
        logger.warning("Blockscout invalid result for %s: %s", symbol or contract_address, data.get("message", "unknown"))
        return []

    rows = result_data or []
    if not rows and symbol:
        logger.info("%s: Blockscout에서 보유자 0명 반환 (해당 토큰 미지원일 수 있음 → SHIB는 Etherscan 사용)", symbol)
    # 보유량(value) 내림차순 정렬 후 상위 limit명
    try:
        rows = sorted(rows, key=lambda x: int(x.get("value") or 0), reverse=True)[:limit]
    except (TypeError, ValueError):
        pass
    result = []
    for i, row in enumerate(rows, start=1):
        addr = row.get("address")
        value = row.get("value")
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
