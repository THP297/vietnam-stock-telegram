"""Fetch Vietnam stock prices: vnstock (thinh-vu/vnstock) → VNDirect WebSocket → VNDirect REST → Yahoo Finance."""
import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Timeouts (seconds)
REQUEST_TIMEOUT = 8
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; StockBot/1.0)", "Accept": "application/json"}

# VNDirect realtime WebSocket (from https://github.com/hoangnt2601/Real-time-data-vndirect)
VNDIRECT_WS_URL = "wss://price-cmc-04.vndirect.com.vn/realtime/websocket"
WS_WAIT_SEC = 5
# Message types: BA=BidAsk (matchPrice), SP=StockPartial (currentPrice), MI=MarketInformation (indexValue)
BA, SP, MI = "BA", "SP", "MI"
# MI market IDs: 10=VNINDEX, 11=VN30, 12=HNX30, 13=VNXALL, 02=HNX, 03=UPCOM
MI_IDS = {"10": "VNINDEX", "11": "VN30", "12": "HNX30", "13": "VNXALL", "02": "HNX", "03": "UPCOM"}

# vnstock from https://github.com/thinh-vu/vnstock (Trading.price_board, optional register_user)
VNSTOCK_AVAILABLE = False
try:
    from vnstock import Trading
    VNSTOCK_AVAILABLE = True
except Exception:
    pass


def _vnstock_register_if_configured() -> None:
    """Optional: register vnstock user for higher rate limits (see vnstocks.com/login)."""
    try:
        api_key = __import__("os").environ.get("VNSTOCK_API_KEY", "").strip()
        if api_key:
            from vnstock import register_user
            register_user(api_key=api_key)
    except Exception:
        pass

# Yahoo Finance
YFINANCE_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except Exception:
    pass


def _vndirect_realtime_prices(symbols: list[str]) -> Optional[str]:
    """Real-time prices via VNDirect WebSocket (see hoangnt2601/Real-time-data-vndirect)."""
    symbol_set = {s.strip().upper() for s in symbols}
    index_set = {"VNINDEX", "VN30", "HNXINDEX", "HNX30", "HNX", "UPCOM", "VNXALL"}
    stock_symbols = [s for s in symbol_set if s not in index_set][:20]
    index_wanted = [k for k, v in MI_IDS.items() if v in symbol_set]
    try:
        return asyncio.run(_vndirect_ws_fetch(stock_symbols, index_wanted))
    except Exception as e:
        logger.info("VNDirect WebSocket failed: %s", e)
        return None


async def _vndirect_ws_fetch(stock_symbols: list[str], index_ids: list[str]) -> Optional[str]:
    import websockets
    prices = {}  # symbol -> price (stocks)
    indices = {}  # name -> value (VNINDEX, VN30, ...)
    try:
        async with websockets.connect(VNDIRECT_WS_URL, ssl=True, close_timeout=2) as ws:
            if stock_symbols:
                await ws.send(json.dumps({
                    "type": "registConsumer",
                    "data": {"sequence": 0, "params": {"name": BA, "codes": stock_symbols}},
                }))
            if index_ids:
                await ws.send(json.dumps({
                    "type": "registConsumer",
                    "data": {"sequence": 0, "params": {"name": MI, "codes": index_ids}},
                }))
            deadline = time.monotonic() + WS_WAIT_SEC
            while time.monotonic() < deadline:
                try:
                    left = max(0.5, deadline - time.monotonic())
                    msg = await asyncio.wait_for(ws.recv(), timeout=min(2, left))
                except asyncio.TimeoutError:
                    break
                obj = json.loads(msg)
                typ = obj.get("type")
                data = obj.get("data") or ""
                arr = data.split("|") if isinstance(data, str) else []
                if typ == BA and len(arr) >= 16:
                    code = arr[1]
                    try:
                        prices[code] = float(arr[15])
                    except (ValueError, IndexError):
                        pass
                elif typ == MI and len(arr) >= 8:
                    mid = arr[0]
                    name = MI_IDS.get(mid)
                    try:
                        if name:
                            indices[name] = float(arr[7])
                    except (ValueError, IndexError):
                        pass
            if not prices and not indices:
                return None
            lines = [f"📊 {k}: {v:,.2f}" for k, v in sorted(indices.items())]
            lines += [f"📈 {k}: {v:,.0f}" for k, v in sorted(prices.items())]
            return "\n".join(lines) if lines else None
    except Exception as e:
        logger.debug("VNDirect WS: %s", e)
        return None


def _fetch_one_vndirect(sym: str) -> Optional[tuple[str, float, str]]:
    """Fetch one symbol from VNDirect. Returns (symbol, close, date) or None."""
    base = "https://finfo-api.vndirect.com.vn/v4/stock_prices"
    today = datetime.now().strftime("%Y-%m-%d")
    from_d = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    q = f"code:{sym}~date:gte:{from_d}~date:lte:{today}"
    try:
        r = requests.get(
            base,
            params={"q": q, "size": 1, "sort": "date", "page": 1},
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json().get("data") or []
        if not data:
            return None
        d = data[0]
        close = d.get("close")
        date = (d.get("date") or "")[:10]
        if close is not None:
            return (sym, float(close), date)
    except Exception as e:
        logger.debug("VNDirect %s: %s", sym, e)
    return None


def _vndirect_prices(symbols: list[str]) -> Optional[str]:
    """Fetch latest close from VNDirect in parallel."""
    index_set = {"VNINDEX", "VN30", "HNXINDEX", "HNX30"}
    stock_symbols = [s.strip().upper() for s in symbols if s.strip().upper() not in index_set][:20]
    if not stock_symbols:
        return None
    lines = []
    max_workers = min(10, len(stock_symbols))
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_fetch_one_vndirect, sym): sym for sym in stock_symbols}
            for future in as_completed(futures, timeout=REQUEST_TIMEOUT + 10):
                try:
                    result = future.result()
                    if result:
                        sym, close, date = result
                        lines.append(f"📈 {sym}: {close:,.0f} ({date})")
                except Exception:
                    pass
    except Exception as e:
        logger.info("VNDirect fetch failed: %s", e)
    if not lines:
        logger.info("VNDirect returned no data (timeout or blocked)")
        return None
    lines.sort(key=lambda x: x.split(":")[0])
    return "\n".join(lines)


def _vnstock_price_board(trading_source: str, stock_symbols: list[str]) -> Optional[list[str]]:
    """Get price board lines from vnstock Trading(source).price_board(). Returns list of 'SYM: price' lines or None."""
    if not VNSTOCK_AVAILABLE or not stock_symbols:
        return None
    lines = []
    try:
        trading = Trading(source=trading_source)
        df = trading.price_board(stock_symbols)
        if df is not None and not df.empty:
            for _, r in df.iterrows():
                ticker = r.get("ticker") or r.get("organCode") or r.get("symbol", "")
                price = r.get("price") or r.get("matchPrice") or r.get("p")
                if price is not None and str(ticker).strip():
                    try:
                        p = float(price)
                        lines.append(f"📈 {ticker}: {p:,.0f}")
                    except (TypeError, ValueError):
                        lines.append(f"📈 {ticker}: {price}")
    except Exception as e:
        logger.debug("vnstock %s: %s", trading_source, e)
    return lines if lines else None


def _vnstock_prices(symbols: list[str], index_codes: tuple) -> Optional[str]:
    """Fetch current prices using vnstock (thinh-vu/vnstock). Try KBS then VCI source."""
    if not VNSTOCK_AVAILABLE:
        return None
    _vnstock_register_if_configured()
    index_set = {"VNINDEX", "VN30", "HNXINDEX", "HNX30"}
    stock_symbols = [s for s in symbols if s.upper() not in index_set][:20]
    if not stock_symbols:
        return None
    # Try KBS first (TCBS), then VCI per vnstock docs
    for source in ("KBS", "VCI"):
        lines = _vnstock_price_board(source, stock_symbols)
        if lines:
            logger.info("vnstock %s OK", source)
            return "\n".join(lines)
    logger.info("vnstock returned no data (KBS and VCI)")
    return None


def _yfinance_prices(symbols: list[str]) -> Optional[str]:
    """Fetch latest close from Yahoo Finance (symbol.VN). Works when VN APIs are blocked."""
    if not YFINANCE_AVAILABLE:
        return None
    index_set = {"VNINDEX", "VN30", "HNXINDEX", "HNX30"}
    stock_symbols = [s.strip().upper() for s in symbols if s.strip().upper() not in index_set][:15]
    if not stock_symbols:
        return None
    lines = []
    for sym in stock_symbols:
        try:
            ticker = yf.Ticker(f"{sym}.VN")
            hist = ticker.history(period="5d", auto_adjust=True)
            if hist is not None and not hist.empty and "Close" in hist.columns:
                last = hist.iloc[-1]
                close = float(last["Close"])
                date = hist.index[-1].strftime("%Y-%m-%d") if hasattr(hist.index[-1], "strftime") else ""
                lines.append(f"📈 {sym}: {close:,.0f} ({date})")
        except Exception as e:
            logger.debug("yfinance %s: %s", sym, e)
    if not lines:
        logger.info("Yahoo Finance returned no data")
        return None
    lines.sort(key=lambda x: x.split(":")[0])
    return "\n".join(lines)


def fetch_prices(symbols: list[str], index_codes: tuple) -> str:
    """Get Vietnam stock prices. Prefer vnstock (GitHub) → VNDirect WS → VNDirect REST → Yahoo."""
    # 1) vnstock from https://github.com/thinh-vu/vnstock (KBS then VCI)
    if VNSTOCK_AVAILABLE:
        logger.info("Trying vnstock (thinh-vu/vnstock)...")
        text = _vnstock_prices(symbols, index_codes)
        if text:
            return text
    # 2) VNDirect real-time WebSocket
    try:
        logger.info("Trying VNDirect WebSocket (realtime)...")
        text = _vndirect_realtime_prices(symbols)
        if text:
            logger.info("VNDirect WebSocket OK")
            return text
    except Exception as e:
        logger.debug("VNDirect WS: %s", e)
    # 3) VNDirect REST
    logger.info("Trying VNDirect REST...")
    text = _vndirect_prices(symbols)
    if text:
        logger.info("VNDirect REST OK")
        return text
    # 4) Yahoo Finance
    if YFINANCE_AVAILABLE:
        logger.info("Trying Yahoo Finance (.VN)...")
        text = _yfinance_prices(symbols)
        if text:
            logger.info("Yahoo Finance OK")
            return text
    return "⚠️ Could not fetch prices. Check network and symbols (e.g. VCB, TCB, FPT)."


def parse_prices_text(text: str) -> dict[str, float]:
    """Parse fetcher output (e.g. '📈 VCB: 95,500') into {symbol: price}. Handles 📈 and 📊 lines."""
    result = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line or ("📈" not in line and "📊" not in line):
            continue
        rest = line.replace("📈", "").replace("📊", "").strip()
        if ":" not in rest:
            continue
        symbol, value = rest.split(":", 1)
        symbol = symbol.strip()
        # value may be "95,500" or "95,500 (2026-02-16)" or "1,250.52"
        value = value.strip().split("(")[0].strip().replace(",", "")
        try:
            result[symbol] = float(value)
        except ValueError:
            pass
    return result


def fetch_prices_dict(symbols: list[str], index_codes: tuple) -> dict[str, float]:
    """Return current prices as {symbol: price}. Empty dict if fetch failed."""
    text = fetch_prices(symbols, index_codes)
    if not text or text.startswith("⚠️"):
        return {}
    return parse_prices_text(text)
