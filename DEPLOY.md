# Production: Supabase/Neon (DB) + Render or PythonAnywhere (API)

## 1. Database (Supabase or Neon)

### Option A: Supabase

1. Go to [supabase.com](https://supabase.com) → New project.
2. In **Settings → Database** copy the **Connection string** (URI). Use "Transaction" mode.
3. It looks like: `postgresql://postgres.[ref]:[PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres`
4. Replace `[PASSWORD]` with your database password. This is your **DATABASE_URL**.

### Option B: Neon

1. Go to [neon.tech](https://neon.tech) → New project.
2. In the dashboard copy the **Connection string** (e.g. from Connection details).
3. It looks like: `postgresql://user:pass@ep-xxx.region.aws.neon.tech/neondb?sslmode=require`
4. This is your **DATABASE_URL**.

No manual table creation needed: the API creates `observers`, `history`, and `last_alerted` on first use when `DATABASE_URL` is set.

---

## 2. API on Render

1. Go to [render.com](https://render.com) → **New** → **Web Service**.
2. Connect your repo (or use the repo that contains this project).
3. **Root directory**: leave blank or set to the folder that contains `app.py`, `requirements.txt`, etc. (e.g. `vietnam-stock-telegram` if the repo root is above it).
4. **Build command**: `pip install -r requirements.txt`  
   (If you use a subfolder: `cd vietnam-stock-telegram && pip install -r requirements.txt`)
5. **Start command**: `gunicorn -w 1 -b 0.0.0.0:$PORT app:app`  
   (If subfolder: `cd vietnam-stock-telegram && gunicorn -w 1 -b 0.0.0.0:$PORT app:app`)
6. **Environment variables** (Render → Environment):
   - `TELEGRAM_BOT_TOKEN` – from BotFather
   - `TELEGRAM_CHAT_ID` – your chat ID
   - `DATABASE_URL` – the Supabase or Neon connection string from step 1
   - `STOCK_SYMBOLS` – optional, e.g. `VCB,TCB,SSI,VNM,FPT,VNINDEX,VN30`
   - `VNSTOCK_API_KEY` – optional (from vnstocks.com/login)
7. Deploy. Your API URL will be like `https://vietnam-stock-api.onrender.com`.

**Free tier note:** The service may sleep after inactivity. The in-process checker (every 30 sec) only runs while the service is awake. To run checks when the app is sleeping, use an external cron (e.g. [cron-job.org](https://cron-job.org)) to call **GET** (or POST) **`https://your-api.onrender.com/api/check`** every 30 seconds (or every minute).

---

## 3. Frontend (React)

The UI is in `frontend/`. Build it and point it at your Render API.

1. **Set API base URL for production**

   In `frontend/src/api.ts` the requests use `/api`. For local dev, Vite proxies `/api` to Flask. For production, either:

   - Host the frontend on the **same origin** as the API (e.g. Render static site on same domain), then `/api` still works, or
   - Use an **env variable** for the API base (e.g. `VITE_API_URL`) and prefix requests with it.

   Example with `VITE_API_URL`:

   - In `frontend/.env.production`:  
     `VITE_API_URL=https://vietnam-stock-api.onrender.com`
   - In `frontend/src/api.ts`:  
     `const API = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL + '/api' : '/api';`
   - Then build: `cd frontend && npm run build`.

2. **Host the build**

   - **Render**: New → **Static Site** → connect repo, build command `cd frontend && npm install && npm run build`, publish directory `frontend/dist`. Add env `VITE_API_URL=https://vietnam-stock-api.onrender.com` for the build.
   - **Vercel / Netlify**: Same idea – build `frontend`, publish `frontend/dist`, set `VITE_API_URL` to your Render API URL.

---

---

## 4. API on PythonAnywhere (alternative to Render)

PythonAnywhere keeps the web app running (no sleep), so the in-process 30‑second checker runs without an external cron.

### 4.1 Get the code on PythonAnywhere

- **Option A – Git:** In a Bash console on PythonAnywhere:
  ```bash
  cd ~
  git clone https://github.com/YOUR_USER/YOUR_REPO.git
  cd vietnam-stock-telegram   # or the folder that contains app.py
  ```
- **Option B – Upload:** Zip the project (excluding `frontend/node_modules`, `__pycache__`, `.env`) and upload via **Files**, then extract in your home directory (e.g. `~/vietnam-stock-telegram`).

### 4.2 Virtualenv and dependencies

In a Bash console:

```bash
cd ~/vietnam-stock-telegram
mkvirtualenv --python=/usr/bin/python3.10 vietnam-stock   # or python3.11
pip install -r requirements.txt
```

If `vnstock` from Git fails, try: `pip install vnstock` (PyPI) or leave it; the app falls back to VNDirect/Yahoo.

### 4.3 Web app and WSGI

1. **Web** tab → **Add a new web app** → **Flask** → choose Python 3.10 (or 3.11).
2. **Source code:** set to your project folder, e.g. `/home/YOUR_USERNAME/vietnam-stock-telegram`.
3. **WSGI configuration file:** open it and replace the Flask section so it loads this project:

   ```python
   import sys
   path = '/home/YOUR_USERNAME/vietnam-stock-telegram'
   if path not in sys.path:
       sys.path.insert(0, path)
   from app import app as application
   ```

   (Replace `YOUR_USERNAME` with your PythonAnywhere username.)  
   Alternatively you can point the WSGI file to `wsgi.py` in the project and set the path inside `wsgi.py` to the same folder.

4. **Virtualenv:** in the Web tab, set it to `~/.virtualenvs/vietnam-stock` (or the path you used with `mkvirtualenv`).
5. **Reload** the web app.

### 4.4 Environment variables

PythonAnywhere does not load `.env` from the project by default. Use one of:

- **Web** tab → your app → **Environment variables** (if available), and add:
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
  - `DATABASE_URL` (Supabase/Neon URI, if you use PostgreSQL)
  - `STOCK_SYMBOLS` (optional)
  - `VNSTOCK_API_KEY` (optional)
- Or set them in the **WSGI file** before importing the app (not ideal for secrets):
  ```python
  import os
  os.environ["TELEGRAM_BOT_TOKEN"] = "your-token"
  os.environ["TELEGRAM_CHAT_ID"] = "your-chat-id"
  # ... then the path and "from app import app as application"
  ```

If you don’t set `DATABASE_URL`, the app uses JSON files in `data/` (no PostgreSQL).

### 4.5 Outbound HTTPS (whitelist)

- **Free accounts:** Only allowlisted domains can be used for outbound HTTPS. `api.telegram.org` is already allowlisted. For Supabase/Neon (e.g. `*.supabase.com`, `*.neon.tech`) and for price data (e.g. VNDirect, Yahoo), either use a **paid account** (unrestricted outbound) or request domains via [PythonAnywhere allowlist](https://help.pythonanywhere.com/pages/RequestingAllowlistAdditions/).
- **Paid accounts:** Outbound HTTPS is unrestricted; Telegram, Supabase/Neon, and price APIs work without changes.

### 4.6 Frontend with PythonAnywhere API

Build the frontend with the PythonAnywhere API URL:

- `VITE_API_URL=https://YOUR_USERNAME.pythonanywhere.com`  
  Then host the built `frontend/dist` on GitHub Pages, Vercel, Netlify, or Render Static Site.

---

## 5. Summary

| Component   | Where                     | Purpose                                                  |
| ----------- | ------------------------- | -------------------------------------------------------- |
| Database    | Supabase or Neon          | `observers`, `history`, `last_alerted`                   |
| API         | Render or PythonAnywhere  | Flask; on PA the 30‑sec checker runs in-process          |
| Frontend    | Render / Vercel / Netlify | React app, calls API via `VITE_API_URL`                  |
| Cron (opt.) | cron-job.org etc.         | GET `/api/check` every 30 sec if using Render (sleeping) |
