# -*- coding: utf-8 -*-
"""보유자 조회 공통 인터페이스."""

from dataclasses import dataclass
from typing import List

from config import COINS, TOP_HOLDERS_COUNT


@dataclass
class HolderInfo:
    """지갑 보유 정보."""
    wallet_address: str  # PK
    balance_raw: str    # 원시 수량 (문자열로 정밀도 유지)
    rank: int           # 1=최대 보유자


def fetch_top_holders(symbol: str) -> List[HolderInfo]:
    """
    코인 심볼에 맞는 API로 상위 N명 보유자 조회.
    """
    if symbol not in COINS:
        return []

    coin_config = COINS[symbol]
    fetcher = coin_config.get("fetcher")
    top_n = coin_config.get("top_holders_count", TOP_HOLDERS_COUNT)

    if fetcher == "blockchair_native":
        from .blockchair import fetch_blockchair_top_holders
        return fetch_blockchair_top_holders(
            chain=coin_config["blockchair_chain"],
            limit=top_n,
            symbol=symbol,
        )
    if fetcher == "blockscout_erc20":
        from .blockscout import fetch_blockscout_top_holders
        return fetch_blockscout_top_holders(
            contract_address=coin_config["contract_address"],
            base_url=coin_config.get("blockscout_base_url", "https://eth.blockscout.com/api"),
            limit=top_n,
            symbol=symbol,
        )
    if fetcher == "etherscan_erc20":
        from .etherscan import fetch_etherscan_top_holders
        return fetch_etherscan_top_holders(
            contract_address=coin_config["contract_address"],
            limit=top_n,
            symbol=symbol,
            chain_id=coin_config.get("chain_id", 1),
        )
    if fetcher == "moralis_erc20":
        from .moralis import fetch_moralis_top_holders
        return fetch_moralis_top_holders(
            contract_address=coin_config["contract_address"],
            limit=top_n,
            symbol=symbol,
            chain=coin_config.get("moralis_chain", "eth"),
        )
    if fetcher == "xrpscan_native":
        from .xrpscan import fetch_xrpscan_top_holders
        return fetch_xrpscan_top_holders(limit=top_n, symbol=symbol)

    return []
