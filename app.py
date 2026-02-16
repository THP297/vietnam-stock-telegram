"""API only: observer prices, history, 30-sec checker. UI is React (frontend/)."""
import logging

from flask import Flask, jsonify, request

from config import DEFAULT_SYMBOLS, SYMBOLS
from store import get_history_filtered, load_observers, save_observers

# Start background checker (every 30 sec)
try:
    from alert_checker import start_background_checker
    start_background_checker()
except Exception as e:
    logging.warning("Background checker not started: %s", e)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


@app.after_request
def cors(resp):
    """Allow React dev server (and any origin) to call the API."""
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


def get_symbol_list() -> list[str]:
    """Symbols to show in UI (from DEFAULT_SYMBOLS / config)."""
    return [s.strip() for s in (DEFAULT_SYMBOLS or "").split(",") if s.strip()] or list(SYMBOLS)


@app.route("/")
def index():
    """Health check / confirms this app is running (not default PythonAnywhere app)."""
    return jsonify({
        "ok": True,
        "app": "vietnam-stock-telegram",
        "endpoints": ["/api/symbols", "/api/observers", "/api/history", "/api/check"],
    })


# API routes
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
    save_observers(observers)
    return jsonify({"ok": True, "observers": observers})


@app.route("/api/history")
def api_history():
    symbol = request.args.get("symbol", "").strip() or None
    history = get_history_filtered(symbol)
    return jsonify({"history": history})


@app.route("/api/check", methods=["GET", "POST"])
def api_run_check():
    """Trigger one alert check (for Render cron or external scheduler)."""
    try:
        from alert_checker import run_check
        run_check()
        return jsonify({"ok": True, "message": "Check completed"})
    except Exception as e:
        logging.exception("api/check: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)
