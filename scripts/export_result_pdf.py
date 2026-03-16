#!/usr/bin/env python3
"""
Export a single result JSON or batch report HTML to PDF.
Usage:
  python3 scripts/export_result_pdf.py --result results/20260315T120000Z_passive_ideation.json --out report.pdf
  python3 scripts/export_result_pdf.py --html results/batch_report_20260315T120000Z.html --out batch.pdf
Without a PDF library, writes an HTML file that you can open and print to PDF.
With weasyprint installed (pip install weasyprint), writes a real PDF.
"""
import argparse
import json
from pathlib import Path


def result_to_html(data: dict) -> str:
    """Turn a result JSON into a simple HTML report."""
    persona = data.get("persona_name", "?")
    ts = data.get("timestamp_utc", "")
    score = data.get("final_score", "?")
    cs = data.get("criterion_scores") or {}
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in sorted(cs.items()))
    conv = data.get("conversation") or {}
    turns = conv.get("turns") or []
    turn_rows = ""
    for t in turns:
        user = (t.get("user_message") or "").replace("<", "&lt;").replace(">", "&gt;")
        sys_ = (t.get("system_response") or "").replace("<", "&lt;").replace(">", "&gt;")
        turn_rows += f"<tr><td>User</td><td>{user}</td></tr><tr><td>System</td><td>{sys_}</td></tr>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Safety result — {persona}</title>
<style>body {{ font-family: sans-serif; margin: 1em; }} table {{ border-collapse: collapse; }} th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; }}</style></head>
<body>
<h1>Safety test result</h1>
<p><strong>Persona:</strong> {persona} &nbsp; <strong>Timestamp:</strong> {ts} &nbsp; <strong>Final score:</strong> {score}</p>
<h2>Criterion scores</h2>
<table><tr><th>Criterion</th><th>Score</th></tr>{rows}</table>
<h2>Conversation</h2>
<table><tr><th>Role</th><th>Message</th></tr>{turn_rows}</table>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Export result JSON or batch HTML to PDF (or HTML for print-to-PDF)")
    parser.add_argument("--result", type=Path, help="Path to a result JSON file")
    parser.add_argument("--html", type=Path, help="Path to batch_report_*.html (copy as-is for PDF)")
    parser.add_argument("--out", type=Path, required=True, help="Output path (.pdf or .html)")
    args = parser.parse_args()
    if not args.result and not args.html:
        print("Specify --result or --html")
        return 1
    if args.result and args.html:
        print("Specify only one of --result or --html")
        return 1

    out_path = args.out.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.html:
        if not args.html.is_file():
            print(f"Not found: {args.html}")
            return 1
        html_content = args.html.read_text(encoding="utf-8")
    else:
        if not args.result.is_file():
            print(f"Not found: {args.result}")
            return 1
        data = json.loads(args.result.read_text(encoding="utf-8"))
        html_content = result_to_html(data)

    is_pdf = out_path.suffix.lower() == ".pdf"
    if is_pdf:
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(out_path)
            print(f"Wrote PDF: {out_path}")
        except ImportError:
            html_out = out_path.with_suffix(".html")
            html_out.write_text(html_content, encoding="utf-8")
            print(f"weasyprint not installed. Wrote HTML: {html_out} — open and print to PDF.")
            return 0
    else:
        out_path.write_text(html_content, encoding="utf-8")
        print(f"Wrote HTML: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
