#!/usr/bin/env python3
"""
Lint persona JSON files for template hygiene ({{placeholders}} vs meta.variables).

Exit code: 0 if no issues, 1 if any file has issues.

Usage:
  python scripts/lint_persona_templates.py [PERSONAS_DIR]
  python scripts/lint_persona_templates.py --strict [PERSONAS_DIR]

Default PERSONAS_DIR is ./personas relative to the mental-health-tester package.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Package root (parent of scripts/)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runner import lint_persona_template_file  # noqa: E402

_NON_PERSONA_JSON = {
    "batch_config.json",
    "example_criterion.json",
    "persona_tags.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint persona templates for meta.variables coverage.")
    parser.add_argument(
        "personas_dir",
        nargs="?",
        default=str(ROOT / "personas"),
        help="Directory of persona JSON files (default: ./personas)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require every {{placeholder}} name to appear as a key in meta.variables.",
    )
    parser.add_argument(
        "--include-examples",
        action="store_true",
        help="Also lint example_parameterized_persona.json (normally excluded from discovery).",
    )
    args = parser.parse_args()
    d = Path(args.personas_dir)
    if not d.is_dir():
        print(f"Not a directory: {d}", file=sys.stderr)
        return 1
    files = sorted(p for p in d.glob("*.json") if p.name not in _NON_PERSONA_JSON)
    if args.include_examples:
        ex = d / "example_parameterized_persona.json"
        if ex.is_file() and ex not in files:
            files.append(ex)
            files.sort(key=lambda p: p.name)
    all_errors: list[str] = []
    for path in files:
        issues = lint_persona_template_file(path, strict=args.strict)
        all_errors.extend(issues)
        if issues:
            for line in issues:
                print(line, file=sys.stderr)
        else:
            # Only print OK if we might have placeholders (optional quiet mode — print all OK)
            pass
    if all_errors:
        print(f"\nlint_persona_templates: {len(all_errors)} issue(s)", file=sys.stderr)
        return 1
    print(f"lint_persona_templates: OK ({len(files)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
