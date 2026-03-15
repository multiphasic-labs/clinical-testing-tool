# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2025-03

### Added

- CLI for scripted mental health safety testing: run persona conversations against a chatbot (SUT), score with an LLM judge, save JSON results.
- Personas: passive/active ideation, mild anxiety, bad day vent, diagnosis seeking, lonely venting, overwhelmed, substance cope, self-harm venting, grief, panic, medication question, caretaker burnout, teen stress, eating distress, relationship abuse, vague physical anxiety, teen crisis, workplace burnout, perinatal worry, identity stress, sleep/low mood, youth substance, chronic pain/mood, disengage (sad path).
- Pluggable SUT backends: Anthropic, OpenAI, custom HTTP API.
- Multiple judge criteria: crisis urgency, no diagnosis, no normalizing self-harm, escalation to human, no promises or specifics.
- Batch runs via config or `--personas-dir`; `--parallel N`, `--max-runs N`, `--shard N/M`; stable alphabetical persona ordering.
- Output: JSON results, optional Markdown/HTML reports, batch summary (JSON/MD/CSV), JUnit XML, audit JSON; `--no-color` for CI.
- Config: optional `safety-tester-config.json` for defaults (`sut_model`, `judge_model`, `output_dir`, `criteria`, `max_runs`, `run_timeout`).
- Baseline comparison and save; retry failed runs; run history (JSONL); failure/success webhooks (Slack-friendly).
- Docker support; health check; version from `pyproject.toml`; persona schema validation; results index and trend scripts; compliance export.
- Mock mode by default; `--live` for real API. Rate limiting and run timeout; judge and SUT retries with clear 401/403 errors.
- Persona metadata: optional `meta` in persona JSON (e.g. author, severity); surfaced in batch summary and compliance export.
- Progress bar for batch runs when not `--quiet`.
- Documentation: README, RUNBOOK, METHODOLOGY, DEPLOYMENT, CUSTOM_SUT_API, PERSONA_SCHEMA.

### Security

- No real user data; synthetic personas only. See SECURITY.md.

[0.1.0]: https://github.com/your-org/mental-health-tester/releases/tag/v0.1.0
