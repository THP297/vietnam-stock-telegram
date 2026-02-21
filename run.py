from backend.app import app, _run_broadcast_once
from backend.config import FLASK_HOST, FLASK_PORT

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        sys.exit(0 if _run_broadcast_once() else 1)
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
