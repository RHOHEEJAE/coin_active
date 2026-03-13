# -*- coding: utf-8 -*-
"""?? ? API ??."""

import os
from dotenv import load_dotenv

load_dotenv()

# API ? (??)
BLOCKCHAIR_API_KEY = os.getenv("BLOCKCHAIR_API_KEY", "")
BLOCKSCOUT_API_KEY = os.getenv("BLOCKSCOUT_API_KEY", "")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY", "")

# ??
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# DB: Supabase ?? ?? PostgreSQL
# Supabase ?? ?: Dashboard > Project Settings > Database > Connection string (URI) ?? ? [YOUR-PASSWORD] ??
SUPABASE_DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mydb")
DATABASE_URL = (
    SUPABASE_DATABASE_URL
    if SUPABASE_DATABASE_URL
    else f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# ??? ?? (PEPE, WETH ? Blockscout ERC-20)
COINS = {
    "PEPE": {
        "name": "??",
        "fetcher": "blockscout_erc20",
        "contract_address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
        "blockscout_base_url": "https://eth.blockscout.com/api",
        "decimals": 18,
        "top_holders_count": 100,
    },
    "WETH": {
        "name": "Wrapped Ether",
        "fetcher": "blockscout_erc20",
        "contract_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "blockscout_base_url": "https://eth.blockscout.com/api",
        "decimals": 18,
        "top_holders_count": 100,
    },
}

# ?? N? ???
TOP_HOLDERS_COUNT = 5

# ?? ?? (?) ? 5??? ??
CHECK_INTERVAL_SECONDS = 300
