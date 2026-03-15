#!/usr/bin/env python3
"""
Read last N batch_summary_*.json files and show pass/fail trend (stdout table or --html PATH).
Run from project root: python3 scripts/trend_batch_summaries.py [--output-dir results] [--last N] [--html trend.html]
"""
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Trend pass/fail over last N batch summaries")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Results directory (default: results)",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=10,
        metavar="N",
        help="Number of batch summaries to include (default: 10)",
    )
    parser.add_argument(
        "--html",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write trend table to this HTML file",
    )
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()
    if not out_dir.is_dir():
        print(f"Not a directory: {out_dir}")
        return

    batch_files = sorted(out_dir.glob("batch_summary_*.json"), key=lambda p: p.name, reverse=True)
    batch_files = batch_files[: args.last]
    rows = []
    for b in batch_files:
        try:
            data = json.loads(b.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        ts = data.get("timestamp_utc", b.stem.replace("batch_summary_", ""))
        runs = data.get("runs", [])
        n = len(runs)
        errors = sum(1 for r in runs if r.get("error"))
        # Passed = no error and score >= 2 (or we don't have fail_under, so use 2 as default)
        passed = sum(1 for r in runs if not r.get("error") and (r.get("score") is not None and int(r.get("score", 0)) >= 2))
        failed = n - passed
        run_id = data.get("run_id", "")
        rows.append({"timestamp": ts, "run_id": run_id, "total": n, "passed": passed, "failed": failed, "errors": errors})
    if not rows:
        print("No batch summaries found.")
        if args.html:
            args.html.write_text("<p>No batch summaries found.</p>", encoding="utf-8")
        return

    # Print table to stdout
    print(f"{'Timestamp (UTC)':<22} {'Run ID':<20} {'Total':>6} {'Passed':>6} {'Failed':>6} {'Errors':>6}")
    print("-" * 72)
    for r in rows:
        print(f"{r['timestamp']:<22} {(r['run_id'] or '')[:18]:<20} {r['total']:>6} {r['passed']:>6} {r['failed']:>6} {r['errors']:>6}")

    if args.html:
        html_path = args.html.resolve()
        lines = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Batch trend</title>",
            "<style>body{font-family:system-ui;margin:1rem 2rem;background:#1a1a1a;color:#e0e0e0}",
            "table{border-collapse:collapse}th,td{text-align:left;padding:0.35rem 0.75rem;border-bottom:1px solid #333}",
            ".pass{color:#6bcf7b}.fail{color:#e06c75}</style></head><body>",
            "<h1>Batch summary trend</h1>",
            "<table><thead><tr><th>Timestamp (UTC)</th><th>Run ID</th><th>Total</th><th>Passed</th><th>Failed</th><th>Errors</th></tr></thead><tbody>",
        ]
        for r in rows:
            lines.append(
                f"<tr><td>{r['timestamp']}</td><td>{r['run_id']}</td><td>{r['total']}</td>"
                f"<td class='pass'>{r['passed']}</td><td class='fail'>{r['failed']}</td><td>{r['errors']}</td></tr>"
            )
        lines.append("</tbody></table></body></html>")
        html_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote {html_path}")


if __name__ == "__main__":
    main()
