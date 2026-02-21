# Vietnam Stock → Telegram

Observer-based alerts: set target prices per symbol; when price is at or below target, you get a Telegram alert (check runs every 30 seconds). Optional: one-off broadcast of all configured symbols to Telegram.

## Setup

### 1. Telegram Bot & Chat ID

- **Bot token**: In Telegram, open [@BotFather](https://t.me/BotFather), send `/newbot`, follow the steps, and copy the token.
- **Chat ID**: Send any message to [@userinfobot](https://t.me/userinfobot); it will reply with your `Id` (that’s your chat ID). Or start a chat with your bot, then open:
  `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser and find `"chat":{"id": ...}`.

### 2. Venv and install dependencies

Requires **git** (to install vnstock from GitHub). Then:

```bash
cd vietnam-stock-telegram
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set:
#   TELEGRAM_BOT_TOKEN=...
#   TELEGRAM_CHAT_ID=...
```

Optional: set `STOCK_SYMBOLS` (comma-separated), e.g. `VCB,TCB,FPT,VNM,VHM,VNINDEX,VN30`. Default is a small set of popular symbols.

## Run

- **API + background checker** (default; use this for the Web UI):

  ```bash
  python run.py
  # or: python3 run.py   or: .venv/bin/python run.py
  ```

  Starts the Flask API (port 5003) and the 30-second alert checker.

- **Once** (single fetch of config symbols and send one Telegram message):

  ```bash
  python run.py --once
  ```

### Web UI (observer prices & alerts)

**Python = API only.** The UI is **React** (Vite + TypeScript) in `frontend/`. Set target prices per symbol; when the price is at or below your target, you get a Telegram alert. The app checks **every 30 seconds**.

Run both the API and the React app:

```bash
# Terminal 1: Flask API (default port 5003; set FLASK_PORT in .env)
python run.py

# Terminal 2: React UI — Vite proxies /api to Flask
cd frontend && npm install && npm run dev
# Open http://127.0.0.1:5173
```

For production, build the frontend and serve `frontend/dist` with any static server (e.g. `npx serve frontend/dist`); keep `python run.py` running for the API. Point the frontend’s API base URL at your Flask host, or use the same proxy in your deployment.

- **Observer prices**: Add symbols and target prices in the UI. Alert fires when current price ≤ target. Click **Save** to store.
- **Alert history**: Table of past alerts; filter by symbol.

## Data sources (tried in order)

1. **vnstock** — installed from [thinh-vu/vnstock](https://github.com/thinh-vu/vnstock) (GitHub). Uses `Trading(source).price_board()`: tries **KBS** (TCBS) then **VCI**. Optional: set `VNSTOCK_API_KEY` in `.env` (free key at [vnstocks.com/login](https://vnstocks.com/login)) for higher rate limits.
2. **VNDirect WebSocket** — real-time feed (BidAsk + MarketInformation for indices).
3. **VNDirect REST** — latest close, parallel requests.
4. **Yahoo Finance** — `symbol.VN` when others are blocked.

If all fail, try another network or VPN.

## Production (Supabase/Neon + Render)

See **[DEPLOY.md](DEPLOY.md)** for hosting the API on Render, using Supabase or Neon for the database, and deploying the React frontend with `VITE_API_URL`.

## License

Use for personal, non-commercial purposes.
