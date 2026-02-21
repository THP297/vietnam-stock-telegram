"""Run every 30 seconds: compare prices to observers, send Telegram on match, update history."""
import logging
import threading
import time

from config import INDEX_CODES, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from fetcher import fetch_prices_dict
from store import (
    USE_DB,
    append_history,
    load_last_alerted,
    load_observers,
    save_last_alerted,
)
from telegram_send import send_telegram

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SEC = 30  # 30 seconds


def run_check() -> None:
    """Fetch prices, compare to observers, send alerts and update history."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    observers = load_observers()
    if not observers:
        return
    # When using DB, fetch prices only for observer symbols (+ indices). Else use config SYMBOLS.
    index_set = set(INDEX_CODES)
    if USE_DB:
        stock_symbols = [s for s in observers if s not in index_set]
        symbols_to_fetch = stock_symbols if stock_symbols else list(SYMBOLS)
    else:
        symbols_to_fetch = list(SYMBOLS)
    prices = fetch_prices_dict(symbols_to_fetch, INDEX_CODES)
    if not prices:
        return
    last_alerted = load_last_alerted()
    updated = False
    for symbol, target_str in list(observers.items()):
        symbol = symbol.strip().upper()
        if not target_str or symbol not in prices:
            continue
        try:
            target = float(str(target_str).replace(",", "").strip())
        except ValueError:
            continue
        current = prices.get(symbol)
        if current is None:
            continue
        # Alert when current price <= target (price reached or dropped to target)
        if current > target:
            if last_alerted.get(symbol) == target:
                last_alerted.pop(symbol, None)
                updated = True
            continue
        if last_alerted.get(symbol) == target:
            continue
        msg = f"🔔 Price alert: {symbol} = {current:,.0f} (target ≤ {target:,.0f})"
        if send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg):
            append_history(symbol, target, current)
            last_alerted[symbol] = target
            updated = True
            logger.info("Alert sent: %s", msg)
    if updated:
        save_last_alerted(last_alerted)


def start_background_checker() -> None:
    """Start a daemon thread that runs run_check every CHECK_INTERVAL_SEC seconds."""
    def loop():
        while True:
            try:
                run_check()
            except Exception as e:
                logger.exception("Checker error: %s", e)
            time.sleep(CHECK_INTERVAL_SEC)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    if CHECK_INTERVAL_SEC >= 60:
        logger.info("Background checker started (every %s min)", CHECK_INTERVAL_SEC // 60)
    else:
        logger.info("Background checker started (every %s sec)", CHECK_INTERVAL_SEC)
