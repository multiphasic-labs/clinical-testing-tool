# Parameterized personas — authoring guide

This doc complements [PERSONA_SCHEMA.md](PERSONA_SCHEMA.md) with **copy-paste examples** and **CI lint policy**.

## Merge order (who wins)

| Priority | Source |
|----------|--------|
| 1 | `meta.variables` in the persona JSON |
| 2 | `variables` on a batch config object entry |
| 3 | `--persona-vars-file` (JSON object) |
| 4 | `--persona-var KEY=VALUE` (repeatable; last wins per key) |

## Example 1 — Single run (CLI)

```bash
cd mental-health-tester
export SAFETY_TESTER_MOCK=1   # optional: no API calls

python3 main.py \
  --persona personas/example_parameterized_persona.json \
  --persona-var topic=caregiving_burnout \
  --persona-var support_person=my_sister \
  --mock --quiet
```

## Example 2 — Batch directory + override

```bash
python3 main.py \
  --personas-dir ./personas \
  --persona-var topic=work_stress \
  --mock --batch-summary
```

(`--personas-dir` resolves bare filenames like `foo.json` against that directory.)

## Example 3 — `batch_config.json` object entry

```json
{
  "personas": [
    "passive_ideation.json",
    {
      "persona": "example_parameterized_persona.json",
      "variables": {
        "topic": "exam_season",
        "support_person": "my_roommate"
      },
      "id": "variant_exams"
    }
  ]
}
```

```bash
python3 main.py --config path/to/batch_config.json --mock --batch-summary
```

## Example 4 — Dry run (see every execution row)

Multi-prompt mode lists **prompt × persona** combinations:

```bash
python3 main.py \
  --personas-dir ./personas \
  --sut-prompts ./prompts/a.txt,./prompts/b.txt \
  --dry-run --mock
```

## Lint policy (`scripts/lint_persona_templates.py`)

| Mode | Meaning | When to use |
|------|---------|-------------|
| **Default** | If the file uses any `{{placeholder}}`, **`meta.variables` must exist** (can be `{}` if you only ever supply values via batch/CLI). | Routine CI; catches “forgot to add `meta.variables`”. |
| **`--strict`** | Every placeholder name found in text must appear as a **key** in `meta.variables`. | Stricter repos that want **defaults in-repo** for every variable. |

**Examples:**

```bash
# Default (recommended for most PRs)
python3 scripts/lint_persona_templates.py

# Stricter gate (e.g. release branch or `main`)
python3 scripts/lint_persona_templates.py --strict

# Also lint the shipped example template
python3 scripts/lint_persona_templates.py --include-examples
```

Validation without running tests:

```bash
python3 main.py --validate-personas
python3 main.py --validate-personas --include-example-personas
```

## List template personas only

```bash
python3 main.py --list-personas --templates
```

Uses the same `--personas-dir` as other commands (default: `personas/`). Includes `example_parameterized_persona.json` (normally excluded from discovery).

## JSON Schema (`schemas/persona.json`)

Structural check for raw persona JSON (array of turns vs `{ "meta", "turns" }`). Run with:

```bash
python3 main.py --validate-personas --validate-schema
```

Requires `jsonschema` (listed in `requirements.txt`). Runs **before** full load/substitution checks.

## Retry

Batch summaries store `persona_source_file`, `persona_variables`, and optional `persona_instance_id`. Use `--retry-failed` to re-run failed rows with the same template + values (CLI vars can still be merged on top).
