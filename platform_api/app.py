from __future__ import annotations

import os
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .db import get_db
from .migrate import run_migrations
from .queue import enqueue_run
from .schemas import ArtifactOut, FindingOut, HealthOut, RunCreate, RunItemOut, RunOut
from .service import create_run, get_run, list_findings, list_run_artifacts, list_run_items, list_runs, retry_failed_run
from .worker import run_evaluation_job

app = FastAPI(
    title="Mental Health Safety Platform API",
    version="0.1.0",
    description="Run registry + findings API for continuous safety monitoring.",
)

run_migrations()


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("SAFETY_PLATFORM_API_KEY")
    if not expected:
        return
    if x_api_key == expected:
        return
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut()


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "docs": "/docs"}


@app.get("/ui", response_class=HTMLResponse)
def ui() -> str:
    return """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Mental Health Safety Platform</title>
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 24px; max-width: 980px; }
      input, button, textarea { font-size: 14px; padding: 8px; margin: 4px 0; }
      .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
      .card { border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-top: 12px; }
      pre { background: #f7f7f7; padding: 8px; overflow: auto; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border: 1px solid #eee; padding: 8px; text-align: left; }
    </style>
  </head>
  <body>
    <h1>Mental Health Safety Platform</h1>
    <div class="card">
      <h3>Create run</h3>
      <div class="row">
        <label>API Key (optional): <input id="apiKey" type="password" size="28" /></label>
        <label>Model name: <input id="modelName" value="unknown" /></label>
        <label><input id="execute" type="checkbox" checked /> execute</label>
      </div>
      <div class="row">
        <button onclick="createRun()">Create Run</button>
        <button onclick="refreshRuns()">Refresh Runs</button>
      </div>
      <pre id="createOut"></pre>
    </div>
    <div class="card">
      <h3>Recent runs</h3>
      <table>
        <thead><tr><th>ID</th><th>Status</th><th>Progress</th><th>Created</th><th>Actions</th></tr></thead>
        <tbody id="runsBody"></tbody>
      </table>
    </div>
    <div class="card">
      <h3>Run details</h3>
      <pre id="detailOut"></pre>
      <h4>Findings</h4>
      <pre id="findingsOut"></pre>
    </div>
    <script>
      function headers() {
        const key = document.getElementById("apiKey").value;
        const h = { "Content-Type": "application/json" };
        if (key) h["x-api-key"] = key;
        return h;
      }

      async function createRun() {
        const payload = {
          model_name: document.getElementById("modelName").value || "unknown",
          execute: document.getElementById("execute").checked
        };
        const r = await fetch("/runs", { method: "POST", headers: headers(), body: JSON.stringify(payload) });
        const data = await r.json();
        document.getElementById("createOut").textContent = JSON.stringify(data, null, 2);
        await refreshRuns();
      }

      async function refreshRuns() {
        const r = await fetch("/runs?limit=20", { headers: headers() });
        const runs = await r.json();
        const body = document.getElementById("runsBody");
        body.innerHTML = "";
        for (const run of runs) {
          const prog = `${run.processed_items || 0}/${run.total_items || 0} (failed ${run.failed_items || 0})`;
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${run.id}</td><td>${run.status}</td><td>${prog}</td><td>${run.created_at}</td>
            <td><button onclick="showRun('${run.id}')">View</button></td>`;
          body.appendChild(tr);
        }
      }

      let pollTimer = null;
      async function showRun(id) {
        if (pollTimer) clearInterval(pollTimer);
        async function refreshOne() {
          const [d, f] = await Promise.all([
            fetch(`/runs/${id}`, { headers: headers() }),
            fetch(`/runs/${id}/findings`, { headers: headers() })
          ]);
          const detail = await d.json();
          document.getElementById("detailOut").textContent = JSON.stringify(detail, null, 2);
          document.getElementById("findingsOut").textContent = JSON.stringify(await f.json(), null, 2);
          if (detail.status === "completed" || detail.status === "failed") {
            clearInterval(pollTimer);
            pollTimer = null;
          }
        }
        await refreshOne();
        pollTimer = setInterval(refreshOne, 1500);
      }

      refreshRuns();
    </script>
  </body>
</html>
"""


@app.post("/runs", response_model=RunOut, status_code=201)
def create_run_endpoint(
    payload: RunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> RunOut:
    run = create_run(db, payload)
    if payload.execute:
        if not enqueue_run(run.id):
            background_tasks.add_task(run_evaluation_job, run.id)
    return run


@app.get("/runs", response_model=list[RunOut])
def list_runs_endpoint(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> list[RunOut]:
    return list_runs(db, limit=limit, offset=offset)


@app.get("/runs/{run_id}", response_model=RunOut)
def get_run_endpoint(run_id: str, db: Session = Depends(get_db), _api_key: None = Depends(require_api_key)) -> RunOut:
    run = get_run(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/runs/{run_id}/items", response_model=list[RunItemOut])
def list_run_items_endpoint(
    run_id: str,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> list[RunItemOut]:
    if get_run(db, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return list_run_items(db, run_id=run_id, limit=limit, offset=offset)


@app.get("/runs/{run_id}/findings", response_model=list[FindingOut])
def list_findings_endpoint(
    run_id: str,
    limit: int = 200,
    offset: int = 0,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> list[FindingOut]:
    if get_run(db, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return list_findings(db, run_id=run_id, limit=limit, offset=offset)


@app.get("/runs/{run_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts_endpoint(
    run_id: str, db: Session = Depends(get_db), _api_key: None = Depends(require_api_key)
) -> list[ArtifactOut]:
    if get_run(db, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return list_run_artifacts(db, run_id=run_id)


@app.post("/runs/{run_id}/retry-failed", response_model=RunOut, status_code=202)
def retry_failed_endpoint(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _api_key: None = Depends(require_api_key),
) -> RunOut:
    new_run, should_execute = retry_failed_run(db, run_id)
    if new_run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if should_execute:
        if not enqueue_run(new_run.id):
            background_tasks.add_task(run_evaluation_job, new_run.id)
    return new_run

