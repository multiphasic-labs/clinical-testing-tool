# Platform API (v1 scaffold)

This package is the first backend step from CLI tooling to product:

- run registry (`/runs`)
- run detail + child collections (`/runs/{id}`, `/items`, `/findings`)
- retry hook (`/runs/{id}/retry-failed`)

## Run locally

```bash
export SAFETY_PLATFORM_DB_URL=sqlite:///./safety_platform.db
python3 -m uvicorn platform_api.app:app --reload --port 8001
```

Migrations run automatically on import via Alembic. To upgrade manually from the repo root:

```bash
export SAFETY_PLATFORM_DB_URL=sqlite:///./safety_platform.db
python3 -m alembic upgrade head
```

### Postgres

Use a URL like `postgresql+psycopg2://user:pass@host:5432/dbname` and install a driver, for example:

```bash
pip install psycopg2-binary
```

Open docs at `http://localhost:8001/docs`.

### Queue worker (recommended)

If `SAFETY_PLATFORM_REDIS_URL` (or `REDIS_URL`) is set, `POST /runs` will enqueue work on Redis/RQ instead of running inside the API process.

Run the worker in a second terminal:

```bash
export SAFETY_PLATFORM_REDIS_URL=redis://localhost:6379/0
python3 -m platform_api.rq_worker
```

## Notes

- Set `"execute": true` on `POST /runs` to run `main.py` in a FastAPI background task, then persist `run_items` and `findings` from `batch_summary_*.json` (or per-persona result JSONs if no batch summary).
- `GET /ui` provides a lightweight built-in dashboard to create runs and inspect details/findings.
- Set `SAFETY_PLATFORM_API_KEY` to require `x-api-key` on `/runs*` endpoints (health, root, docs, and `/ui` remain open).
- Output artifacts go under `SAFETY_PLATFORM_ARTIFACTS` (default `./platform_artifacts/{run_id}/output`).
- Finding generation rules are policy-driven via `platform_api/finding_policy.json`; override with `SAFETY_PLATFORM_FINDING_POLICY=/abs/path/to/finding_policy.json`.
- `POST /runs/{id}/retry-failed` re-runs when the source run has `execution_config` (for example after an executed run).
- Schema changes: add a new Alembic revision (`python3 -m alembic revision --autogenerate -m "describe_change"`), review the file, then `alembic upgrade head`.
- If you have an old SQLite DB created before Alembic, either delete it and restart, or if the schema already matches the latest migration, run `python3 -m alembic stamp head` once (only when you are sure).
- Set `SAFETY_PLATFORM_SKIP_MIGRATIONS=1` to skip auto-migrate on import (not recommended for production).

