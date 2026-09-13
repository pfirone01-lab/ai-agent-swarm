# AI Agent Swarm

A 4-agent AI pipeline that generates, evaluates, selects, and formats
optimised sales emails automatically. Originally a script triggered by
GitHub Actions; this version adds a real frontend so you can run it and
watch it work from a browser instead of reading Action logs.

## Agents

- **Generator** — creates 3 versions of the email
- **Evaluator** — scores each version on clarity, CTA, and tone
- **Selector** — picks the highest performing version
- **Formatter** — polishes and delivers the final output

Built with the Gemini API. Model-agnostic — swap `agents.py`'s
`call_gemini` for any other provider without touching the pipeline logic.

## Project layout

```
backend/    FastAPI server that runs the pipeline and exposes it as a
            pollable job API (POST /api/runs, GET /api/runs/{id})
frontend/   React (Vite) app: enter a prompt, watch the four stages run,
            read the scored drafts and the final email
agent_swarm.py, run-swarm.yml
            the original standalone script + GitHub Actions workflow —
            unchanged, still works as a scheduled/manual CLI run
```

## Running it locally

**1. Backend**

```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
uvicorn main:app --reload --port 8787
```

**2. Frontend** (in a separate terminal)

```bash
cd frontend
npm install
cp .env.example .env      # points the app at http://localhost:8787
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`), type a
brief, and hit **Run the swarm**. Each Gemini call is throttled to respect
free-tier rate limits (see `GEMINI_CALL_DELAY` in `backend/agents.py`), so
a full run takes a few minutes — the UI shows live progress per stage
while it works rather than a single loading spinner.

## Still using GitHub Actions

`agent_swarm.py` and `run-swarm.yml` are untouched — the scheduled/manual
Action still works exactly as before, independent of the new frontend.
`backend/agents.py` is a copy of that same agent logic adapted to report
progress incrementally instead of only printing to stdout.

## Deploying it: GitHub Pages (frontend) + Render (backend)

GitHub Pages only serves static files — it can host the React frontend but
not the FastAPI backend, so this needs two pieces:

**1. Push the repo to GitHub**

```bash
git init
git add .
git commit -m "Add React frontend + FastAPI backend"
git branch -M main
git remote add origin https://github.com/<you>/ai-agent-swarm.git
git push -u origin main
```

**2. Deploy the backend (Render free tier)**

- On [render.com](https://render.com), New → Web Service → connect this repo.
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add environment variable `GEMINI_API_KEY` with your key.
- Deploy, then copy the service URL, e.g. `https://ai-agent-swarm-api.onrender.com`.
- In `backend/main.py`, change `allow_origins=["*"]` to your GitHub Pages
  origin, e.g. `["https://<you>.github.io"]`, and push that change.

**3. Deploy the frontend (GitHub Pages via Actions)**

Already set up in `.github/workflows/deploy-frontend.yml` — it builds the
frontend and publishes it whenever you push to `main`.

- In the repo: Settings → Pages → Source → **GitHub Actions**.
- Settings → Secrets and variables → Actions → Variables → add
  `VITE_API_URL` set to your Render URL from step 2.
- If your repo isn't named `ai-agent-swarm`, update `base` in
  `frontend/vite.config.js` to match (`/<your-repo-name>/`).
- Push to `main` (or run the workflow manually from the Actions tab). The
  site will be live at `https://<you>.github.io/<repo-name>/`.

**Note on Render's free tier:** the service spins down after inactivity,
so the first request after a while can take ~30s to wake it up before the
pipeline even starts. Fine for a portfolio demo, worth mentioning if you
link it somewhere.
