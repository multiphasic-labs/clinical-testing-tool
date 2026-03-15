#!/usr/bin/env python3
"""
Generate results/index.html listing recent result files and batch summaries with links.
Run from project root: python3 scripts/generate_results_index.py [--output-dir results]
Opens as file:// or serve the results dir with any static server.
"""
import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate results/index.html")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Results directory to scan (default: results)",
    )
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()
    if not out_dir.is_dir():
        print(f"Not a directory: {out_dir}")
        return
    index_path = out_dir / "index.html"

    # Single-run result JSONs: TIMESTAMP_persona.json or TIMESTAMP_persona_label.json
    single_pattern = re.compile(r"^(\d{8}T\d{6}Z)_(.+?)\.json$")
    single_runs: list[dict] = []
    batch_summaries: list[dict] = []
    batch_audits: list[dict] = []

    for f in out_dir.iterdir():
        if not f.is_file():
            continue
        name = f.name
        # Skip index and non-result files
        if name == "index.html" or name.startswith("baseline_"):
            continue
        if name.startswith("batch_summary_") and name.endswith(".json"):
            ts = name.replace("batch_summary_", "").replace(".json", "")
            batch_summaries.append({"timestamp": ts, "base": name.replace(".json", "")})
            continue
        if name.startswith("batch_summary_") and (name.endswith(".md") or name.endswith(".csv")):
            continue  # covered by .json entry
        if name.startswith("batch_audit_") and name.endswith(".json"):
            ts = name.replace("batch_audit_", "").replace(".json", "")
            batch_audits.append({"timestamp": ts, "name": name})
            continue
        m = single_pattern.match(name)
        if m:
            ts, rest = m.group(1), m.group(2)
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                persona = data.get("persona_name", rest)
                score = data.get("final_score")
                error = data.get("error")  # not in normal result; for failed runs
            except Exception:
                persona = rest
                score = None
                error = None
            html_name = name.replace(".json", ".html")
            has_html = (out_dir / html_name).is_file()
            single_runs.append({
                "timestamp": ts,
                "persona": persona,
                "json": name,
                "html": html_name if has_html else None,
                "score": score,
                "error": error,
            })

    # Sort: newest first
    single_runs.sort(key=lambda x: x["timestamp"], reverse=True)
    batch_summaries.sort(key=lambda x: x["timestamp"], reverse=True)
    batch_audits.sort(key=lambda x: x["timestamp"], reverse=True)

    def row_score(score, error) -> str:
        if error:
            return '<span class="fail">error</span>'
        if score is not None:
            if int(score) >= 2:
                return f'<span class="pass">{score}</span>'
            if int(score) == 1:
                return f'<span class="warn">{score}</span>'
            return f'<span class="fail">{score}</span>'
        return "—"

    rows = []
    for r in single_runs:
        score_cell = row_score(r["score"], r.get("error"))
        links = f'<a href="{r["json"]}">JSON</a>'
        if r.get("html"):
            links += f' | <a href="{r["html"]}">Report</a>'
        rows.append(f"<tr><td>{r['timestamp']}</td><td>{r['persona']}</td><td>{score_cell}</td><td>{links}</td></tr>")

    batch_rows = []
    for b in batch_summaries:
        base = b["base"]
        links = []
        for ext in [".json", ".md", ".csv"]:
            if (out_dir / (base + ext)).is_file():
                links.append(f'<a href="{base + ext}">{ext[1:]}</a>')
        batch_rows.append(f"<tr><td>{b['timestamp']}</td><td>{' | '.join(links)}</td></tr>")

    audit_rows = []
    for a in batch_audits:
        audit_rows.append(f"<tr><td>{a['timestamp']}</td><td><a href=\"{a['name']}\">Audit JSON</a></td></tr>")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Results index — Mental Health Safety Tester</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 1rem 2rem; background: #1a1a1a; color: #e0e0e0; }
  h1 { font-size: 1.25rem; margin-bottom: 0.5rem; }
  h2 { font-size: 1rem; margin-top: 1.5rem; margin-bottom: 0.5rem; color: #a0a0a0; }
  table { border-collapse: collapse; width: 100%; max-width: 56rem; }
  th, td { text-align: left; padding: 0.35rem 0.75rem; border-bottom: 1px solid #333; }
  th { color: #888; font-weight: 600; }
  a { color: #6ab7ff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .pass { color: #6bcf7b; }
  .warn { color: #e6b84a; }
  .fail { color: #e06c75; }
  p.meta { color: #666; font-size: 0.875rem; margin-top: 0.25rem; }
</style>
</head>
<body>
<h1>Results index</h1>
<p class="meta">Mental Health Safety Tester — single runs and batch summaries. Open JSON for data; Report for HTML view when available.</p>
"""
    if rows:
        html += """
<h2>Single runs</h2>
<table>
<thead><tr><th>Timestamp (UTC)</th><th>Persona</th><th>Score</th><th>Links</th></tr></thead>
<tbody>
"""
        html += "\n".join(rows)
        html += "\n</tbody>\n</table>\n"
    if batch_rows:
        html += """
<h2>Batch summaries</h2>
<table>
<thead><tr><th>Timestamp (UTC)</th><th>Links</th></tr></thead>
<tbody>
"""
        html += "\n".join(batch_rows)
        html += "\n</tbody>\n</table>\n"
    if audit_rows:
        html += """
<h2>Batch audits</h2>
<table>
<thead><tr><th>Timestamp (UTC)</th><th>Links</th></tr></thead>
<tbody>
"""
        html += "\n".join(audit_rows)
        html += "\n</tbody>\n</table>\n"

    html += "\n</body>\n</html>"
    index_path.write_text(html, encoding="utf-8")

    # Stable "latest" link: redirect to most recent run's HTML report, or index if none
    latest_path = out_dir / "latest.html"
    latest_target = None
    for r in single_runs:
        if r.get("html") and (out_dir / r["html"]).is_file():
            latest_target = r["html"]
            break
    if latest_target:
        latest_path.write_text(
            f'<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={latest_target}"><title>Latest run</title></head><body><p>Redirecting to <a href="{latest_target}">latest report</a>...</p></body></html>',
            encoding="utf-8",
        )
    else:
        latest_path.write_text(
            '<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=index.html"><title>Latest</title></head><body><p>No single-run HTML reports. Redirecting to <a href="index.html">results index</a>...</p></body></html>',
            encoding="utf-8",
        )

    print(f"Wrote {index_path} ({len(single_runs)} runs, {len(batch_summaries)} batch summaries, {len(batch_audits)} audits); latest.html -> {latest_target or 'index.html'}")


if __name__ == "__main__":
    main()
