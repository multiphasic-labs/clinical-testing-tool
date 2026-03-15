# Deployment and production use

This guide covers running the mental health safety tester in production-like environments: env vars, recommended flags, cron, and CI.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes (for real runs) | API key for SUT and judge (Anthropic). |
| `OPENAI_API_KEY` | If `--sut openai` | API key for OpenAI SUT. |
| `SUT_ENDPOINT` | If `--sut custom` | URL of the chat API. |
| `SUT_API_KEY` | Optional | Bearer key for custom SUT or override. |
| `OUTPUT_DIR` | No | Default `results/`. |
| `SUT_MODEL` | No | Override SUT model (e.g. `gpt-4o-mini` for OpenAI). |
| `JUDGE_MODEL` | No | Override judge model. |
| `API_TIMEOUT` | No | Request timeout in seconds (default 120). |
| `HISTORY_FILE` | No | JSONL path for run history (`--history`). |
| `NOTIFY_WEBHOOK` | No | URL to POST on failure (e.g. Slack). |
| `SAFETY_TESTER_MOCK` | No | Set to `1` for mock (no API calls). |

Use a `.env` file (see `.env.example`) or inject vars in your runner (cron, CI, Docker).

**Deploy verification:** Run `python3 main.py --health-check` or `bash scripts/health_check.sh` to confirm the pipeline works in the target environment (one mock run, exit 0 on success). Use in your deploy or smoke step.

**Methodology:** For a short “what we test” (personas, criteria, judge, limitations) for sales and compliance, see [METHODOLOGY.md](METHODOLOGY.md).

**Runbook:** For when to use `--live`, how to read results, add personas, run by tag, and the scheduled workflow, see [RUNBOOK.md](RUNBOOK.md).

## Recommended flags for production

- **Batch run:** `--config personas/batch_config.json`
- **Fail gate:** `--fail-under 2` (or use `--fail-under-criteria crisis_urgency=2,no_diagnosis=1`)
- **Quiet:** `--quiet` for script/CI
- **History:** `--history results/run_history.jsonl` for trends
- **Notify:** `--notify-webhook $NOTIFY_WEBHOOK` so failures post to Slack (or similar); add `--notify-success` to also POST when the run passes
- **Save baseline:** `--save-baseline` to write current run’s scores as baseline for future `--compare-baseline` regression checks
- **Rate limit (optional):** `--max-requests-per-minute 30` if you hit provider limits

Example:

```bash
python3 main.py \
  --config personas/batch_config.json \
  --fail-under 2 \
  --quiet \
  --batch-summary \
  --history results/run_history.jsonl \
  --notify-webhook "$NOTIFY_WEBHOOK"
```

## Running with cron

Run weekly (e.g. Monday 2am):

```bash
0 2 * * 1 cd /path/to/mental-health-tester && . .env && python3 main.py --config personas/batch_config.json --fail-under 2 --quiet --batch-summary --history results/run_history.jsonl >> results/cron.log 2>&1
```

Use a virtualenv or system Python that has the dependencies installed.

## CI (GitHub Actions)

- **On every push/PR:** The default `CI` workflow runs tests, `--validate-personas`, and a mock batch (see `.github/workflows/ci.yml`). No secrets required.
- **Scheduled run (mock by default):** `.github/workflows/scheduled.yml` runs the full batch weekly (e.g. Monday 00:00 UTC). By default it uses **mock** (no API key). See [RUNBOOK](RUNBOOK.md#scheduled-workflow-weekly) for how to switch to a **weekly live run** (add `ANTHROPIC_API_KEY` and `--live`, optional `NOTIFY_WEBHOOK`, `--notify-success`, `--save-baseline`, or `--write-index`).

## Docker

See the main README **Docker** section. Example production-style run:

```bash
docker run --env-file .env \
  -v $(pwd)/results:/app/results \
  mental-health-tester:latest \
  --config personas/batch_config.json \
  --fail-under 2 \
  --quiet \
  --batch-summary
```

## Retrying failed runs

After a batch, if some runs failed or scored below threshold:

```bash
python3 main.py --retry-failed --retry-failed-from results/batch_summary_20260315T120000Z.json --fail-under 2 --quiet
```

Omit `--retry-failed-from` to use the latest `batch_summary_*.json` in the output dir.

## Audit and compliance

- Each batch write can produce `batch_audit_TIMESTAMP.json` (see `_write_batch_summary` with audit enabled) with run metadata and scores.
- Use `--history` and `scripts/show_history.py` for a simple run history.
- Store result JSONs and audit files in a secure, append-only location if needed for compliance.
