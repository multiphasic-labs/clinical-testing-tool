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

4. **Run it locally**:

   ```bash
   cd mental-health-tester
   python main.py --persona personas/anxiety_checkin.json --verbose
   ```

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

Mock mode is designed so you can iterate on UX and plumbing without consuming API credits.

- Enable mock mode via CLI:

  ```bash
  python main.py --persona passive_ideation.json --mock --verbose
  ```

- Or via env:

  ```bash
  export SAFETY_TESTER_MOCK=1
  python main.py --persona passive_ideation.json --verbose
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

