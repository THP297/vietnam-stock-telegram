#!/usr/bin/env python3
"""
Vietnam stock price → Telegram every 1 minute.

Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env or environment.
Optional: STOCK_SYMBOLS (comma-separated, e.g. VCB,TCB,FPT,VNINDEX,VN30).
"""
import logging
import sys
import time
from datetime import datetime

from config import INDEX_CODES, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from fetcher import fetch_prices
from telegram_send import send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 60


def run_once() -> bool:
    """Fetch prices and send one message to Telegram. Returns True if sent."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return False
    if not SYMBOLS:
        logger.error("Set STOCK_SYMBOLS in .env (e.g. VCB,TCB,FPT,VNINDEX,VN30)")
        return False

    logger.info("Fetching prices...")
    body = fetch_prices(SYMBOLS, INDEX_CODES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"🇻🇳 Vietnam stock @ {now}\n\n{body}"

    if send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message):
        logger.info("Sent to Telegram (%d chars)", len(message))
        return True
    return False


def main() -> None:
    logger.info("Starting Vietnam stock → Telegram (every %s s)", INTERVAL_SECONDS)
    logger.info("Symbols: %s", ", ".join(SYMBOLS[:15]) + ("..." if len(SYMBOLS) > 15 else ""))

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_once()
        return

    while True:
        run_once()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
