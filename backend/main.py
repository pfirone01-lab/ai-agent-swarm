"""
API server for the AI Agent Swarm.

Wraps the Generator -> Evaluator -> Selector -> Formatter pipeline (agents.py)
behind two endpoints:

  POST /api/runs        start a new pipeline run for a prompt, returns {id}
  GET  /api/runs/{id}    poll the current state of that run

A run takes a few minutes (each Gemini call is deliberately throttled to
respect the free tier), so the frontend polls rather than waiting on one
long request.

Run with:
    GEMINI_API_KEY=your_key uvicorn main:app --reload --port 8787
"""
import threading
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents import EmailAgentSwarm

app = FastAPI(title="AI Agent Swarm API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local/portfolio tool - lock this down if you deploy it publicly
    allow_methods=["*"],
    allow_headers=["*"],
)

STAGES = ["generator", "evaluator", "selector", "formatter"]

# In-memory job store. Fine for a single-user local/demo tool; swap for a
# real datastore if this ever needs to survive a server restart or serve
# multiple concurrent users reliably.
runs: dict[str, dict] = {}


def new_run_state(prompt: str) -> dict:
    return {
        "id": None,
        "prompt": prompt,
        "status": "running",  # running | done | error
        "stages": {s: {"status": "pending", "detail": None} for s in STAGES},
        "candidates": [],
        "evaluations": [],
        "best_index": None,
        "selection_rationale": None,
        "final_email": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def run_pipeline(run_id: str, prompt: str):
    state = runs[run_id]

    def on_update(patch: dict):
        stage = patch.get("stage")
        if stage:
            stage_state = state["stages"][stage]
            if "stage_status" in patch:
                stage_state["status"] = patch["stage_status"]
            if "detail" in patch:
                stage_state["detail"] = patch["detail"]
        if "candidates" in patch:
            state["candidates"] = patch["candidates"]
        if "evaluations" in patch:
            state["evaluations"] = patch["evaluations"]
        if "best_index" in patch:
            state["best_index"] = patch["best_index"]
        if "selection_rationale" in patch:
            state["selection_rationale"] = patch["selection_rationale"]
        if "final_email" in patch:
            state["final_email"] = patch["final_email"]

    try:
        swarm = EmailAgentSwarm()
        swarm.generate_email(prompt, on_update=on_update)
        state["status"] = "done"
    except Exception as exc:  # surfaced to the frontend rather than a bare 500
        state["status"] = "error"
        state["error"] = str(exc)


class RunRequest(BaseModel):
    prompt: str


@app.post("/api/runs")
def start_run(req: RunRequest):
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    run_id = uuid.uuid4().hex[:12]
    state = new_run_state(prompt)
    state["id"] = run_id
    runs[run_id] = state

    thread = threading.Thread(target=run_pipeline, args=(run_id, prompt), daemon=True)
    thread.start()

    return {"id": run_id}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    state = runs.get(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="Run not found.")
    return state


@app.get("/api/health")
def health():
    return {"ok": True}
