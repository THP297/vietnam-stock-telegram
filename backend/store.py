import json
import logging
import os
from datetime import datetime
from typing import Any

from .config import DATA_DIR, UTC7

logger = logging.getLogger(__name__)

OBSERVERS_FILE = DATA_DIR / "observers.json"
HISTORY_FILE = DATA_DIR / "history.json"
LAST_ALERTED_FILE = DATA_DIR / "last_alerted.json"
MATCH_PRICE_FILE = DATA_DIR / "match_price.json"


def _use_db() -> bool:
    return bool(os.getenv("DATABASE_URL", "").strip())


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_observers() -> dict[str, str]:
    if _use_db():
        from .db import load_observers as _load
        return _load()
    _ensure_dir()
    if not OBSERVERS_FILE.exists():
        return {}
    try:
        with open(OBSERVERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("load_observers: %s", e)
        return {}


def save_observers(observers: dict[str, str]) -> None:
    if _use_db():
        from .db import save_observers as _save
        return _save(observers)
    _ensure_dir()
    with open(OBSERVERS_FILE, "w", encoding="utf-8") as f:
        json.dump(observers, f, indent=2, ensure_ascii=False)


def load_history() -> list[dict[str, Any]]:
    if _use_db():
        from .db import load_history as _load
        return _load()
    _ensure_dir()
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning("load_history: %s", e)
        return []


def append_history(symbol: str, target: float, price: float) -> None:
    if _use_db():
        from .db import append_history as _append
        return _append(symbol, target, price)
    _ensure_dir()
    history = load_history()
    history.insert(0, {
        "symbol": symbol,
        "target": target,
        "price": price,
        "at": datetime.now(UTC7).strftime("%Y-%m-%d %H:%M:%S"),
    })
    history = history[:500]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def load_last_alerted() -> dict[str, float]:
    if _use_db():
        from .db import load_last_alerted as _load
        return _load()
    _ensure_dir()
    if not LAST_ALERTED_FILE.exists():
        return {}
    try:
        with open(LAST_ALERTED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: float(v) for k, v in (data or {}).items()}
    except Exception:
        return {}


def save_last_alerted(last: dict[str, float]) -> None:
    if _use_db():
        from .db import save_last_alerted as _save
        return _save(last)
    _ensure_dir()
    with open(LAST_ALERTED_FILE, "w", encoding="utf-8") as f:
        json.dump(last, f, indent=2)


def get_history_filtered(symbol: str | None) -> list[dict[str, Any]]:
    if _use_db():
        from .db import get_history_filtered as _get
        return _get(symbol)
    history = load_history()
    if symbol:
        symbol = symbol.strip().upper()
        history = [h for h in history if (h.get("symbol") or "").upper() == symbol]
    return history


def append_match_price(symbol: str, target: float, price: float) -> None:
    if _use_db():
        from .db import insert_match_price as _insert
        return _insert(symbol, target, price)
    _ensure_dir()
    data = load_match_price_raw()
    data.insert(0, {
        "symbol": symbol,
        "target": target,
        "price": price,
        "at": datetime.now(UTC7).strftime("%Y-%m-%d %H:%M:%S"),
    })
    data = data[:500]
    with open(MATCH_PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_match_price_raw() -> list[dict[str, Any]]:
    _ensure_dir()
    if not MATCH_PRICE_FILE.exists():
        return []
    try:
        with open(MATCH_PRICE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning("load_match_price_raw: %s", e)
        return []


def get_match_price_filtered(symbol: str | None) -> list[dict[str, Any]]:
    if _use_db():
        from .db import get_match_price_filtered as _get
        return _get(symbol)
    data = load_match_price_raw()
    if symbol:
        symbol = symbol.strip().upper()
        data = [h for h in data if (h.get("symbol") or "").upper() == symbol]
    return data
