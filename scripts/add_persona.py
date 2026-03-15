#!/usr/bin/env python3
"""
Helper to add a new persona: prompts for name, turns (message + expected_behavior), and optional tags,
then writes personas/{name}.json and optionally updates personas/persona_tags.json.
Usage: python3 scripts/add_persona.py   (interactive)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = ROOT / "personas"
TAGS_FILE = PERSONAS_DIR / "persona_tags.json"


def main() -> None:
    print("Add a new persona (JSON + optional tags).\n")
    name = input("Persona filename (e.g. my_persona.json): ").strip()
    if not name:
        print("No name given.")
        sys.exit(1)
    if not name.endswith(".json"):
        name += ".json"
    path = PERSONAS_DIR / name
    if path.exists():
        print(f"File already exists: {path}")
        sys.exit(1)
    try:
        n_turns = int(input("Number of turns (1–10): ").strip() or "2")
    except ValueError:
        n_turns = 2
    n_turns = max(1, min(10, n_turns))
    turns = []
    for i in range(1, n_turns + 1):
        print(f"\n--- Turn {i} ---")
        message = input(f"  User message: ").strip()
        expected = input(f"  Expected behavior (what a good response looks like): ").strip()
        turns.append({
            "turn": i,
            "message": message or f"(Turn {i} message)",
            "expected_behavior": expected or f"(Expected behavior for turn {i})",
        })
    PERSONAS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(turns, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {path}")
    tags_input = input("\nTags (comma-separated, e.g. crisis,support; or leave blank): ").strip()
    if tags_input:
        tag_list = [t.strip() for t in tags_input.split(",") if t.strip()]
        if tag_list:
            tag_map = {}
            if TAGS_FILE.is_file():
                try:
                    tag_map = json.loads(TAGS_FILE.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
            if not isinstance(tag_map, dict):
                tag_map = {}
            tag_map[name] = tag_list
            TAGS_FILE.write_text(json.dumps(tag_map, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Updated {TAGS_FILE} with tags: {tag_list}")
    print("\nDone. Run with: python3 main.py --persona " + name)


if __name__ == "__main__":
    main()
