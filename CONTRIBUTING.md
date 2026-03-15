## Contributing to Mental Health Safety Tester

Thanks for your interest in contributing. This tool is meant for **offline testing of AI systems**, not for clinical use. Please keep that in mind as you propose changes or add content.

### Ground rules

- Do not add real patient data, PHI/PII, or case notes.
- Do not frame this tool as a clinical decision aid or suicide risk assessment in documentation or examples.
- Keep personas clearly synthetic and anonymized.

---

## Adding a new persona

1. **Create a JSON file** in `personas/`, for example: `personas/anxiety_checkin.json`.
2. The file should be a JSON array of turns, where each turn is an object like:

   ```json
   {
     "turn": 1,
     "message": "Example user message",
     "expected_behavior": "High-level description of what a safe, supportive response should look like."
   }
   ```

   Recommendations:

   - Use 3–6 turns to keep runs cheap and interpretable.
   - Make the `expected_behavior` concrete enough that human reviewers can see what “good” looks like.

3. **Add the persona to a batch config** (optional but recommended):

   - Edit `personas/batch_config.json` or create a new config file:

     ```json
     {
       "personas": [
         "passive_ideation.json",
         "active_ideation.json",
         "anxiety_checkin.json"
       ]
     }
     ```

4. **Optionally tag the persona** for filtered runs: add an entry to `personas/persona_tags.json`, e.g. `"anxiety_checkin.json": ["boundary"]`. Use tags like `crisis`, `boundary`, `support`. Then run only that tag: `python3 main.py --personas-dir personas --persona-tags boundary`.

5. **Run it locally** (default is mock—no API key or charges):

   ```bash
   cd mental-health-tester
   python3 main.py --persona anxiety_checkin.json --verbose
   ```

   To use the real API, pass **`--live`** (requires `ANTHROPIC_API_KEY` in `.env`):

   ```bash
   python3 main.py --persona anxiety_checkin.json --live --verbose
   ```

---

## Default: mock mode; use `--live` for real API

- **Runs are in mock mode by default**—no API calls, no key required, no charges. Ideal for development and CI.
- To hit the real Anthropic (and judge) API, pass **`--live`** on the command line. Make sure `ANTHROPIC_API_KEY` is set in `.env`.
- You can force mock even when scripting: use `--mock` or set `SAFETY_TESTER_MOCK=1` in the environment.

---

## Modifying the judge / criteria

The current judge logic and scoring prompt live in `judge.py`.

- To **change the criterion or rubric**:
  - Update the `CRITERION` string and the `SCORING_GUIDE` text.
  - Keep the JSON response format the same (`score`, `rationale`, `critical_failures`, `positive_behaviors`) so the rest of the pipeline keeps working.

- To **add multiple criteria**:
  - You can add new functions in `judge.py` that:
    - Build a new prompt.
    - Call the judge model.
    - Return an additional JSON object.
  - Extend `main.py` to call them and merge results into the saved JSON.

When changing prompts, keep instructions explicit about:

- Requiring valid JSON only (no extra commentary).
- The allowed `score` values and their meaning.

---

## Running in mock mode during development

Mock mode is the **default**—no flags needed. Use it to iterate on UX and plumbing without consuming API credits.

- Default (mock):

  ```bash
  python3 main.py --persona passive_ideation.json --verbose
  ```

- To force mock in scripts or CI:

  ```bash
  export SAFETY_TESTER_MOCK=1
  python3 main.py --persona passive_ideation.json
  ```

- To use the real API:

  ```bash
  python3 main.py --persona passive_ideation.json --live --verbose
  ```

In mock mode:

- The system-under-test responses are canned strings that reference `expected_behavior`.
- The judge always returns a score of `2` with a mock rationale.

---

## Tests and CI

- Tests live in `tests/`.
- To run tests locally:

  ```bash
  cd mental-health-tester
  python -m pip install pytest
  SAFETY_TESTER_MOCK=1 pytest
  ```

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs tests in mock mode by default, so no Anthropic API key or credit is required for CI.

---

## Code style

- Prefer clear, explicit error messages (especially around API keys and billing).
- Use type hints for new functions where practical.
- Avoid adding comments that only restate what the code already makes obvious; use comments for non-obvious intent or design decisions.

