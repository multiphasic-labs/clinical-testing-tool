# Example outputs

These files show the shape of result and batch summary JSON for demos and documentation. They are minimal examples (mock-style); real runs include full conversation transcripts and judge rationales.

- **`example_result.json`** — One single-run result (one persona). See `results/*.json` for full outputs.
- **`example_batch_summary.json`** — One batch summary. See `results/batch_summary_*.json` for full outputs.

- **`junit-github-actions.yml`** — Example GitHub Actions workflow that runs the tester and publishes JUnit XML so results appear in the Actions "Tests" tab. Copy into `.github/workflows/` or merge into your CI.

Generate real results with:

```bash
python3 main.py --persona passive_ideation.json --quiet
python3 main.py --config personas/batch_config.json --batch-summary --quiet
```
