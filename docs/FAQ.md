# Frequently asked questions

### How do I add a new criterion?

1. **Built-in**: Edit `judge.py` and add a new entry to the `CRITERIA` list with `id`, `criterion`, `scoring_guide`, and optional `considerations`. Use the same JSON response shape (`score`, `rationale`, `critical_failures`, `positive_behaviors`).
2. **From file**: Create a JSON file with `id`, `criterion`, `scoring_guide`, and optional `considerations`. Run with `--criterion-file path/to/criterion.json`. See `personas/example_criterion.json`.
3. **From directory**: Put one criterion JSON per file in a directory and use `--criteria-dir path/to/criteria`.

Then run with `--criteria id1,id2,...` to select which criteria to run, or omit to run all (including the new one).

---

### Can I use a different judge model?

Yes. Override the judge model with **`--judge-model MODEL`** (e.g. `--judge-model claude-3-5-sonnet-20241022`) or set **`JUDGE_MODEL`** in `.env`. The default is `claude-sonnet-4-6`.

To use **OpenAI as the judge**, pass **`--judge openai`** and set **`OPENAI_API_KEY`**. Override the model with **`--judge-model gpt-4o`** or **`JUDGE_MODEL_OPENAI`** in `.env`. See README “Judge model” and RUNBOOK.

---

### Why do scores vary between runs?

The judge is an LLM, so outputs can vary slightly. To reduce variability:

- Use **`--judge-temperature 0`** (the default) or set `judge_temperature: 0` in `safety-tester-config.json`.
- Use **`--compare-baseline`** and **`--save-baseline`** to track regressions instead of absolute scores.
- Use **`--report-only results/`** to re-score the same conversations with a new criterion or temperature without re-running the SUT.

See [RUNBOOK — Troubleshooting: Inconsistent judge scores](RUNBOOK.md#troubleshooting).

---

### How do I run only crisis personas?

1. Tag personas in **`personas/persona_tags.json`** (e.g. `"passive_ideation.json": ["crisis"]`).
2. Run with **`--personas-dir personas --persona-tags crisis`** (or use **`--config`** with a config that lists only crisis personas and add **`--persona-tags crisis`**).

List which personas have which tags: **`python3 main.py --list-tags`**.

---

### How do I run the tool without using the API (no charges)?

Runs are **mock by default**. Do not pass `--live` and the tool will use canned responses and mock judge scores. No API key is required. Use this for development, CI, and the scheduled workflow. Pass **`--live`** only when you want to hit the real API.

---

### Where are results saved?

By default, result JSON files go in **`results/`**. Override with **`--output-dir PATH`** or **`OUTPUT_DIR`** in `.env`. Batch summaries (when using **`--batch-summary`**) are written to the same directory as `batch_summary_TIMESTAMP.json` and optionally `.md`, `.csv`, and `batch_audit_*.json`.

---

### How do I re-score existing runs without calling the SUT again?

Use **`--report-only PATH`** where `PATH` is a single result JSON file or a directory of result JSONs. The tool loads each file’s conversation, re-runs the judge with the current criteria (and `--judge-temperature`), and overwrites the file with new scores. Use this after adding a new criterion or changing judge temperature. Use **`--live`** if you want the real judge API; otherwise it uses mock judge.

---

### Can I cache SUT responses to save time or cost?

Yes. Use **`--cache-dir PATH`** (or **`CACHE_DIR`** in `.env`). The tool caches SUT responses by a hash of (persona path + system prompt). The next run with the same persona and prompt will reuse the cached conversation and only re-run the judge. Useful for re-judging with new criteria or after changing judge temperature.

---

### How do I get a JUnit report for CI?

Run with **`--batch-summary --junit report.xml`** (and e.g. **`--config personas/batch_config.json`**). The XML file can be published with an action like `EnricoMi/publish-unit-test-result-action`. See **`examples/junit-github-actions.yml`**.

---

### Where is the full list of CLI flags?

See **[docs/CLI_REFERENCE.md](CLI_REFERENCE.md)** for a one-line description of every flag and the main environment variables.
