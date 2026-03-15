#!/usr/bin/env python3
"""
Read a JSONL history file (from --history) and print a simple table or trend.
Usage: python3 scripts/show_history.py [path/to/history.jsonl]
        Default: results/run_history.jsonl
"""
import json
import sys
from pathlib import Path

def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path(__file__).resolve().parent.parent / "results" / "run_history.jsonl"
    if not path.is_file():
        print(f"No history file at {path}. Run the tester with --history {path} to create one.")
        sys.exit(1)
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not records:
        print("No records in history.")
        return
    # Simple table: timestamp, persona, run_label?, score, error?
    print(f"{'timestamp_utc':<22} {'persona':<25} {'run_label':<15} {'score':<6} {'error'}")
    print("-" * 90)
    for r in records:
        ts = r.get("timestamp_utc", "")
        persona = (r.get("persona_name") or "")[:24]
        label = (r.get("run_label") or "")[:14]
        score = r.get("score", "")
        err = (r.get("error") or "")[:30]
        print(f"{ts:<22} {persona:<25} {label:<15} {score!s:<6} {err}")
    print(f"\nTotal runs: {len(records)}")

if __name__ == "__main__":
    main()
