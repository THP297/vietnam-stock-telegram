# Production: Supabase/Neon (DB) + Render (API)

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

**Free tier note:** The service may sleep after inactivity. The in-process checker (every 5 min) only runs while the service is awake. To run checks when the app is sleeping, use an external cron (e.g. [cron-job.org](https://cron-job.org)) to call **GET** (or POST) **`https://your-api.onrender.com/api/check`** every 5 minutes.

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

## 4. Summary

| Component   | Where                     | Purpose                                       |
| ----------- | ------------------------- | --------------------------------------------- |
| Database    | Supabase or Neon          | `observers`, `history`, `last_alerted`        |
| API         | Render Web Service        | Flask + gunicorn, `/api/*`, `/api/check`      |
| Frontend    | Render / Vercel / Netlify | React app, calls API via `VITE_API_URL`       |
| Cron (opt.) | cron-job.org etc.         | GET `/api/check` every 5 min if Render sleeps |
