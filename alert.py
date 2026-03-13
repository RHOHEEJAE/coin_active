# -*- coding: utf-8 -*-
"""알럿 발송: 콘솔 및 선택적 텔레그램."""

import logging
from typing import Optional

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, COINS

logger = logging.getLogger(__name__)


def send_console_alert(
    symbol: str,
    alert_type: str,
    wallet_address: str,
    message: str,
) -> None:
    """콘솔 로그로 알림."""
    coin_name = COINS.get(symbol, {}).get("name", symbol)
    label = "매수" if alert_type == "buy" else "매도"
    logger.info("[알럿] %s (%s) 최대 보유자 %s | 지갑: %s | %s", coin_name, symbol, label, wallet_address, message)


def send_telegram_alert(
    symbol: str,
    alert_type: str,
    wallet_address: str,
    message: str,
) -> bool:
    """텔레그램 봇으로 알림. 성공 여부 반환."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    coin_name = COINS.get(symbol, {}).get("name", symbol)
    label = "매수" if alert_type == "buy" else "매도"
    text = f"🔔 [{coin_name}] 최대 보유자 {label}\n지갑: {wallet_address}\n{message}"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        if r.ok:
            return True
        logger.warning("Telegram send failed: %s %s", r.status_code, r.text)
    except Exception as e:
        logger.warning("Telegram request failed: %s", e)
    return False


def send_alert(
    symbol: str,
    alert_type: str,
    wallet_address: str,
    message: str = "",
) -> None:
    """콘솔 + (설정 시) 텔레그램 알림."""
    send_console_alert(symbol, alert_type, wallet_address, message)
    send_telegram_alert(symbol, alert_type, wallet_address, message)
