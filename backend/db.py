import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from .config import UTC7

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def _conn():
    import psycopg2
    url = DATABASE_URL
    if not url:
        raise ValueError("DATABASE_URL is not set")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if "sslmode" not in url and "postgresql" in url:
        url = url + ("&" if "?" in url else "?") + "sslmode=require"
    return psycopg2.connect(url)


@contextmanager
def _cursor():
    conn = _conn()
    try:
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()


def init_schema() -> None:
    with _cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS observers (
                symbol VARCHAR(20) PRIMARY KEY,
                target_price TEXT NOT NULL DEFAULT ''
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                target NUMERIC NOT NULL,
                price NUMERIC NOT NULL,
                at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS last_alerted (
                symbol VARCHAR(20) PRIMARY KEY,
                target NUMERIC NOT NULL
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_symbol ON history(symbol);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_at ON history(at DESC);")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS observer_price_change (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                target NUMERIC NOT NULL,
                price NUMERIC NOT NULL,
                at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_observer_price_change_symbol ON observer_price_change(symbol);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_observer_price_change_at ON observer_price_change(at DESC);")


def load_observers() -> dict[str, str]:
    obs = {}
    try:
        init_schema()
        with _cursor() as cur:
            cur.execute("SELECT symbol, target_price FROM observers")
            for row in cur.fetchall():
                obs[row[0]] = row[1] or ""
    except Exception as e:
        logger.warning("db load_observers: %s", e)
    return obs


def save_observers(observers: dict[str, str]) -> None:
    try:
        init_schema()
        with _cursor() as cur:
            cur.execute("DELETE FROM observers")
            for sym, target in observers.items():
                if sym:
                    cur.execute(
                        "INSERT INTO observers (symbol, target_price) VALUES (%s, %s) ON CONFLICT (symbol) DO UPDATE SET target_price = EXCLUDED.target_price",
                        (sym.strip().upper(), str(target).strip()),
                    )
    except Exception as e:
        logger.warning("db save_observers: %s", e)


def load_history() -> list[dict[str, Any]]:
    out = []
    try:
        with _cursor() as cur:
            cur.execute("SELECT symbol, target, price, at FROM history ORDER BY at DESC LIMIT 500")
            for row in cur.fetchall():
                out.append({
                    "symbol": row[0],
                    "target": float(row[1]) if row[1] is not None else 0,
                    "price": float(row[2]) if row[2] is not None else 0,
                    "at": row[3].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row[3], "strftime") else str(row[3]),
                })
    except Exception as e:
        logger.warning("db load_history: %s", e)
    return out


def append_history(symbol: str, target: float, price: float) -> None:
    try:
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO history (symbol, target, price, at) VALUES (%s, %s, %s, %s)",
                (symbol, target, price, datetime.now(UTC7).replace(tzinfo=None)),
            )
    except Exception as e:
        logger.warning("db append_history: %s", e)


def load_last_alerted() -> dict[str, float]:
    out = {}
    try:
        with _cursor() as cur:
            cur.execute("SELECT symbol, target FROM last_alerted")
            for row in cur.fetchall():
                out[row[0]] = float(row[1])
    except Exception as e:
        logger.warning("db load_last_alerted: %s", e)
    return out


def save_last_alerted(last: dict[str, float]) -> None:
    try:
        with _cursor() as cur:
            cur.execute("DELETE FROM last_alerted")
            for sym, target in last.items():
                cur.execute(
                    "INSERT INTO last_alerted (symbol, target) VALUES (%s, %s) ON CONFLICT (symbol) DO UPDATE SET target = EXCLUDED.target",
                    (sym, target),
                )
    except Exception as e:
        logger.warning("db save_last_alerted: %s", e)


def get_history_filtered(symbol: str | None) -> list[dict[str, Any]]:
    if not symbol:
        return load_history()
    out = []
    try:
        with _cursor() as cur:
            cur.execute(
                "SELECT symbol, target, price, at FROM history WHERE UPPER(symbol) = UPPER(%s) ORDER BY at DESC LIMIT 500",
                (symbol.strip(),),
            )
            for row in cur.fetchall():
                out.append({
                    "symbol": row[0],
                    "target": float(row[1]) if row[1] is not None else 0,
                    "price": float(row[2]) if row[2] is not None else 0,
                    "at": row[3].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row[3], "strftime") else str(row[3]),
                })
    except Exception as e:
        logger.warning("db get_history_filtered: %s", e)
    return out


def insert_observer_price_change(symbol: str, target: float, price: float) -> None:
    try:
        with _cursor() as cur:
            cur.execute(
                "INSERT INTO observer_price_change (symbol, target, price, at) VALUES (%s, %s, %s, %s)",
                (symbol, target, price, datetime.now(UTC7).replace(tzinfo=None)),
            )
    except Exception as e:
        logger.warning("db insert_observer_price_change: %s", e)


def get_observer_price_change_filtered(symbol: str | None) -> list[dict[str, Any]]:
    out = []
    try:
        with _cursor() as cur:
            if symbol:
                cur.execute(
                    "SELECT symbol, target, price, at FROM observer_price_change WHERE UPPER(symbol) = UPPER(%s) ORDER BY at DESC LIMIT 500",
                    (symbol.strip(),),
                )
            else:
                cur.execute("SELECT symbol, target, price, at FROM observer_price_change ORDER BY at DESC LIMIT 500")
            for row in cur.fetchall():
                out.append({
                    "symbol": row[0],
                    "target": float(row[1]) if row[1] is not None else 0,
                    "price": float(row[2]) if row[2] is not None else 0,
                    "at": row[3].strftime("%Y-%m-%d %H:%M:%S") if hasattr(row[3], "strftime") else str(row[3]),
                })
    except Exception as e:
        logger.warning("db get_observer_price_change_filtered: %s", e)
    return out
