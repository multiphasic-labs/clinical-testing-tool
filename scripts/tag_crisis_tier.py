#!/usr/bin/env python3
"""
Migrate all personas in personas/ to object format with a crisis_tier meta field.

crisis_tier: true  — persona involves explicit suicidal ideation or self-harm
crisis_tier: false — persona involves mental health distress but no explicit ideation

Detection heuristics (conservative — when in doubt, mark true):
- Explicit mentions of suicide, suicidal thoughts, self-harm, or wanting to die
  in ANY turn's message or expected_behavior field
- References to methods, plans, or intent to harm self

Usage:
    python scripts/tag_crisis_tier.py [--personas-dir personas/] [--dry-run] [--force]

Flags:
    --personas-dir  Path to personas directory (default: personas/ relative to script)
    --dry-run       Print what would change without writing files
    --force         Re-tag personas that already have crisis_tier set (default: skip)
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Patterns that indicate explicit suicidal ideation or self-harm
CRISIS_PATTERNS = [
    r"\bsuicid(e|al|ally)\b",
    r"\bself.harm\b",
    r"\bself.injur\w*\b",
    r"\bwant(ing)? to die\b",
    r"\bend (my|their|his|her) life\b",
    r"\bkill (my|them|him|her)self\b",
    r"\bno longer want(ing)? to (be here|live|exist)\b",
    r"\bstep(ping)? out into traffic\b",
    r"\boverdos(e|ing)\b",
    r"\bcut(ting)? (my|them|him|her)self\b",
    r"\bhurt(ing)? (my|them|him|her)self\b",
    r"\b(thoughts?|ideation) of (death|dying|suicide)\b",
    r"\bbetter off (if I|without me|dead)\b",
    r"\bsafety (assessment|plan|concern|risk)\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in CRISIS_PATTERNS]


def _is_crisis(turns: list) -> bool:
    for turn in turns:
        text = " ".join([
            str(turn.get("message", "")),
            str(turn.get("expected_behavior", "")),
        ])
        for pat in _COMPILED:
            if pat.search(text):
                return True
    return False


def _read_persona(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"meta": {}, "turns": data, "_was_bare_array": True}
    if isinstance(data, dict) and "turns" in data:
        result = dict(data)
        if "meta" not in result:
            result["meta"] = {}
        result["_was_bare_array"] = False
        return result
    raise ValueError(f"Unexpected persona format in {path}: root must be list or object with 'turns'")


def _write_persona(path: Path, data: dict) -> None:
    was_bare_array = data.pop("_was_bare_array", False)
    output = {
        "meta": data["meta"],
        "turns": data["turns"],
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--personas-dir",
        type=Path,
        default=None,
        help="Path to personas directory (default: personas/ relative to repo root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes without writing files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-tag personas that already have crisis_tier set",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    personas_dir = args.personas_dir or (repo_root / "personas")

    if not personas_dir.is_dir():
        print(f"ERROR: not a directory: {personas_dir}", file=sys.stderr)
        return 1

    paths = sorted(personas_dir.glob("*.json"))
    if not paths:
        print(f"No JSON files found in {personas_dir}", file=sys.stderr)
        return 1

    tagged = 0
    skipped = 0
    errors = 0

    for path in paths:
        try:
            data = _read_persona(path)
        except json.JSONDecodeError as e:
            print(f"  ERROR {path.name}: invalid JSON: {e}")
            errors += 1
            continue
        except ValueError:
            # Not a persona file (e.g. batch_config.json, persona_tags.json)
            skipped += 1
            continue

        if not args.force and "crisis_tier" in data["meta"]:
            skipped += 1
            continue

        crisis = _is_crisis(data["turns"])
        data["meta"]["crisis_tier"] = crisis

        label = "crisis" if crisis else "non-crisis"
        if args.dry_run:
            print(f"  [dry-run] {path.name}: crisis_tier={crisis} ({label})")
        else:
            _write_persona(path, data)
            print(f"  {path.name}: crisis_tier={crisis} ({label})")
        tagged += 1

    print(f"\nDone: {tagged} tagged, {skipped} skipped (already tagged), {errors} errors")
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
