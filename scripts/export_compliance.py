#!/usr/bin/env python3
"""
Export a compliance bundle (zip) for a run: result JSONs, batch summary, audit, methodology doc.
Run from project root: python3 scripts/export_compliance.py --last --out compliance_bundle.zip
Or: python3 scripts/export_compliance.py --run-id 20260315T120000_abc123 --out bundle.zip
"""
import argparse
import json
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compliance bundle (zip) for a run")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Results directory (default: results)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run-id", type=str, metavar="ID", help="Run ID to export (e.g. from batch_summary)")
    group.add_argument("--last", action="store_true", help="Use run_id from most recent batch summary")
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        metavar="ZIP",
        help="Output zip path",
    )
    parser.add_argument(
        "--no-methodology",
        action="store_true",
        help="Do not include docs/METHODOLOGY.md in the bundle",
    )
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()
    if not out_dir.is_dir():
        print(f"Not a directory: {out_dir}")
        return 1

    run_id = args.run_id
    if args.last:
        batch_files = sorted(out_dir.glob("batch_summary_*.json"), key=lambda p: p.name, reverse=True)
        if not batch_files:
            print("No batch summary found; cannot use --last.")
            return 1
        try:
            data = json.loads(batch_files[0].read_text(encoding="utf-8"))
            run_id = data.get("run_id")
        except (json.JSONDecodeError, OSError):
            pass
        if not run_id:
            print("Latest batch summary has no run_id; specify --run-id explicitly.")
            return 1
        print(f"Using run_id from latest batch: {run_id}")

    to_add: list[tuple[Path, str]] = []  # (source path, arcname in zip)
    # Result JSONs with this run_id
    for f in out_dir.glob("*.json"):
        if f.name.startswith("batch_"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("run_id") == run_id:
                to_add.append((f, f"results/{f.name}"))
        except (json.JSONDecodeError, OSError):
            continue
    # Batch summary (json + same-base .md and .csv) and audit with this run_id
    batch_ts = None
    for b in out_dir.glob("batch_summary_*.json"):
        try:
            data = json.loads(b.read_text(encoding="utf-8"))
            if data.get("run_id") == run_id:
                base = b.stem  # batch_summary_TIMESTAMP
                batch_ts = base.replace("batch_summary_", "")
                to_add.append((b, f"results/{b.name}"))
                for ext in [".md", ".csv"]:
                    other = out_dir / (base + ext)
                    if other.is_file():
                        to_add.append((other, f"results/{other.name}"))
                break
        except (json.JSONDecodeError, OSError):
            continue
    for a in out_dir.glob("batch_audit_*.json"):
        try:
            data = json.loads(a.read_text(encoding="utf-8"))
            if data.get("run_id") == run_id:
                to_add.append((a, f"results/{a.name}"))
                break
        except (json.JSONDecodeError, OSError):
            continue
    if batch_ts:
        batch_report = out_dir / f"batch_report_{batch_ts}.html"
        if batch_report.is_file():
            to_add.append((batch_report, f"results/{batch_report.name}"))
    # Methodology doc
    if not args.no_methodology:
        project_root = Path(__file__).resolve().parents[1]
        methodology = project_root / "docs" / "METHODOLOGY.md"
        if methodology.is_file():
            to_add.append((methodology, "docs/METHODOLOGY.md"))

    if not to_add:
        print("No files found for this run_id.")
        return 1

    zip_path = args.out.resolve()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLated) as zf:
        for src, arcname in to_add:
            zf.write(src, arcname)
    print(f"Wrote {zip_path} ({len(to_add)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
