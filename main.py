# -*- coding: utf-8 -*-
"""
PEPE 상위 100명 보유자 조회 및 전원 보유량 변동 추적(매수/매도 알럿).
"""

import logging
import sys
import time

import schedule

from config import COINS, CHECK_INTERVAL_SECONDS
from fetchers.base import fetch_top_holders
from storage import save_top_holders, _raw_to_human
from db import init_db, upsert_top_holders, check_and_record_alerts_for_all
from alert import send_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def run_check():
    """PEPE 상위 100명 조회 → state + DB 저장, 전원 보유량 변동 시 매수/매도 알럿 기록 및 발송."""
    for symbol in COINS:
        try:
            holders = fetch_top_holders(symbol)
            if not holders:
                logger.debug("%s: no holders fetched", symbol)
                continue
            save_top_holders(symbol, holders)
            upsert_top_holders(symbol, holders, lambda raw: _raw_to_human(raw, symbol))
            logger.info("%s 상위 %d명 보유자 저장 완료 (state + DB)", symbol, len(holders))
            alerts = check_and_record_alerts_for_all(symbol, holders)
            coin_name = COINS.get(symbol, {}).get("name", symbol)
            for alert_type, wallet, rank, _before, _after in alerts:
                msg = f"{coin_name} 상위 {rank}위 지갑 보유량 변동"
                send_alert(symbol, alert_type, wallet, msg)
            if alerts:
                logger.info("%s 매수/매도 알럿 %d건 발송", symbol, len(alerts))
        except Exception as e:
            logger.exception("Error checking %s: %s", symbol, e)


def main():
    logger.info("PEPE 상위 100명 보유자 변동 감지 시작")
    init_db()
    # 즉시 1회 실행
    run_check()
    # 주기적 실행
    schedule.every(CHECK_INTERVAL_SECONDS).seconds.do(run_check)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
