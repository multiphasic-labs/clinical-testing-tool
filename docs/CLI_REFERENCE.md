# CLI flag reference

One-line reference for all flags. See `python3 main.py --help` and the [README](../README.md) for full details.

| Flag | Short description |
|------|--------------------|
| `--persona` | Persona file (default: passive_ideation.json). |
| `--config` | JSON config with `personas` list for batch runs. |
| `--sut-model` | Override SUT model name. |
| `--judge-model` | Override judge model name. |
| `--mock` | Mock mode (default); no API calls. |
| `--live` | Use real API (required for real runs). |
| `--verbose` | Print raw judge JSON before formatted output. |
| `--output-dir` | Directory for result JSON (default: results/). |
| `--quiet` | Only score and result path (for CI). |
| `--md` | Also write Markdown report. |
| `--fail-under` | Exit 1 if any run score < N. |
| `--sut-system-prompt` | Path to SUT system prompt file. |
| `--criteria` | Comma-separated criterion IDs to run. |
| `--personas` | Comma-separated persona names (filter or batch). |
| `--personas-dir` | Run all persona JSONs in this dir. |
| `--persona-tags` | Only run personas with at least one of these tags. |
| `--list-tags` | Print tags and personas; exit. |
| `--validate-personas` | Validate persona schema; exit 0 if OK. |
| `--log` | Append run log to this file. |
| `--batch-summary` | Write batch_summary_*.json (and .md). |
| `--fail-under-criteria` | Per-criterion minimum (e.g. crisis_urgency=2). |
| `--compare-baseline` | Exit 1 if any score below baseline. |
| `--baseline` | Path to baseline file or dir. |
| `--list-personas` | List persona files; exit. |
| `--list-criteria` | List criterion IDs; exit. |
| `--criterion-file` | Path to extra criterion JSON. |
| `--report` | Also write report: html. |
| `--sut-prompts` | Comma-separated prompt files for comparison. |
| `--parallel` | Max N concurrent runs (default: 1). |
| `--csv` | With --batch-summary, also write CSV. |
| `--write-index` | Regenerate results/index.html. |
| `--config-file` | Path to defaults JSON (default: safety-tester-config.json). |
| `--sut` | SUT backend: anthropic, openai, custom. |
| `--sut-endpoint` | For --sut custom: API URL. |
| `--sut-api-key` | For --sut custom or openai (prefer env). |
| `--sut-response-path` | For --sut custom: dot path to assistant text. |
| `--dry-run` | Print what would run; no API. |
| `--history` | Append each run to JSONL file. |
| `--notify-webhook` | POST to URL on exit 1. |
| `--retry-failed` | Re-run only failed from batch summary. |
| `--retry-failed-from` | Batch summary path for --retry-failed. |
| `--max-requests-per-minute` | Rate limit (with --parallel). |
| `--save-baseline` | Write baseline_<persona>.json after run. |
| `--notify-success` | POST to webhook on exit 0. |
| `--notify-format` | Webhook format: slack. |
| `--version` | Print version; exit. |
| `--health-check` | One mock run; exit 0 if OK. |
| `--branded-report` | Write HTML report to PATH. |
| `--report-branding-title` | Title for branded report. |
| `--run-timeout` | Timeout per run (seconds). |
| `--judge` | Judge backend: anthropic, openai. |
| `--criteria-dir` | Load criteria from directory. |
| `--max-runs` | Cap batch at N runs. |
| `--no-color` | Disable colored output. |
| `--shard` | Run only index i where i % M == N (e.g. 0/4). |
| `--junit` | Write JUnit XML to PATH. |
| `--failures-only` | Print only failed runs and stats. |
| `--judge-temperature` | Judge temperature (0–1; default 0). |
| `--report-only` | Re-score existing result JSON(s); no SUT. |
| `--cache-dir` | Cache SUT responses by persona+prompt hash. |
| `--profile` | Print timing per run (SUT vs judge) and total. |
| `--ndjson` | Print one JSON object per run to stdout (for jq). |
| `--redact` | Redact conversation content in saved result JSON. |
| `--criterion-weights` | Weight criteria for final score (e.g. crisis_urgency=2,no_diagnosis=1). |
| `--baseline` | Path or `last` for --compare-baseline (use latest batch summary). |
| `--persona-difficulty` | Only run personas with meta.difficulty matching (easy/medium/hard). |
| `--config-profile` | With --config: use named profile's personas (profiles.NAME.personas). |
| `--repeat` | Run each persona N times; report score distribution (min/max/mean). |
| `--sut-timeout` | Timeout in seconds for SUT (conversation) phase. |
| `--judge-timeout` | Timeout in seconds for judge (scoring) phase. |
| `--log-format` | Log format: text or jsonl (one JSON object per line). |
| `--preflight` | Validate personas, criteria, and (if --live) API keys; then exit. |
| `--interactive` | Interactively pick personas from a numbered list before running. |

## Environment variables

- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` — API keys for SUT/judge.
- `OUTPUT_DIR`, `SUT_MODEL`, `JUDGE_MODEL`, `JUDGE_MODEL_OPENAI` — Override defaults.
- `NOTIFY_WEBHOOK`, `NOTIFY_FORMAT` — Webhook and format (e.g. slack).
- `SAFETY_TESTER_MOCK` — Force mock (1/true/yes).
- `CACHE_DIR` — SUT cache directory.
- `HISTORY_FILE`, `API_TIMEOUT`, `SUT_SYSTEM_PROMPT`, `SUT_ENDPOINT`, `SUT_API_KEY`, `SUT_RESPONSE_PATH` — See .env.example.
