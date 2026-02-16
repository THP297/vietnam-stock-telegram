"""Configuration: symbols to watch and env vars."""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram (required)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Vietnam stock symbols to fetch (comma-separated or list)
# Default: VN30 representative + indices
DEFAULT_SYMBOLS = "CTG, VIB"
SYMBOLS_STR = os.getenv("STOCK_SYMBOLS", DEFAULT_SYMBOLS)
SYMBOLS = [s.strip() for s in SYMBOLS_STR.split(",") if s.strip()]

# Optional: vnstock API key for higher limits (get free key at https://vnstocks.com/login)
VNSTOCK_API_KEY = os.getenv("VNSTOCK_API_KEY", "").strip()

INDEX_CODES = ("VNINDEX", "VN30", "HNXIndex", "HNX30")
