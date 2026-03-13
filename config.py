# -*- coding: utf-8 -*-
"""코인 및 API 설정."""

import os
from dotenv import load_dotenv

load_dotenv()

# API 키 (선택)
BLOCKCHAIR_API_KEY = os.getenv("BLOCKCHAIR_API_KEY", "")
BLOCKSCOUT_API_KEY = os.getenv("BLOCKSCOUT_API_KEY", "")

# 알림
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# DB: Supabase 또는 로컬 PostgreSQL
# Supabase 사용 시: Dashboard > Project Settings > Database > Connection string (URI) 복사 후 [YOUR-PASSWORD] 치환
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

# 코인별 설정 (PEPE만 사용)
COINS = {
    "PEPE": {
        "name": "페페",
        "fetcher": "blockscout_erc20",
        "contract_address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933",
        "blockscout_base_url": "https://eth.blockscout.com/api",
        "decimals": 18,
        "top_holders_count": 100,
    },
}

# 상위 N명 보유자
TOP_HOLDERS_COUNT = 5

# 체크 주기 (초)
CHECK_INTERVAL_SECONDS = 300
