# Changelog

All notable changes to **Mental Health Safety Tester** are documented here.

## [Unreleased]

### Added

- **Parameterized personas**: `{{variable_name}}` placeholders in `message` / `expected_behavior`, with defaults in `meta.variables`, per-batch `variables` in `batch_config.json`, and CLI `--persona-vars-file` / `--persona-var`.
- **Display names** for runs: `stem`, `stem__id`, or `stem__key=value_...`.
- **SUT cache** keys include template variables (and optional instance id).
- **Batch summary / audit / CSV / JUnit**: `persona_source_file`, `persona_variables`, `persona_instance_id` where applicable; CSV columns `persona_variables_json`, etc.
- **`--dry-run`**: prints each planned run with **resolved variables** (file → id → vars → display name).
- **`--validate-personas --include-example-personas`**: validates template examples excluded from discovery (e.g. `example_parameterized_persona.json`).
- **Literal braces**: in JSON strings, use `\\{{` and `\\}}` for literal `{{` / `}}` (see `docs/PERSONA_SCHEMA.md`).
- **`scripts/lint_persona_templates.py`**: optional CI lint for `meta.variables` when placeholders exist (`--strict` for full key coverage).
- **Saved result JSON** (`save_result_json`): includes `persona_source_file`, `persona_variables`, `persona_instance_id` when applicable.

### Fixed

- **`--personas-dir`**: bare filenames (e.g. `foo.json`) now resolve against the directory passed to `--personas-dir`, not only `personas/`.

### Documentation

- `docs/PERSONA_SCHEMA.md`: placeholders, merge order, escape rules, batch object shape, retry fields.
- `docs/PARAMETERIZED_PERSONAS.md`: copy-paste examples and **lint policy** (default vs `--strict`).
- README: parameterized personas overview and merge-order table.

### Tooling

- **CI** (`.github/workflows/ci.yml`): runs `pytest`, smoke script, `lint_persona_templates.py`, `--validate-personas --include-example-personas --validate-schema`, and a mock batch config run (repo root = package).
- **Scheduled workflow** (`scheduled.yml`): aligned with the same repo layout (no nested `cd`).
- **`--list-personas --templates`**: list only files with `{{placeholder}}` syntax; includes `example_parameterized_persona.json`.
- **`--validate-schema`**: validate raw JSON against `schemas/persona.json` (requires `jsonschema`).
- **Batch HTML report**: columns for source file, template variables JSON, and instance id when present.

### Tests

- **Golden-shape** test for saved result JSON keys on a parameterized mock run (`tests/test_golden_parameterized_result.py`).
