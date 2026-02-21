import logging
import threading
import time

from .config import (
    CHECK_INTERVAL_SEC,
    INDEX_CODES,
    PRICE_BAND_PCT,
    SAMPLE_PRICES,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from .fetcher import fetch_prices_dict
from .store import (
    append_observer_price_change,
    load_last_alerted,
    load_observers,
    save_last_alerted,
)
from .telegram_send import send_telegram

logger = logging.getLogger(__name__)

_last_seen_prices: dict[str, float] = {}


def run_check() -> None:
    global _last_seen_prices
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    observers = load_observers()
    if not observers:
        return
    index_set = set(INDEX_CODES)
    stock_symbols = [s for s in observers if s not in index_set]
    prices = fetch_prices_dict(stock_symbols, INDEX_CODES)
    if not prices:
        return
    last_alerted = load_last_alerted()
    if SAMPLE_PRICES:
        for sym, p in prices.items():
            if _last_seen_prices.get(sym) != p:
                last_alerted.pop(sym, None)
                _last_seen_prices[sym] = p
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
        low = target * (1 - PRICE_BAND_PCT)
        high = target * (1 + PRICE_BAND_PCT)
        inside_band = low < current < high
        if not inside_band:
            if last_alerted.get(symbol) == target:
                last_alerted.pop(symbol, None)
                updated = True
            continue
        if last_alerted.get(symbol) == target:
            continue
        msg = f"🔔 Price alert: {symbol} = {current:,.0f} (within 0.1% of target {target:,.0f})"
        append_observer_price_change(symbol, target, current)
        if send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg):
            last_alerted[symbol] = target
            updated = True
            logger.info("Alert sent: %s", msg)
    if updated:
        save_last_alerted(last_alerted)


def start_background_checker() -> None:
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
