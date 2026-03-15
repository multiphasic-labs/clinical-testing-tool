# Runbook: Mental Health Safety Tester

Short ops guide: when to use the real API, how to read results, add personas, run by tag, and how the scheduled workflow fits in.

---

## When to use `--live`

- **Default (no flag):** Mock mode. No API calls, no key, no charges. Use for development, CI, and the weekly scheduled run.
- **`--live`:** Real Anthropic (and judge) API. Requires `ANTHROPIC_API_KEY` in `.env`. Use when you want to test against the actual model (e.g. before a release or to validate a new prompt).

Example:

```bash
# Mock (default)
python3 main.py --persona passive_ideation.json

# Real API
python3 main.py --persona passive_ideation.json --live
```

---

## Reading results

- **Single run:** One JSON file in `results/` (or `--output-dir`), e.g. `20260315T120000Z_passive_ideation.json`. Contains:
  - `schema_version`, `timestamp_utc`, `persona_name`, `run_id` (when from a batch)
  - `conversation` (full transcript)
  - `judge_results` (per-criterion score, rationale, critical_failures, positive_behaviors)
  - `criterion_scores`, `final_score` (min across criteria)
- **Batch run:** With `--batch-summary`, you get `batch_summary_TIMESTAMP.json` (and optional `.md`, `.csv`) with one row per persona: score, error, result_path, criterion_scores; and `summary_by_tag` (passed/failed/total per tag) when persona_tags.json exists. A **Summary by tag** table is also printed when not quiet.
- **Audit:** With `--batch-summary`, an optional `batch_audit_TIMESTAMP.json` is written for compliance (schema_version, run_id, runs, timestamps).

---

## Adding a persona and running by tag

1. Add a new JSON file under `personas/` (array of turns with `turn`, `message`, `expected_behavior`). You can use the helper: `python3 scripts/add_persona.py` (interactive). See CONTRIBUTING.md for the schema.
2. Optionally add it to `personas/batch_config.json` and to `personas/persona_tags.json` with tags (e.g. `"my_persona.json": ["support"]`). The add_persona script can add tags when creating the persona.
3. Run all personas in the dir: `python3 main.py --personas-dir personas`
4. Run only certain tags: `python3 main.py --personas-dir personas --persona-tags crisis,support`
5. List tags and which personas have them: `python3 main.py --list-tags`
6. Validate all persona files: `python3 main.py --validate-personas`

---

## Scheduled workflow (weekly)

- **File:** `.github/workflows/scheduled.yml`
- **Default:** Runs in **mock** (no API key). Every Monday 00:00 UTC (and on `workflow_dispatch`). Runs `python3 main.py --config personas/batch_config.json --fail-under 2 --quiet --batch-summary`. No secrets required.
- **To use the real API on schedule:** Add `ANTHROPIC_API_KEY` (and optionally `NOTIFY_WEBHOOK`) as repo secrets, then edit the workflow and add `--live` to the `python3 main.py ...` command in the "Run safety tester" step.

---

## Quick reference

| Goal                    | Command |
|-------------------------|--------|
| One persona (mock)      | `python3 main.py --persona passive_ideation.json` |
| One persona (live)      | `python3 main.py --persona passive_ideation.json --live` |
| All personas in dir     | `python3 main.py --personas-dir personas` |
| Only crisis personas    | `python3 main.py --personas-dir personas --persona-tags crisis` |
| Batch from config       | `python3 main.py --config personas/batch_config.json --batch-summary` |
| List personas           | `python3 main.py --list-personas` |
| List tags               | `python3 main.py --list-tags` |
| Validate persona files  | `python3 main.py --validate-personas` |
| Health check (deploy)   | `python3 main.py --health-check` |
| Add persona (interactive)| `python3 scripts/add_persona.py` |
| Generate results index    | `python3 scripts/generate_results_index.py` (or use `--write-index` after a run) |
| Run with timeout (e.g. 300s per run) | `python3 main.py --config ... --run-timeout 300` |
| Use OpenAI as judge     | `python3 main.py --judge openai` (set `JUDGE_MODEL_OPENAI` or config `judge_model_openai`) |
| Load criteria from dir  | `python3 main.py --criteria-dir path/to/criteria` |
| Quick smoke (first N)    | `python3 main.py --personas-dir personas --max-runs 3` |
| Slack webhook format    | `python3 main.py ... --notify-webhook URL --notify-format slack` |
| Trend (last N batches)  | `python3 scripts/trend_batch_summaries.py --last 10 [--html trend.html]` |
| Compliance export       | `python3 scripts/export_compliance.py --last --out bundle.zip` |
| Latest run (stable URL) | Open `results/latest.html` (generated with index) |
