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

## Recommended flags for production

- **Batch run:** `--config personas/batch_config.json`
- **Fail gate:** `--fail-under 2` (or use `--fail-under-criteria crisis_urgency=2,no_diagnosis=1`)
- **Quiet:** `--quiet` for script/CI
- **History:** `--history results/run_history.jsonl` for trends
- **Notify:** `--notify-webhook $NOTIFY_WEBHOOK` so failures post to Slack (or similar)
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

- **On every push/PR:** The default `CI` workflow runs tests and a mock batch (see `.github/workflows/ci.yml`). No secrets required.
- **Scheduled run:** Use `.github/workflows/scheduled.yml` to run the full batch on a schedule (e.g. weekly). Add `ANTHROPIC_API_KEY` and optionally `NOTIFY_WEBHOOK` as repository secrets, then enable the workflow.

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
