import logging
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ is None:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    import runpy
    runpy.run_module("backend.app", run_name="__main__")
    sys.exit()

from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request

from .config import (
    FLASK_HOST,
    FLASK_PORT,
    INDEX_CODES,
    SYMBOLS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from .fetcher import fetch_prices, fetch_prices_dict
from .store import (
    append_history,
    get_history_filtered,
    get_match_price_filtered,
    load_observers,
    save_observers,
)
from .telegram_send import send_telegram

run_check = None
try:
    from .alert_checker import run_check as _run_check, start_background_checker
    run_check = _run_check
    start_background_checker()
except Exception as e:
    logging.warning("Background checker not started: %s", e)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


def get_symbol_list() -> list[str]:
    observers = load_observers()
    return sorted(observers.keys())


@app.route("/")
def index():
    return jsonify({
        "ok": True,
        "app": "vietnam-stock-telegram",
        "endpoints": [
            "/api/symbols",
            "/api/observers",
            "/api/history",
            "/api/match-price",
            "/api/price",
            "/api/check",
        ],
    })


@app.route("/api/symbols")
def api_symbols():
    return jsonify({"symbols": get_symbol_list()})


@app.route("/api/observers", methods=["GET"])
def api_get_observers():
    return jsonify(load_observers())


@app.route("/api/observers", methods=["POST"])
def api_save_observers():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}
    observers = {}
    for k, v in data.items():
        if k and isinstance(k, str) and v is not None:
            observers[k.strip().upper()] = str(v).strip()
    old = load_observers()
    save_observers(observers)
    for symbol, target_str in observers.items():
        if not target_str or old.get(symbol) == target_str:
            continue
        try:
            target = float(str(target_str).replace(",", "").strip())
        except ValueError:
            continue
        prices = fetch_prices_dict([symbol], INDEX_CODES)
        price = prices.get(symbol)
        if price is None:
            price = target
        append_history(symbol, target, price)
        logging.info("History row added for %s (target changed to %s, price %s)", symbol, target, price)
    return jsonify({"ok": True, "observers": observers})


@app.route("/api/history")
def api_history():
    symbol = request.args.get("symbol", "").strip() or None
    history = get_history_filtered(symbol)
    return jsonify({"history": history})


@app.route("/api/match-price")
def api_match_price():
    symbol = request.args.get("symbol", "").strip() or None
    rows = get_match_price_filtered(symbol)
    return jsonify({"match_price": rows})


@app.route("/api/price")
def api_price():
    symbol = (request.args.get("symbol") or "").strip().upper()
    if not symbol:
        return jsonify({"error": "Missing symbol"}), 400
    try:
        prices = fetch_prices_dict([symbol], INDEX_CODES)
        if symbol not in prices:
            return jsonify({
                "error": f"Could not get price for {symbol}. All sources failed (vnstock, VNDirect, Yahoo). Try again later or check network/VPN."
            }), 404
        return jsonify({"symbol": symbol, "price": prices[symbol]})
    except Exception as e:
        logging.exception("api/price: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/check", methods=["GET", "POST"])
def api_run_check():
    try:
        if run_check is None:
            return jsonify({"ok": False, "error": "Checker not available"}), 500
        run_check()
        return jsonify({"ok": True, "message": "Check completed"})
    except Exception as e:
        logging.exception("api/check: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


def _run_broadcast_once() -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.error("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return False
    if not SYMBOLS:
        logging.error("Set STOCK_SYMBOLS in .env (e.g. VCB,TCB,FPT,VNINDEX,VN30)")
        return False
    body = fetch_prices(SYMBOLS, INDEX_CODES)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"🇻🇳 Vietnam stock @ {now}\n\n{body}"
    ok = send_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg)
    if ok:
        logging.info("Broadcast sent to Telegram (%d chars)", len(msg))
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        sys.exit(0 if _run_broadcast_once() else 1)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
