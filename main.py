import argparse
import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table
from rich.text import Text

from runner import ConversationError, load_persona, load_persona_metadata, run_conversation
from judge import CRITERIA, get_criteria_specs, score_all_criteria
from sut_backends import get_backend


console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI mental health safety tester: run a persona against a chatbot and score clinical safety."
    )
    parser.add_argument(
        "--persona",
        type=str,
        default="passive_ideation.json",
        help="Persona filename in the personas folder or a full/relative path to a persona JSON file.",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Optional JSON config file with a 'personas' list for batch runs.",
    )
    parser.add_argument(
        "--sut-model",
        type=str,
        default=None,
        help="Override system-under-test model name (default: claude-haiku-4-5-20251001).",
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Override judge model name (default: claude-sonnet-4-6).",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock mode (default). No API calls; uses canned responses. Kept for explicit use and scripts.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use the real Anthropic (and judge) API. Without this, runs are in mock mode and do not use your API key.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print raw judge response JSON before formatted output.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for result JSON (and optional Markdown). Default: results/. Overridden by OUTPUT_DIR env.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print final score(s) and result file path (for CI/scripts).",
    )
    parser.add_argument(
        "--md",
        action="store_true",
        help="Also write a Markdown report alongside the JSON result.",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=None,
        metavar="N",
        help="Exit with code 1 if any run has final score < N (for CI). Default: no threshold.",
    )
    parser.add_argument(
        "--sut-system-prompt",
        type=str,
        default=None,
        help="Path to a file containing the system prompt for the SUT. Overridden by SUT_SYSTEM_PROMPT env (path).",
    )
    parser.add_argument(
        "--criteria",
        type=str,
        default=None,
        help="Comma-separated criterion ids to run (e.g. crisis_urgency,no_diagnosis). Default: all.",
    )
    parser.add_argument(
        "--personas",
        type=str,
        default=None,
        help="Comma-separated persona names to run. With --config: filter to these; without: run these as a batch.",
    )
    parser.add_argument(
        "--personas-dir",
        type=str,
        default=None,
        metavar="PATH",
        help="Run all persona JSON files in this directory (excludes batch_config, example_criterion, persona_tags). Overrides --config persona list when set.",
    )
    parser.add_argument(
        "--persona-tags",
        type=str,
        default=None,
        metavar="TAGS",
        help="Comma-separated tags (e.g. crisis,support). When set, only run personas that have at least one of these tags in personas/persona_tags.json.",
    )
    parser.add_argument(
        "--list-tags",
        action="store_true",
        help="Print tags from persona_tags.json and which personas have each tag; then exit.",
    )
    parser.add_argument(
        "--validate-personas",
        action="store_true",
        help="Load each persona in personas/ (or --personas-dir), validate schema, and exit 0 if all OK.",
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        metavar="PATH",
        help="Append a simple log (timestamp, persona, score, errors) to this file for debugging/auditing.",
    )
    parser.add_argument(
        "--batch-summary",
        action="store_true",
        help="When running multiple personas, write a batch_summary_TIMESTAMP.json (and .md) to the output dir.",
    )
    parser.add_argument(
        "--fail-under-criteria",
        type=str,
        default=None,
        metavar="CID=N,...",
        help="Per-criterion minimum score (e.g. crisis_urgency=2,no_diagnosis=1). Exit 1 if any run is below.",
    )
    parser.add_argument(
        "--compare-baseline",
        action="store_true",
        help="Load baseline result for each persona and exit 1 if any criterion score is lower than baseline.",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        help="Path to baseline result JSON (or dir). Used with --compare-baseline. Default: output_dir/baseline_<persona>.json",
    )
    parser.add_argument(
        "--list-personas",
        action="store_true",
        help="List available persona files and exit.",
    )
    parser.add_argument(
        "--list-criteria",
        action="store_true",
        help="List available criterion IDs and exit.",
    )
    parser.add_argument(
        "--criterion-file",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to JSON file defining an extra criterion (id, criterion, scoring_guide, considerations).",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        choices=["html"],
        help="Also write an HTML report (e.g. --report html) alongside the JSON result.",
    )
    parser.add_argument(
        "--sut-prompts",
        type=str,
        default=None,
        help="Comma-separated paths to SUT system prompt files. Run the same persona against each and compare.",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        metavar="N",
        help="Run up to N personas (or persona×prompt runs) in parallel. Default: 1 (sequential).",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="When using --batch-summary, also write batch_summary_TIMESTAMP.csv.",
    )
    parser.add_argument(
        "--write-index",
        action="store_true",
        help="After writing results, regenerate results/index.html (or OUTPUT_DIR/index.html) for browsing runs.",
    )
    parser.add_argument(
        "--config-file",
        type=str,
        default=None,
        help="Path to JSON config for defaults (sut_model, judge_model, output_dir, criteria, etc.). Default: look for safety-tester-config.json in project root.",
    )
    parser.add_argument(
        "--sut",
        type=str,
        default="anthropic",
        choices=["anthropic", "openai", "custom"],
        help="SUT backend: anthropic (Claude), openai (OpenAI/Azure), or custom (your HTTP API). Default: anthropic.",
    )
    parser.add_argument(
        "--sut-endpoint",
        type=str,
        default=None,
        help="For --sut custom: URL of the chat API (e.g. https://api.example.com/chat). Or set SUT_ENDPOINT.",
    )
    parser.add_argument(
        "--sut-api-key",
        type=str,
        default=None,
        help="For --sut custom (or openai): API key. Prefer env SUT_API_KEY or OPENAI_API_KEY for security.",
    )
    parser.add_argument(
        "--sut-response-path",
        type=str,
        default=None,
        help="For --sut custom: dot path to assistant text in response JSON (e.g. data.reply or choices.0.message.content).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run (personas, prompts, criteria, SUT) and exit without calling any API.",
    )
    parser.add_argument(
        "--history",
        type=str,
        default=None,
        metavar="PATH",
        help="Append each run to a JSONL history file (one JSON object per line). Use with scripts/show_history.py for trends.",
    )
    parser.add_argument(
        "--notify-webhook",
        type=str,
        default=None,
        help="On exit code 1, POST a JSON payload to this URL (e.g. Slack incoming webhook). Env: NOTIFY_WEBHOOK.",
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-run only failed runs from a batch summary (use with --retry-failed-from or latest in output dir).",
    )
    parser.add_argument(
        "--retry-failed-from",
        type=str,
        default=None,
        metavar="PATH",
        help="Batch summary JSON for --retry-failed. If omitted, use latest batch_summary_*.json in output dir.",
    )
    parser.add_argument(
        "--max-requests-per-minute",
        type=int,
        default=None,
        metavar="N",
        help="When using --parallel, cap at N SUT+judge requests per minute (approx). Ignored in mock.",
    )
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="After a successful run, write criterion_scores to baseline_<persona>.json for future --compare-baseline.",
    )
    parser.add_argument(
        "--notify-success",
        action="store_true",
        help="When run passes (exit 0), POST a summary to --notify-webhook (or NOTIFY_WEBHOOK).",
    )
    parser.add_argument(
        "--notify-format",
        type=str,
        default=None,
        choices=["slack"],
        help="Webhook payload format: 'slack' for Slack blocks (use with Slack incoming webhook). Env: NOTIFY_FORMAT.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Run one mock persona and exit 0 if the pipeline works (for deploy verification).",
    )
    parser.add_argument(
        "--branded-report",
        type=str,
        default=None,
        metavar="PATH",
        help="Write a single HTML report to PATH with optional branding (use with --report-branding-title for 'Run by X').",
    )
    parser.add_argument(
        "--report-branding-title",
        type=str,
        default=None,
        help="Title for branded report (e.g. 'Run by Acme Corp'). Used with --branded-report.",
    )
    parser.add_argument(
        "--run-timeout",
        type=int,
        default=None,
        metavar="SECONDS",
        help="Timeout per run (persona) in seconds. On timeout, the run is recorded as failed and the batch continues.",
    )
    parser.add_argument(
        "--judge",
        type=str,
        default=None,
        choices=["anthropic", "openai"],
        help="Judge backend: anthropic (default) or openai. Requires OPENAI_API_KEY for openai.",
    )
    parser.add_argument(
        "--criteria-dir",
        type=str,
        default=None,
        metavar="PATH",
        help="Load all criterion JSON files from this directory and add them to the criteria run.",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        metavar="N",
        help="Cap batch at N persona runs (e.g. --personas-dir personas --max-runs 3 for a quick smoke).",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (for CI or pipes).",
    )
    parser.add_argument(
        "--shard",
        type=str,
        default=None,
        metavar="N/M",
        help="Run only persona index i where i %% M == N (e.g. --shard 0/4, --shard 1/4 to split a batch across 4 runners). Personas are sorted before sharding.",
    )
    parser.add_argument(
        "--junit",
        type=str,
        default=None,
        metavar="PATH",
        help="Write JUnit-style XML report to PATH (for CI). Used with batch runs; one testcase per persona.",
    )
    parser.add_argument(
        "--failures-only",
        action="store_true",
        help="With batch runs: print only failed runs and stats (no full table).",
    )
    parser.add_argument(
        "--judge-temperature",
        type=float,
        default=None,
        metavar="F",
        help="Judge model temperature (0–1). Lower = more consistent scores. Default: 0. Config: judge_temperature.",
    )
    parser.add_argument(
        "--report-only",
        type=str,
        default=None,
        metavar="PATH",
        help="Re-score existing result JSON(s) without calling SUT. PATH = file or directory of result JSONs.",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=None,
        metavar="PATH",
        help="Cache SUT responses by (persona + prompt) hash. Re-use for re-judging or parallel runs. Env: CACHE_DIR.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Print timing per run (SUT vs judge) and total batch time.",
    )
    parser.add_argument(
        "--ndjson",
        action="store_true",
        help="Print one JSON object per run to stdout (for piping to jq etc.).",
    )
    parser.add_argument(
        "--redact",
        action="store_true",
        help="Redact conversation content in saved result JSON (replace with [redacted]) for compliance sharing.",
    )
    parser.add_argument(
        "--criterion-weights",
        type=str,
        default=None,
        metavar="CID=W,...",
        help="Weight criteria for final score (e.g. crisis_urgency=2,no_diagnosis=1). Default: min across criteria.",
    )
    return parser.parse_args()


def _load_defaults_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Load optional defaults from safety-tester-config.json (or --config-file path).
    Returns a dict with keys like sut_model, judge_model, output_dir, criteria (list).
    CLI and env override these.
    """
    project_root = Path(__file__).resolve().parent
    config_path = getattr(args, "config_file", None)
    if config_path:
        path = Path(config_path)
    else:
        path = project_root / "safety-tester-config.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _parse_shard(shard_arg: Optional[str]) -> Optional[Tuple[int, int]]:
    """Parse --shard N/M into (N, M). Returns None if invalid or not set."""
    if not shard_arg or not str(shard_arg).strip():
        return None
    parts = str(shard_arg).strip().split("/")
    if len(parts) != 2:
        return None
    try:
        n, m = int(parts[0].strip()), int(parts[1].strip())
        if m <= 0 or n < 0 or n >= m:
            return None
        return (n, m)
    except ValueError:
        return None


def _apply_shard(items: List[str], shard: Optional[Tuple[int, int]]) -> List[str]:
    """Filter items to indices i where i % M == N. Personas should already be sorted."""
    if not shard:
        return items
    n, m = shard
    return [items[i] for i in range(len(items)) if i % m == n]


def resolve_persona_path(persona_arg: str) -> Path:
    candidate = Path(persona_arg)
    if candidate.is_file():
        return candidate

    project_root = Path(__file__).resolve().parent
    persona_path = project_root / "personas" / persona_arg
    return persona_path


# Names of JSON files that are not persona scripts (excluded from --personas-dir discovery).
_NON_PERSONA_JSON = {"batch_config.json", "example_criterion.json", "persona_tags.json"}


def _discover_personas_from_dir(dir_path: Path) -> List[str]:
    """List persona JSON filenames in dir_path, excluding config/criterion/tags files."""
    if not dir_path.is_dir():
        return []
    out = []
    for f in sorted(dir_path.iterdir()):
        if f.suffix.lower() == ".json" and f.name not in _NON_PERSONA_JSON:
            out.append(f.name)
    return out


def _load_persona_tags(tags_dir: Path) -> Dict[str, List[str]]:
    """Load persona_tags.json from tags_dir. Returns dict mapping filename -> list of tags."""
    path = tags_dir / "persona_tags.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _filter_personas_by_tags(
    persona_list: List[str],
    tags_requested: List[str],
    tags_dir: Path,
) -> List[str]:
    """Keep only personas that have at least one of tags_requested in persona_tags.json."""
    if not tags_requested:
        return persona_list
    tag_map = _load_persona_tags(tags_dir)
    requested = {t.strip().lower() for t in tags_requested if t.strip()}
    if not requested:
        return persona_list
    out = []
    for p in persona_list:
        # Match by exact filename or stem
        key = p if p.endswith(".json") else f"{p}.json"
        tags = tag_map.get(key) or tag_map.get(p) or []
        if any((t or "").lower() in requested for t in tags):
            out.append(p)
    return out


def get_output_dir(args: argparse.Namespace) -> Path:
    """Resolve output directory: --output-dir, then OUTPUT_DIR env, then default results/."""
    raw = args.output_dir if hasattr(args, "output_dir") and args.output_dir else os.getenv("OUTPUT_DIR")
    if raw:
        path = Path(raw)
    else:
        project_root = Path(__file__).resolve().parent
        path = project_root / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_sut_system_prompt(args: argparse.Namespace) -> Optional[str]:
    """
    Resolve SUT system prompt: --sut-system-prompt (path) or SUT_SYSTEM_PROMPT env (path).
    If set, read file and return content; otherwise return None (use runner default).
    """
    raw = getattr(args, "sut_system_prompt", None) or os.getenv("SUT_SYSTEM_PROMPT")
    if not raw:
        return None
    path = Path(raw)
    if not path.is_file():
        raise FileNotFoundError(f"SUT system prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def get_sut_prompts_list(args: argparse.Namespace) -> Optional[List[Tuple[str, str]]]:
    """
    If --sut-prompts is set, return [(prompt_name_stem, prompt_text), ...]; else None.
    """
    raw = getattr(args, "sut_prompts", None)
    if not raw:
        return None
    paths = [s.strip() for s in raw.split(",") if s.strip()]
    out = []
    for p in paths:
        path = Path(p)
        if not path.is_file():
            raise FileNotFoundError(f"SUT prompt file not found: {path}")
        out.append((path.stem, path.read_text(encoding="utf-8").strip()))
    return out if out else None


def _redact_conversation(conversation: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of conversation with message content replaced by [redacted]."""
    import copy
    out = copy.deepcopy(conversation)
    for turn in out.get("turns", []):
        if "user_message" in turn:
            turn["user_message"] = "[redacted]"
        if "system_response" in turn:
            turn["system_response"] = "[redacted]"
    for msg in out.get("conversation_for_judge", []):
        if "content" in msg:
            msg["content"] = "[redacted]"
    return out


def save_result_json(
    results_dir: Path,
    persona_name: str,
    conversation: Dict[str, Any],
    judge_results: List[Dict[str, Any]],
    timestamp: Optional[str] = None,
    run_label: Optional[str] = None,
    run_id: Optional[str] = None,
    redact: bool = False,
    criterion_weights: Optional[Dict[str, float]] = None,
) -> Path:
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_persona = persona_name.replace(" ", "_")
    if run_label:
        safe_label = Path(run_label).stem.replace(" ", "_")
        filename = f"{timestamp}_{safe_persona}_{safe_label}.json"
    else:
        filename = f"{timestamp}_{safe_persona}.json"
    path = results_dir / filename

    criterion_scores = {
        r.get("criterion_id", f"criterion_{i}"): r.get("parsed", {}).get("score", 0)
        for i, r in enumerate(judge_results)
    }
    if criterion_weights and criterion_scores:
        total_w = sum(criterion_weights.get(c, 1.0) for c in criterion_scores)
        if total_w > 0:
            weighted = sum(criterion_scores.get(c, 0) * criterion_weights.get(c, 1.0) for c in criterion_scores) / total_w
            final_score = max(0, min(2, round(weighted)))
        else:
            final_score = min(criterion_scores.values()) if criterion_scores else 0
    else:
        final_score = min(criterion_scores.values()) if criterion_scores else 0

    conv_out = _redact_conversation(conversation) if redact else conversation
    payload = {
        "schema_version": "1",
        "timestamp_utc": timestamp,
        "persona_name": persona_name,
        "conversation": conv_out,
        "judge_results": judge_results,
        "criterion_scores": criterion_scores,
        "final_score": final_score,
    }
    if run_id:
        payload["run_id"] = run_id
    try:
        payload["tool_version"] = _get_version()
    except Exception:
        pass

    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return path


def save_result_md(
    results_dir: Path,
    persona_name: str,
    conversation: Dict[str, Any],
    judge_results: List[Dict[str, Any]],
    timestamp: str,
) -> Path:
    safe_persona = persona_name.replace(" ", "_")
    filename = f"{timestamp}_{safe_persona}.md"
    path = results_dir / filename

    lines = [
        f"# Mental Health Safety Evaluation: {persona_name}",
        "",
        f"**Timestamp (UTC):** {timestamp}",
        "",
        "## Criteria scores",
        "",
    ]
    for r in judge_results:
        cid = r.get("criterion_id", "")
        parsed = r.get("parsed", {})
        score = parsed.get("score", 0)
        rationale = parsed.get("rationale", "")
        lines.append(f"### {cid}")
        lines.append("")
        lines.append(f"- **Score:** {score}")
        lines.append(f"- **Rationale:** {rationale}")
        lines.append("")
    lines.append("## Conversation")
    lines.append("")
    for turn in conversation.get("turns", []):
        lines.append(f"**Turn {turn.get('turn')} — user:** {turn.get('user_message', '')}")
        lines.append("")
        lines.append(f"**assistant:** {turn.get('system_response', '')}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def save_result_html(
    results_dir: Path,
    persona_name: str,
    conversation: Dict[str, Any],
    judge_results: List[Dict[str, Any]],
    timestamp: str,
    run_label: Optional[str] = None,
) -> Path:
    """Write a single HTML report with transcript and criterion scores."""
    safe_persona = persona_name.replace(" ", "_")
    if run_label:
        safe_label = Path(run_label).stem.replace(" ", "_")
        filename = f"{timestamp}_{safe_persona}_{safe_label}.html"
    else:
        filename = f"{timestamp}_{safe_persona}.html"
    path = results_dir / filename

    rows_criteria = []
    for r in judge_results:
        cid = r.get("criterion_id", "")
        parsed = r.get("parsed", {})
        score = parsed.get("score", 0)
        rationale = parsed.get("rationale", "").replace("<", "&lt;").replace(">", "&gt;")
        rows_criteria.append(f"<tr><td>{cid}</td><td>{score}</td><td>{rationale}</td></tr>")

    rows_conv = []
    for turn in conversation.get("turns", []):
        u = (turn.get("user_message") or "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        a = (turn.get("system_response") or "").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        rows_conv.append(f"<tr><td>Turn {turn.get('turn')}</td><td>user</td><td>{u}</td></tr>")
        rows_conv.append(f"<tr><td></td><td>assistant</td><td>{a}</td></tr>")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Safety Evaluation: {persona_name}</title>
<style>
  body {{ font-family: system-ui,sans-serif; max-width: 900px; margin: 1rem auto; padding: 0 1rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
  th {{ background: #f5f5f5; }}
  .score-2 {{ color: green; }} .score-1 {{ color: #b8860b; }} .score-0 {{ color: red; }}
</style>
</head>
<body>
<h1>Mental Health Safety Evaluation: {persona_name}</h1>
<p><strong>Timestamp (UTC):</strong> {timestamp}</p>
<h2>Criteria scores</h2>
<table>
  <thead><tr><th>Criterion</th><th>Score</th><th>Rationale</th></tr></thead>
  <tbody>{"".join(rows_criteria)}</tbody>
</table>
<h2>Conversation</h2>
<table>
  <thead><tr><th>Turn</th><th>Role</th><th>Content</th></tr></thead>
  <tbody>{"".join(rows_conv)}</tbody>
</table>
</body>
</html>"""
    path.write_text(html, encoding="utf-8")
    return path


def _style_score(score: int) -> Text:
    if score == 2:
        return Text("2 (Meets criterion strongly)", style="bold green")
    if score == 1:
        return Text("1 (Partially meets criterion)", style="bold yellow")
    return Text("0 (Does NOT meet criterion)", style="bold red")


def print_conversation(conversation: Dict[str, Any]) -> None:
    table = Table(
        title="Conversation Transcript",
        box=box.SIMPLE_HEAVY,
        show_lines=True,
    )
    table.add_column("Turn", justify="center", style="cyan", no_wrap=True)
    table.add_column("Speaker", style="magenta")
    table.add_column("Message", style="white")

    for turn in conversation.get("turns", []):
        turn_idx = str(turn.get("turn", ""))
        user_msg = turn.get("user_message", "")
        sys_msg = turn.get("system_response", "")

        table.add_row(turn_idx, "user", user_msg)
        table.add_row(turn_idx, "assistant", sys_msg)

    console.print(table)


def print_results(judge_result: Dict[str, Any]) -> None:
    parsed = judge_result.get("parsed", {})
    score = int(parsed.get("score", 0))
    rationale = parsed.get("rationale", "No rationale provided.")
    critical_failures = parsed.get("critical_failures", [])
    positive_behaviors = parsed.get("positive_behaviors", [])
    criterion = judge_result.get("criterion")
    cid = judge_result.get("criterion_id", "")

    score_text = _style_score(score)

    header_title = f"AI Mental Health Safety Evaluation — {cid}" if cid else "AI Mental Health Safety Evaluation"
    header = Panel(Text(header_title, style="bold white"), style="bold blue")
    console.print(header)

    console.print(Text("Criterion:", style="bold white"))
    console.print(Text(criterion or "", style="italic cyan"))
    console.print()

    console.print(Text("Score:", style="bold white"))
    console.print(score_text)
    console.print()

    console.print(Text("Rationale:", style="bold white"))
    console.print(Text(rationale, style="white"))
    console.print()

    if critical_failures:
        console.print(Text("Critical Failures:", style="bold red"))
        for item in critical_failures:
            console.print(f"- {item}")
        console.print()

    if positive_behaviors:
        console.print(Text("Positive Behaviors:", style="bold green"))
        for item in positive_behaviors:
            console.print(f"- {item}")
        console.print()


def _mock_conversation(persona_name: str) -> Dict[str, Any]:
    persona_path = resolve_persona_path(persona_name)
    persona = load_persona(persona_path)

    turns: List[Dict[str, Any]] = []
    for turn in persona:
        msg = str(turn.get("message", ""))
        expected = str(turn.get("expected_behavior", ""))
        idx = turn.get("turn")
        system_response = (
            "MOCK RESPONSE: This is a simulated assistant reply. In a real run, this would be the "
            "model's response. Expected behavior for this turn was: "
            f"{expected}"
        )
        turns.append(
            {
                "turn": idx,
                "user_message": msg,
                "expected_behavior": expected,
                "system_response": system_response,
            }
        )

    conversation_for_judge: List[Dict[str, Any]] = []
    for turn in turns:
        conversation_for_judge.append(
            {"role": "user", "turn": turn["turn"], "content": turn["user_message"]}
        )
        conversation_for_judge.append(
            {"role": "assistant", "turn": turn["turn"], "content": turn["system_response"]}
        )

    return {
        "persona_name": persona_path.stem,
        "turns": turns,
        "conversation_for_judge": conversation_for_judge,
    }


def _mock_judge_all(
    criterion_ids: Optional[List[str]] = None,
    extra_specs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Return one mock judge result per selected criterion."""
    specs = get_criteria_specs(criterion_ids, extra_specs)
    rationale = (
        "MOCK MODE: This is a fake judge response for testing the pipeline without calling the "
        "Anthropic API. No real clinical evaluation was performed."
    )
    results = []
    for spec in specs:
        parsed = {
            "score": 2,
            "rationale": rationale,
            "critical_failures": [],
            "positive_behaviors": ["Mock mode always returns a passing score to verify plumbing."],
        }
        results.append({
            "criterion_id": spec["id"],
            "criterion": spec["criterion"],
            "raw_text": json.dumps(parsed, indent=2),
            "parsed": parsed,
        })
    return results


async def run_single_persona(
    persona_name: str,
    verbose: bool,
    sut_model: str,
    judge_model: str,
    mock: bool,
    output_dir: Path,
    quiet: bool,
    write_md: bool,
    system_prompt: Optional[str] = None,
    criterion_ids: Optional[List[str]] = None,
    log_path: Optional[Path] = None,
    extra_criterion_specs: Optional[List[Dict[str, Any]]] = None,
    run_label: Optional[str] = None,
    report_html: bool = False,
    sut_backend: str = "anthropic",
    sut_options: Optional[Dict[str, Any]] = None,
    history_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    judge_backend: str = "anthropic",
    judge_temperature: float = 0.0,
    cache_dir: Optional[Path] = None,
    profile: bool = False,
    redact: bool = False,
    criterion_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    persona_path = resolve_persona_path(persona_name)
    sut_seconds: Optional[float] = None
    judge_seconds: Optional[float] = None

    if mock:
        conversation = _mock_conversation(persona_name)
        if profile:
            sut_seconds = 0.0
            judge_seconds = 0.0
    else:
        cache_hit = False
        if cache_dir and cache_dir.is_dir():
            import hashlib
            key = hashlib.sha256((str(persona_path.resolve()) + (system_prompt or "")).encode()).hexdigest()[:24]
            cache_file = cache_dir / f"{key}.json"
            if cache_file.is_file():
                try:
                    cached = json.loads(cache_file.read_text(encoding="utf-8"))
                    conv_judge = cached.get("conversation_for_judge")
                    if isinstance(conv_judge, list):
                        conversation = {
                            "persona_name": persona_path.stem,
                            "turns": [],
                            "conversation_for_judge": conv_judge,
                        }
                        cache_hit = True
                except (json.JSONDecodeError, OSError):
                    pass
        if not cache_hit:
            try:
                if profile:
                    _t0 = time.perf_counter()
                conversation = await run_conversation(
                    persona_path,
                    model=sut_model,
                    system_prompt=system_prompt,
                    sut_backend=sut_backend,
                    sut_options=sut_options,
                )
                if profile:
                    sut_seconds = time.perf_counter() - _t0
                if cache_dir and cache_dir.is_dir():
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    import hashlib
                    key = hashlib.sha256((str(persona_path.resolve()) + (system_prompt or "")).encode()).hexdigest()[:24]
                    cache_file = cache_dir / f"{key}.json"
                    try:
                        cache_file.write_text(
                            json.dumps({"conversation_for_judge": conversation["conversation_for_judge"]}, indent=2),
                            encoding="utf-8",
                        )
                    except OSError:
                        pass
            except ConversationError as e:
                console.print(f"[bold red]Conversation error for persona '{persona_name}':[/bold red] {e}")
                _log_line(log_path, f"{datetime.utcnow().isoformat()}Z\t{persona_name}\terror=ConversationError\t{e}")
                if history_path:
                    _append_history(history_path, {"timestamp_utc": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"), "persona_name": persona_name, "error": str(e)})
                return {"persona_name": persona_name, "error": str(e)}

    if not quiet:
        console.rule(f"[bold cyan]Persona: {conversation.get('persona_name', persona_name)}[/bold cyan]")
        print_conversation(conversation)

    if mock:
        judge_results = _mock_judge_all(criterion_ids=criterion_ids, extra_specs=extra_criterion_specs)
        if profile and sut_seconds is None:
            sut_seconds = 0.0
        if profile and judge_seconds is None:
            judge_seconds = 0.0
    else:
        try:
            if profile:
                _t0 = time.perf_counter()
            judge_results = await score_all_criteria(
                conversation["conversation_for_judge"],
                model=judge_model,
                criterion_ids=criterion_ids,
                extra_specs=extra_criterion_specs,
                judge_backend=judge_backend,
                temperature=judge_temperature,
            )
            if profile:
                judge_seconds = time.perf_counter() - _t0
        except Exception as e:
            console.print(f"[bold red]Judge error for persona '{persona_name}':[/bold red] {e}")
            pname = conversation.get("persona_name", persona_name)
            _log_line(log_path, f"{datetime.utcnow().isoformat()}Z\t{pname}\terror=JudgeError\t{e}")
            if history_path:
                _append_history(history_path, {"timestamp_utc": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"), "persona_name": pname, "error": str(e)})
            return {"persona_name": pname, "error": str(e)}

    if verbose:
        console.print("\n[bold magenta]Raw judge response(s):[/bold magenta]")
        for r in judge_results:
            console.print(f"--- {r.get('criterion_id', '')} ---")
            console.print(r.get("raw_text", ""))
        console.print()

    if not quiet:
        for r in judge_results:
            print_results(r)

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    persona_display = conversation.get("persona_name", persona_name)

    result_path = save_result_json(
        results_dir=output_dir,
        persona_name=persona_display,
        conversation=conversation,
        judge_results=judge_results,
        timestamp=timestamp,
        run_label=run_label,
        run_id=run_id,
        redact=redact,
        criterion_weights=criterion_weights,
    )

    if write_md:
        md_path = save_result_md(
            results_dir=output_dir,
            persona_name=persona_display,
            conversation=conversation,
            judge_results=judge_results,
            timestamp=timestamp,
        )
        if not quiet:
            console.print(f"\n[bold green]Markdown report:[/bold green] {md_path}")
    if report_html:
        html_path = save_result_html(
            results_dir=output_dir,
            persona_name=persona_display,
            conversation=conversation,
            judge_results=judge_results,
            timestamp=timestamp,
            run_label=run_label,
        )
        if not quiet:
            console.print(f"[bold green]HTML report:[/bold green] {html_path}")

    if not quiet:
        console.print(f"\n[bold green]Results saved to:[/bold green] {result_path}")
    else:
        criterion_scores = {r.get("criterion_id", i): r.get("parsed", {}).get("score", 0) for i, r in enumerate(judge_results)}
        final_score = min(criterion_scores.values()) if criterion_scores else 0
        console.print(f"persona={persona_display} score={final_score} criterion_scores={criterion_scores} path={result_path}")

    criterion_scores = {r.get("criterion_id", f"c{i}"): r.get("parsed", {}).get("score", 0) for i, r in enumerate(judge_results)}
    if criterion_weights and criterion_scores:
        total_w = sum(criterion_weights.get(c, 1.0) for c in criterion_scores)
        final_score = max(0, min(2, round(sum(criterion_scores.get(c, 0) * criterion_weights.get(c, 1.0) for c in criterion_scores) / total_w))) if total_w > 0 else (min(criterion_scores.values()) if criterion_scores else 0)
    else:
        final_score = min(criterion_scores.values()) if criterion_scores else 0

    _log_line(
        log_path,
        f"{datetime.utcnow().isoformat()}Z\t{persona_display}\tscore={final_score}\tcriterion_scores={json.dumps(criterion_scores)}\tpath={result_path}",
    )

    out: Dict[str, Any] = {
        "persona_name": persona_display,
        "score": final_score,
        "criterion_scores": criterion_scores,
        "result_path": str(result_path),
    }
    if run_label is not None:
        out["run_label"] = run_label
    if profile and (sut_seconds is not None or judge_seconds is not None):
        out["sut_seconds"] = sut_seconds
        out["judge_seconds"] = judge_seconds
    try:
        meta = load_persona_metadata(persona_path)
        if meta:
            out["persona_meta"] = meta
    except Exception:
        pass
    if history_path:
        record = {"timestamp_utc": timestamp, "persona_name": persona_display, "score": final_score, "criterion_scores": criterion_scores, "result_path": str(result_path)}
        if run_label:
            record["run_label"] = run_label
        _append_history(history_path, record)
    return out


def _parse_list_arg(value: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated string into list of stripped non-empty strings."""
    if not value:
        return None
    return [s.strip() for s in value.split(",") if s.strip()]


def _parse_fail_under_criteria(value: Optional[str]) -> Optional[Dict[str, int]]:
    """Parse e.g. crisis_urgency=2,no_diagnosis=1 into {criterion_id: min_score}."""
    if not value:
        return None
    out: Dict[str, int] = {}
    for part in value.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        cid, _, n = part.partition("=")
        cid, n = cid.strip(), n.strip()
        try:
            out[cid] = int(n)
        except ValueError:
            continue
    return out if out else None


def _parse_criterion_weights(value: Optional[str]) -> Optional[Dict[str, float]]:
    """Parse e.g. crisis_urgency=2,no_diagnosis=1 into {criterion_id: weight}."""
    if not value:
        return None
    out: Dict[str, float] = {}
    for part in value.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        cid, _, w = part.partition("=")
        cid, w = cid.strip(), w.strip()
        try:
            out[cid] = float(w)
        except ValueError:
            continue
    return out if out else None


def _load_baseline(path: Path) -> Optional[Dict[str, int]]:
    """Load baseline result JSON and return criterion_scores dict, or None if missing/invalid."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        scores = data.get("criterion_scores") or data.get("judge_results")
        if isinstance(scores, dict):
            return {k: int(v) for k, v in scores.items() if isinstance(v, (int, float))}
        if isinstance(scores, list):
            return {r.get("criterion_id"): int(r.get("parsed", {}).get("score", 0)) for r in scores if r.get("criterion_id") is not None}
        return None
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def _load_criterion_file(path: Path) -> List[Dict[str, Any]]:
    """Load a single criterion from JSON: id, criterion, scoring_guide, considerations (optional). Returns list of one spec."""
    if not path.is_file():
        raise FileNotFoundError(f"Criterion file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Criterion file must be a JSON object.")
    for key in ("id", "criterion", "scoring_guide"):
        if key not in data:
            raise ValueError(f"Criterion file missing required key: {key}")
    spec = {
        "id": str(data["id"]),
        "criterion": str(data["criterion"]),
        "scoring_guide": str(data["scoring_guide"]),
        "considerations": str(data.get("considerations", "")),
    }
    return [spec]


def _load_criteria_dir(dir_path: Path) -> List[Dict[str, Any]]:
    """Load all criterion JSON files from a directory. Returns list of specs."""
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Criteria directory not found: {dir_path}")
    specs: List[Dict[str, Any]] = []
    for f in sorted(dir_path.glob("*.json")):
        try:
            specs.extend(_load_criterion_file(f))
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"{f.name}: {e}") from e
    return specs


def _print_prompt_comparison_table(summary: List[Dict[str, Any]], prompts_list: List[Tuple[str, str]]) -> None:
    """Print a table of persona x prompt -> score when running with --sut-prompts."""
    prompt_names = [p[0] for p in prompts_list]
    personas = sorted({item.get("persona_name", "") for item in summary if item.get("persona_name")})
    table = Table(title="SUT prompt comparison", box=box.SIMPLE_HEAVY, show_lines=True)
    table.add_column("Persona", style="cyan")
    for pname in prompt_names:
        table.add_column(pname, style="white")
    for persona in personas:
        row = [persona]
        for pname in prompt_names:
            match = next(
                (item for item in summary
                 if item.get("persona_name") == persona and item.get("run_label") == pname),
                None,
            )
            cell = str(match.get("score", "—")) if match else "—"
            row.append(cell)
        table.add_row(*row)
    console.print()
    console.print(table)


def _check_baseline(
    persona_name: str,
    criterion_scores: Dict[str, int],
    baseline_scores: Dict[str, int],
    quiet: bool,
) -> bool:
    """Return False if any current score < baseline (regression)."""
    for cid, base_score in baseline_scores.items():
        current = criterion_scores.get(cid, 0)
        if current < base_score:
            if not quiet:
                console.print(f"[bold red]Regression: {persona_name} criterion {cid} score {current} < baseline {base_score}[/bold red]")
            return False
    return True


async def _run_one(
    persona_name: str,
    args: argparse.Namespace,
    sut_model: str,
    judge_model: str,
    mock: bool,
    output_dir: Path,
    quiet: bool,
    write_md: bool,
    criterion_ids: Optional[List[str]],
    log_path: Optional[Path],
    extra_criterion_specs: Optional[List[Dict[str, Any]]],
    system_prompt: Optional[str],
    run_label: Optional[str],
    report_html: bool,
    semaphore: Optional[asyncio.Semaphore],
    sut_backend: str = "anthropic",
    sut_options: Optional[Dict[str, Any]] = None,
    history_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    run_timeout: Optional[int] = None,
    on_complete_msg: Optional[str] = None,
    judge_backend: str = "anthropic",
    judge_temperature: float = 0.0,
    cache_dir: Optional[Path] = None,
    profile: bool = False,
    redact: bool = False,
    criterion_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Run a single persona (optionally under a semaphore for parallel batch)."""
    async def _do() -> Dict[str, Any]:
        out = await run_single_persona(
            persona_name,
            verbose=args.verbose,
            sut_model=sut_model,
            judge_model=judge_model,
            mock=mock,
            judge_temperature=judge_temperature,
            cache_dir=cache_dir,
            profile=profile,
            redact=redact,
            criterion_weights=criterion_weights,
            output_dir=output_dir,
            quiet=quiet,
            write_md=write_md,
            system_prompt=system_prompt,
            criterion_ids=criterion_ids,
            log_path=log_path,
            extra_criterion_specs=extra_criterion_specs,
            run_label=run_label,
            report_html=report_html,
            sut_backend=sut_backend,
            sut_options=sut_options,
            history_path=history_path,
            run_id=run_id,
            judge_backend=judge_backend,
        )
        if on_complete_msg:
            console.print(on_complete_msg)
        return out
    coro = _do()
    if run_timeout and run_timeout > 0:
        try:
            return await asyncio.wait_for(coro, timeout=float(run_timeout))
        except asyncio.TimeoutError:
            return {
                "persona_name": persona_name,
                "run_label": run_label,
                "error": f"Run timed out after {run_timeout}s",
                "score": None,
                "criterion_scores": {},
            }
    if semaphore:
        async with semaphore:
            return await coro
    return await coro


def _build_notify_payload(
    message: str,
    passed: bool,
    summary: Optional[List[Dict[str, Any]]],
    notify_format: Optional[str],
) -> str:
    """Build JSON payload for webhook. If notify_format is 'slack', use Slack blocks."""
    if (notify_format or "").strip().lower() == "slack":
        lines = [f"*Mental Health Safety Tester*: {message}"]
        if summary:
            for s in (summary or [])[:15]:
                p = s.get("persona_name", "?")
                sc = s.get("score")
                err = s.get("error")
                if err:
                    lines.append(f"• {p}: error")
                else:
                    lines.append(f"• {p}: score {sc}")
            if len(summary) > 15:
                lines.append(f"_... and {len(summary) - 15} more_")
        text = "\n".join(lines)
        payload = {
            "text": message,
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": text}},
            ],
        }
        return json.dumps(payload)
    return json.dumps({"text": message, "passed": passed, "runs": summary})


def _notify_failure(
    webhook_url: Optional[str],
    message: str,
    summary: Optional[List[Dict[str, Any]]] = None,
    notify_format: Optional[str] = None,
) -> None:
    """POST a JSON payload to webhook_url (e.g. Slack) on failure. Silently ignore errors."""
    if not webhook_url or not webhook_url.strip():
        return
    try:
        import urllib.request
        body = _build_notify_payload(message, False, summary, notify_format)
        req = urllib.request.Request(webhook_url, data=body.encode("utf-8"), method="POST", headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def _notify_success(
    webhook_url: Optional[str],
    summary: List[Dict[str, Any]],
    message: str,
    notify_format: Optional[str] = None,
) -> None:
    """POST a JSON payload to webhook_url on success. Silently ignore errors."""
    if not webhook_url or not webhook_url.strip():
        return
    try:
        import urllib.request
        body = _build_notify_payload(message, True, summary, notify_format)
        req = urllib.request.Request(webhook_url, data=body.encode("utf-8"), method="POST", headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def _load_retry_failed(
    path: Optional[Path],
    output_dir: Path,
    fail_under: Optional[int],
) -> List[Tuple[str, Optional[str]]]:
    """Load batch summary and return list of (persona_name, run_label) for failed runs (error or score < fail_under)."""
    if path is None or not path.is_file():
        # Find latest batch_summary_*.json in output_dir
        summaries = sorted(output_dir.glob("batch_summary_*.json"), key=lambda p: p.name, reverse=True)
        if not summaries:
            return []
        path = summaries[0]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    runs = data.get("runs") or []
    out: List[Tuple[str, Optional[str]]] = []
    for r in runs:
        if r.get("error"):
            persona = (r.get("persona") or "").strip()
            if persona:
                label = (r.get("run_label") or "").strip() or None
                out.append((persona, label))
            continue
        if fail_under is not None:
            score = r.get("score")
            if score is None or int(score) < fail_under:
                persona = (r.get("persona") or "").strip()
                if persona:
                    label = (r.get("run_label") or "").strip() or None
                    out.append((persona, label))
    return out


def _write_branded_report(
    path: Path,
    summary: List[Dict[str, Any]],
    title: Optional[str] = None,
) -> None:
    """Write a single HTML report with optional branding (e.g. 'Run by Acme Corp')."""
    rows = []
    for item in summary:
        p = item.get("persona_name", "")
        s = item.get("score", "—")
        err = item.get("error", "")
        rows.append(f"<tr><td>{p}</td><td>{s}</td><td>{err or '—'}</td></tr>")
    branding = f"<p><strong>{title}</strong></p>" if title else ""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Safety Run Report</title>
<style>body {{ font-family: system-ui,sans-serif; max-width: 800px; margin: 1rem auto; padding: 0 1rem; }} table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #ccc; padding: 0.5rem; }} th {{ background: #f5f5f5; }}</style>
</head>
<body>
<h1>Mental Health Safety Run Report</h1>
<p>Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC</p>
{branding}
<h2>Runs</h2>
<table>
<thead><tr><th>Persona</th><th>Score</th><th>Error</th></tr></thead>
<tbody>{"".join(rows)}</tbody>
</table>
</body>
</html>"""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    except OSError:
        pass


def _write_results_index(output_dir: Path) -> None:
    """Regenerate results/index.html (or OUTPUT_DIR/index.html) by running the index script."""
    project_root = Path(__file__).resolve().parent
    script = project_root / "scripts" / "generate_results_index.py"
    if not script.is_file():
        return
    try:
        subprocess.run(
            [os.environ.get("PYTHON", "python3"), str(script), "--output-dir", str(output_dir)],
            cwd=str(project_root),
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def _maybe_save_baseline_and_notify_success(
    args: argparse.Namespace,
    output_dir: Path,
    summary: List[Dict[str, Any]],
    notify_webhook: Optional[str],
    quiet: bool,
) -> None:
    """If --save-baseline or --notify-success set, save baselines and/or POST success to webhook."""
    if quiet and summary:
        fail_under = getattr(args, "fail_under", None)
        passed = sum(
            1
            for s in summary
            if not s.get("error")
            and (fail_under is None or (s.get("score") is not None and int(s["score"]) >= fail_under))
        )
        failed = len(summary) - passed
        console.print(f"Passed: {passed}, Failed: {failed}")
    if getattr(args, "save_baseline", False):
        for item in summary:
            if item.get("error"):
                continue
            cs = item.get("criterion_scores") or {}
            if cs:
                _save_baseline(
                    output_dir,
                    item.get("persona_name", ""),
                    cs,
                    item.get("run_label"),
                )
    if getattr(args, "notify_success", False) and notify_webhook and summary:
        n = len(summary)
        failed = sum(1 for s in summary if s.get("error"))
        msg = f"Safety run passed: {n} run(s), all scores meet threshold." if failed == 0 else f"Safety run completed: {n} run(s)."
        _notify_success(notify_webhook, summary, msg, getattr(args, "notify_format", None) or os.getenv("NOTIFY_FORMAT"))
    if getattr(args, "branded_report", None) and summary:
        _write_branded_report(Path(args.branded_report), summary, getattr(args, "report_branding_title", None))
    if getattr(args, "write_index", False):
        _write_results_index(output_dir)


def _save_baseline(
    output_dir: Path,
    persona_name: str,
    criterion_scores: Dict[str, int],
    run_label: Optional[str] = None,
) -> None:
    """Write baseline JSON for this persona so --compare-baseline can use it later."""
    safe = persona_name.replace(" ", "_")
    if run_label:
        safe_label = Path(run_label).stem.replace(" ", "_")
        path = output_dir / f"baseline_{safe}_{safe_label}.json"
    else:
        path = output_dir / f"baseline_{safe}.json"
    payload = {
        "schema_version": "1",
        "persona_name": persona_name,
        "criterion_scores": criterion_scores,
        "timestamp_utc": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
    }
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def _append_history(history_path: Optional[Path], record: Dict[str, Any]) -> None:
    """Append one JSON object (as a single line) to the history file."""
    if not history_path:
        return
    try:
        with history_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _log_line(log_path: Optional[Path], line: str) -> None:
    """Append a line to the log file if --log was set."""
    if not log_path:
        return
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _compute_summary_by_tag(
    summary: List[Dict[str, Any]],
    tags_dir: Path,
    fail_under: Optional[int],
) -> Dict[str, Dict[str, int]]:
    """Return dict tag -> {passed, failed, total} for batch summary persistence."""
    tag_map = _load_persona_tags(tags_dir)
    if not tag_map:
        return {}
    by_tag: Dict[str, List[Dict[str, Any]]] = {}
    for item in summary:
        pname = item.get("persona_name", "")
        key = pname if pname.endswith(".json") else f"{pname}.json"
        tags = tag_map.get(key) or tag_map.get(pname) or []
        for t in (tags if isinstance(tags, list) else []) or []:
            t = (t or "").strip()
            if t:
                by_tag.setdefault(t, []).append(item)
    out: Dict[str, Dict[str, int]] = {}
    for tag, items in by_tag.items():
        n_passed = sum(
            1
            for i in items
            if not i.get("error")
            and (fail_under is None or (i.get("score") is not None and int(i["score"]) >= fail_under))
        )
        out[tag] = {"passed": n_passed, "failed": len(items) - n_passed, "total": len(items)}
    return out


def _write_batch_summary(
    output_dir: Path,
    summary: List[Dict[str, Any]],
    write_md: bool,
    write_csv: bool = False,
    audit: bool = True,
    tags_dir: Optional[Path] = None,
    fail_under: Optional[int] = None,
    run_id: Optional[str] = None,
) -> None:
    """Write batch_summary_TIMESTAMP.json and optionally .md, .csv, and audit report to output_dir."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rows = []
    criterion_columns: List[str] = []
    for item in summary:
        cs = item.get("criterion_scores") or {}
        for cid in cs:
            if cid not in criterion_columns:
                criterion_columns.append(cid)
        row = {
            "persona": item.get("persona_name", ""),
            "run_label": item.get("run_label", ""),
            "score": item.get("score"),
            "error": item.get("error"),
            "result_path": item.get("result_path"),
            "criterion_scores": cs,
        }
        if item.get("persona_meta"):
            row["persona_meta"] = item["persona_meta"]
            row["severity"] = item["persona_meta"].get("severity")
        else:
            row["severity"] = None
        rows.append(row)
    payload: Dict[str, Any] = {"schema_version": "1", "timestamp_utc": timestamp, "runs": rows}
    if run_id:
        payload["run_id"] = run_id
    try:
        payload["tool_version"] = _get_version()
    except Exception:
        pass
    summary_by_tag = _compute_summary_by_tag(summary, tags_dir, fail_under) if tags_dir else {}
    if summary_by_tag:
        payload["summary_by_tag"] = summary_by_tag
    path = output_dir / f"batch_summary_{timestamp}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    if write_md:
        md_path = output_dir / f"batch_summary_{timestamp}.md"
        lines = [f"# Batch summary — {timestamp}", ""]
        if run_id:
            lines.append(f"**Run ID:** {run_id}")
            lines.append("")
        if summary_by_tag:
            lines.append("## Summary by tag")
            lines.append("")
            for tag in sorted(summary_by_tag.keys()):
                s = summary_by_tag[tag]
                lines.append(f"- **{tag}:** {s['passed']} passed, {s['failed']} failed, {s['total']} total")
            lines.append("")
        lines.append("## Runs")
        lines.append("")
        for r in rows:
            lines.append(f"### {r['persona']}" + (f" ({r.get('run_label', '')})" if r.get("run_label") else ""))
            lines.append(f"- **Score:** {r['score']}")
            if r.get("error"):
                lines.append(f"- **Error:** {r['error']}")
            if r.get("result_path"):
                lines.append(f"- **Result:** {r['result_path']}")
            lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")
    if write_csv:
        import csv
        csv_path = output_dir / f"batch_summary_{timestamp}.csv"
        headers = ["persona", "run_label", "score", "error", "result_path"] + criterion_columns
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                row = {
                    "persona": r["persona"],
                    "run_label": r.get("run_label", ""),
                    "score": r.get("score", ""),
                    "error": r.get("error", "") or "",
                    "result_path": r.get("result_path", "") or "",
                }
                for cid in criterion_columns:
                    row[cid] = r["criterion_scores"].get(cid, "")
                w.writerow(row)
    if audit:
        audit_path = output_dir / f"batch_audit_{timestamp}.json"
        audit_data = {
            "schema_version": "1",
            "timestamp_utc": timestamp,
            "run_count": len(rows),
            "runs": [
                {
                    "persona": r["persona"],
                    "run_label": r.get("run_label", ""),
                    "severity": r.get("severity"),
                    "score": r.get("score"),
                    "error": r.get("error"),
                    "result_path": r.get("result_path"),
                    "criterion_scores": r.get("criterion_scores", {}),
                }
                for r in rows
            ],
        }
        if run_id:
            audit_data["run_id"] = run_id
        if summary_by_tag:
            audit_data["summary_by_tag"] = summary_by_tag
        try:
            audit_data["tool_version"] = _get_version()
        except Exception:
            pass
        with audit_path.open("w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)
    _write_batch_report_html(output_dir, summary, timestamp, rows)


def _write_batch_report_html(
    output_dir: Path,
    summary: List[Dict[str, Any]],
    timestamp: str,
    rows: List[Dict[str, Any]],
) -> None:
    """Write batch_report_TIMESTAMP.html with a table and expandable rows (criterion_scores, severity)."""
    path = output_dir / f"batch_report_{timestamp}.html"
    severity_col = '<th>Severity</th>' if any(r.get("severity") for r in rows) else ''
    trs = []
    for r in rows:
        persona = _escape_html(str(r.get("persona", "")))
        run_label = _escape_html(str(r.get("run_label", "") or ""))
        label = f"{persona}" + (f" ({run_label})" if run_label else "")
        score = r.get("score")
        score_str = str(score) if score is not None else "—"
        err = _escape_html(str(r.get("error") or ""))
        rpath = r.get("result_path") or ""
        result_basename = Path(rpath).name if rpath else "—"
        href = _escape_html(result_basename) if rpath else "#"
        sev = _escape_html(str(r.get("severity") or ""))
        cs = r.get("criterion_scores") or {}
        details = "<br />".join(f"{k}: {v}" for k, v in sorted(cs.items()))
        severity_cell = f'<td>{sev}</td>' if severity_col else ''
        trs.append(
            f'<tr><td>{label}</td>{severity_cell}<td>{score_str}</td><td>{err}</td>'
            f'<td><a href="{href}">{_escape_html(result_basename)}</a></td>'
            f'<td><details><summary>Details</summary><pre>{_escape_html(details)}</pre></details></td></tr>'
        )
    table_rows = "\n".join(trs)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"/><title>Batch report — {_escape_html(timestamp)}</title>
<style>table {{ border-collapse: collapse; }} th, td {{ border: 1px solid #ccc; padding: 6px; }} pre {{ margin: 0; }}</style></head>
<body><h1>Batch report — {timestamp}</h1>
<table><thead><tr><th>Persona</th>{severity_col}<th>Score</th><th>Error</th><th>Result</th><th>Details</th></tr></thead>
<tbody>
{table_rows}
</tbody></table></body></html>"""
    try:
        path.write_text(html, encoding="utf-8")
    except OSError:
        pass


def _escape_html(s: str) -> str:
    """Escape for HTML text content."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _write_junit(
    path: Path,
    summary: List[Dict[str, Any]],
    fail_under: Optional[int],
) -> None:
    """Write a JUnit-style XML report (one testcase per run) for CI."""
    import xml.sax.saxutils as sax
    def esc(s: str) -> str:
        return sax.escape(str(s) if s is not None else "", entities={"'": "&apos;", '"': "&quot;"})
    failures = 0
    cases = []
    for item in summary:
        name = item.get("persona_name", "unknown")
        if item.get("run_label"):
            name = f"{name}({item.get('run_label')})"
        err = item.get("error")
        score = item.get("score")
        failed = bool(err) or (fail_under is not None and score is not None and int(score) < fail_under)
        if failed:
            failures += 1
        msg = err if err else (f"score {score} below {fail_under}" if failed and score is not None else "")
        if failed:
            cases.append(f'    <testcase name="{esc(name)}"><failure message="{esc(msg)}"/></testcase>')
        else:
            cases.append(f'    <testcase name="{esc(name)}"/>')
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuite name="mental-health-safety" tests="{len(summary)}" failures="{failures}">\n'
        + "\n".join(cases) + "\n"
        "</testsuite>\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml_content, encoding="utf-8")


async def _gather_with_progress(
    tasks: List[Any],
    quiet: bool,
) -> List[Dict[str, Any]]:
    """Run coroutines and optionally show a progress bar when not quiet and len(tasks) > 1."""
    if quiet or len(tasks) <= 1:
        return list(await asyncio.gather(*tasks))

    with Progress() as progress:
        task_id = progress.add_task("Runs", total=len(tasks))
        async def wrap(i: int, c: Any) -> Tuple[int, Dict[str, Any]]:
            result = await c
            progress.advance(task_id)
            return (i, result)
        results = await asyncio.gather(*[wrap(i, t) for i, t in enumerate(tasks)])
        return [r for _, r in sorted(results, key=lambda x: x[0])]


def _generate_run_id() -> str:
    import random
    import string
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{ts}_{suffix}"


async def main_async(args: argparse.Namespace) -> int:
    defaults = _load_defaults_config(args)
    sut_model = (
        args.sut_model
        or os.getenv("SUT_MODEL")
        or defaults.get("sut_model")
        or "claude-haiku-4-5-20251001"
    )
    judge_model = (
        getattr(args, "judge_model", None)
        or os.getenv("JUDGE_MODEL")
        or defaults.get("judge_model")
        or "claude-sonnet-4-6"
    )
    mock_env = os.getenv("SAFETY_TESTER_MOCK", "").lower() in {"1", "true", "yes"}
    # Default is mock; only use real API when --live is set. SAFETY_TESTER_MOCK or --mock force mock.
    mock = mock_env or getattr(args, "mock", False) or (not getattr(args, "live", False))
    output_dir = get_output_dir(args)
    if defaults.get("output_dir") and not (getattr(args, "output_dir", None) or os.getenv("OUTPUT_DIR")):
        output_dir = Path(defaults["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
    quiet = getattr(args, "quiet", False)
    profile = getattr(args, "profile", False)
    write_md = getattr(args, "md", False)
    write_csv = getattr(args, "csv", False)
    criterion_ids = _parse_list_arg(getattr(args, "criteria", None))
    if criterion_ids is None and defaults.get("criteria"):
        crit = defaults["criteria"]
        criterion_ids = crit if isinstance(crit, list) else [c.strip() for c in str(crit).split(",") if c.strip()]
    personas_override = _parse_list_arg(getattr(args, "personas", None))
    project_root = Path(__file__).resolve().parent
    personas_dir: Optional[Path] = Path(args.personas_dir) if getattr(args, "personas_dir", None) else None
    persona_tags_requested = _parse_list_arg(getattr(args, "persona_tags", None))
    parallel = max(1, int(getattr(args, "parallel", 1)))
    sut_backend = (getattr(args, "sut", None) or defaults.get("sut") or "anthropic").strip().lower()
    sut_options: Dict[str, Any] = {}
    if sut_backend == "custom":
        sut_options["endpoint"] = getattr(args, "sut_endpoint", None) or os.getenv("SUT_ENDPOINT") or defaults.get("sut_endpoint")
        sut_options["api_key"] = getattr(args, "sut_api_key", None) or os.getenv("SUT_API_KEY") or defaults.get("sut_api_key")
        rp = getattr(args, "sut_response_path", None) or os.getenv("SUT_RESPONSE_PATH") or defaults.get("sut_response_path")
        if rp:
            sut_options["response_path"] = rp
    elif sut_backend == "openai":
        sut_options["api_key"] = getattr(args, "sut_api_key", None) or os.getenv("OPENAI_API_KEY") or defaults.get("sut_api_key")
    judge_backend = (getattr(args, "judge", None) or defaults.get("judge") or "anthropic").strip().lower()
    if judge_backend == "openai":
        judge_model = (
            getattr(args, "judge_model", None)
            or os.getenv("JUDGE_MODEL_OPENAI")
            or defaults.get("judge_model_openai")
            or os.getenv("JUDGE_MODEL")
            or defaults.get("judge_model")
            or "gpt-4o-mini"
        )
    run_timeout = getattr(args, "run_timeout", None) or defaults.get("run_timeout")
    judge_temperature = getattr(args, "judge_temperature", None)
    if judge_temperature is None:
        judge_temperature = float(defaults.get("judge_temperature", 0.0))
    cache_dir: Optional[Path] = None
    if getattr(args, "cache_dir", None) or os.getenv("CACHE_DIR"):
        cache_dir = Path(args.cache_dir or os.getenv("CACHE_DIR", ""))
    log_path = None
    if getattr(args, "log", None):
        log_path = Path(args.log)
    batch_summary = getattr(args, "batch_summary", False)
    history_path = None
    if getattr(args, "history", None) or os.getenv("HISTORY_FILE"):
        history_path = Path(args.history or os.getenv("HISTORY_FILE", ""))
    notify_webhook = getattr(args, "notify_webhook", None) or os.getenv("NOTIFY_WEBHOOK") or None
    notify_format = getattr(args, "notify_format", None) or os.getenv("NOTIFY_FORMAT") or None
    try:
        import rate_limit
        rate_limit.set_max_per_minute(getattr(args, "max_requests_per_minute", None))
    except ImportError:
        pass

    try:
        prompts_list = get_sut_prompts_list(args)
        if prompts_list is None:
            system_prompt = get_sut_system_prompt(args)
        else:
            system_prompt = None  # per-run prompt used in loop
    except FileNotFoundError as e:
        console.print(f"[bold red]{e}[/bold red]")
        return 1

    report_html = getattr(args, "report", None) == "html"
    fail_under_criteria = _parse_fail_under_criteria(getattr(args, "fail_under_criteria", None))
    compare_baseline = getattr(args, "compare_baseline", False)
    baseline_path_or_dir = getattr(args, "baseline", None)
    redact = getattr(args, "redact", False)
    criterion_weights = _parse_criterion_weights(getattr(args, "criterion_weights", None)) or defaults.get("criterion_weights")

    extra_criterion_specs: Optional[List[Dict[str, Any]]] = None
    if getattr(args, "criterion_file", None):
        try:
            extra_criterion_specs = _load_criterion_file(Path(args.criterion_file))
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]Criterion file: {e}[/bold red]")
            return 1
    if getattr(args, "criteria_dir", None):
        try:
            from_dir = _load_criteria_dir(Path(args.criteria_dir))
            extra_criterion_specs = (extra_criterion_specs or []) + from_dir
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]Criteria dir: {e}[/bold red]")
            return 1
    if criterion_ids:
        try:
            get_criteria_specs(criterion_ids, extra_criterion_specs)
        except ValueError as e:
            console.print(f"[bold red]{e}[/bold red]")
            return 1

    if sut_backend == "custom" and not sut_options.get("endpoint"):
        console.print("[bold red]--sut custom requires an endpoint. Set --sut-endpoint URL or SUT_ENDPOINT.[/bold red]")
        return 1
    try:
        get_backend(sut_backend)
    except ValueError as e:
        console.print(f"[bold red]{e}[/bold red]")
        return 1

    # --report-only: re-score existing result JSON(s) without calling SUT
    if getattr(args, "report_only", None):
        report_path = Path(args.report_only)
        if report_path.is_file():
            result_files = [report_path]
        elif report_path.is_dir():
            result_files = sorted(
                f for f in report_path.glob("*.json")
                if f.name.startswith("2") and "batch_summary" not in f.name and "batch_audit" not in f.name and "baseline" not in f.name
            )
        else:
            console.print(f"[bold red]--report-only path not found: {report_path}[/bold red]")
            return 1
        if not result_files:
            console.print("[bold red]No result JSON files found for --report-only.[/bold red]")
            return 1
        for res_path in result_files:
            try:
                data = json.loads(res_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                console.print(f"[bold red]Failed to load {res_path}: {e}[/bold red]")
                return 1
            conv = (data.get("conversation") or {}).get("conversation_for_judge")
            if not conv:
                console.print(f"[yellow]Skipping {res_path.name}: no conversation_for_judge.[/yellow]")
                continue
            if mock:
                judge_results = _mock_judge_all(criterion_ids=criterion_ids, extra_specs=extra_criterion_specs)
            else:
                try:
                    judge_results = await score_all_criteria(
                        conv,
                        model=judge_model,
                        criterion_ids=criterion_ids,
                        extra_specs=extra_criterion_specs,
                        judge_backend=judge_backend,
                        temperature=judge_temperature,
                    )
                except Exception as e:
                    console.print(f"[bold red]Judge error for {res_path.name}: {e}[/bold red]")
                    return 1
            criterion_scores = {r.get("criterion_id", f"c{i}"): r.get("parsed", {}).get("score", 0) for i, r in enumerate(judge_results)}
            data["judge_results"] = [
                {"criterion_id": r.get("criterion_id"), "criterion": r.get("criterion"), "raw_text": r.get("raw_text"), "parsed": r.get("parsed")}
                for r in judge_results
            ]
            data["criterion_scores"] = criterion_scores
            data["final_score"] = min(criterion_scores.values()) if criterion_scores else 0
            res_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            if not quiet:
                console.print(f"[green]Re-scored: {res_path.name} (score={data['final_score']})[/green]")
        return 0

    # --retry-failed: re-run only failed runs from a batch summary
    if getattr(args, "retry_failed", False):
        retry_from = getattr(args, "retry_failed_from", None)
        path = Path(retry_from) if retry_from else None
        fail_under = getattr(args, "fail_under", None)
        retry_list = _load_retry_failed(path, output_dir, fail_under)
        if not retry_list:
            if not quiet:
                console.print("No failed runs to retry (or no batch summary found).")
            return 0
        if not quiet:
            console.print(f"Retrying {len(retry_list)} failed run(s).")
        run_id = _generate_run_id()
        sem = asyncio.Semaphore(parallel) if parallel > 1 else None
        tasks = []
        for persona_name, run_label in retry_list:
            tasks.append(
                _run_one(
                    persona_name,
                    args,
                    sut_model,
                    judge_model,
                    mock,
                    output_dir,
                    quiet,
                    write_md,
                    criterion_ids,
                    log_path,
                    extra_criterion_specs,
                    system_prompt,
                    run_label,
                    report_html,
                    sem,
                    sut_backend,
                    sut_options,
                    history_path,
                    run_id=run_id,
                    run_timeout=run_timeout,
                    judge_backend=judge_backend,
                    judge_temperature=judge_temperature,
                    cache_dir=cache_dir,
                    profile=profile,
                    redact=redact,
                    criterion_weights=criterion_weights,
                )
            )
        summary = await _gather_with_progress(tasks, quiet)
        if batch_summary and len(summary) > 1:
            _write_batch_summary(
                output_dir,
                summary,
                write_md=write_md,
                write_csv=write_csv,
                tags_dir=project_root / "personas",
                fail_under=getattr(args, "fail_under", None),
                run_id=run_id,
            )
        if getattr(args, "junit", None):
            _write_junit(Path(args.junit), summary, getattr(args, "fail_under", None))
        fail_under = getattr(args, "fail_under", None)
        if not quiet:
            if getattr(args, "failures_only", False):
                _print_failed_runs(summary, fail_under)
                _print_batch_stats(summary, fail_under)
            else:
                table = Table(title="Retry Summary", box=box.SIMPLE_HEAVY, show_lines=True)
                table.add_column("Persona", style="cyan")
                table.add_column("Score", style="white")
                table.add_column("Result File", style="green")
                table.add_column("Error", style="red")
                for item in summary:
                    p = item.get("persona_name", "")
                    err = item.get("error")
                    if err:
                        table.add_row(p, "-", "-", err)
                    else:
                        s = item.get("score")
                        table.add_row(p, str(s) if s is not None else "?", item.get("result_path", ""), "")
                console.print()
                console.print(table)
                _print_batch_stats(summary, fail_under)
                _print_failed_runs(summary, fail_under)
        fail_under = getattr(args, "fail_under", None)
        if fail_under is not None:
            for item in summary:
                if "error" in item:
                    _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                    return 1
                s = item.get("score")
                if s is not None and int(s) < fail_under:
                    _notify_failure(notify_webhook, f"Safety tester failed: score {s} below --fail-under {fail_under}.", summary, notify_format)
                    return 1
        if fail_under_criteria:
            for item in summary:
                if "error" in item:
                    _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                    return 1
                for cid, min_score in (fail_under_criteria or {}).items():
                    if (item.get("criterion_scores") or {}).get(cid, 0) < min_score:
                        _notify_failure(notify_webhook, f"Safety tester failed: criterion {cid} below threshold.", summary, notify_format)
                        return 1
        _maybe_save_baseline_and_notify_success(args, output_dir, summary, notify_webhook, quiet)
        return 0

    if args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            console.print(f"[bold red]Config file not found:[/bold red] {config_path}")
            return 1

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"[bold red]Failed to parse config JSON:[/bold red] {e}")
            return 1

        if personas_dir is not None:
            personas = _discover_personas_from_dir(personas_dir)
            if not personas:
                console.print("[bold red]No persona JSON files found in --personas-dir.[/bold red]")
                return 1
        else:
            personas = config.get("personas", [])
            if not isinstance(personas, list) or not personas:
                console.print("[bold red]Config must contain a non-empty 'personas' list.[/bold red]")
                return 1
        if personas_override is not None:
            # Filter to only requested personas (match by filename or stem, e.g. passive_ideation or passive_ideation.json)
            allowed = {p.strip() for p in personas_override}
            def _match(p: str) -> bool:
                if p in allowed:
                    return True
                stem = Path(p).stem if "." in p else p
                return stem in allowed or p.replace(".json", "") in allowed
            personas = [p for p in personas if _match(p)]
            if not personas:
                console.print("[bold red]No personas left after --personas filter.[/bold red]")
                return 1
        tags_dir = personas_dir if personas_dir is not None else project_root / "personas"
        personas = _filter_personas_by_tags(personas, persona_tags_requested or [], tags_dir)
        if not personas:
            console.print("[bold red]No personas match --persona-tags.[/bold red]")
            return 1
        personas = sorted(personas)
        shard_arg = getattr(args, "shard", None)
        shard = _parse_shard(shard_arg)
        if shard_arg and not shard:
            console.print("[bold red]Invalid --shard; use N/M with 0 <= N < M (e.g. 0/4).[/bold red]")
            return 1
        if shard:
            personas = _apply_shard(personas, shard)
            if not quiet:
                console.print(f"[dim]Shard {shard[0]}/{shard[1]}: running {len(personas)} persona(s).[/dim]")
        max_runs = getattr(args, "max_runs", None) or defaults.get("max_runs")
        if max_runs is not None and max_runs > 0:
            personas = personas[:max_runs]
            if not quiet:
                console.print(f"[dim]Capped to --max-runs {max_runs}: running {len(personas)} persona(s).[/dim]")

        if getattr(args, "dry_run", False):
            _print_dry_run(
                personas,
                prompts_list,
                criterion_ids,
                len(extra_criterion_specs) if extra_criterion_specs else 0,
                sut_backend,
                sut_model,
                judge_model,
                mock,
            )
            return 0

        run_id = _generate_run_id()
        total_config_runs = len(personas) * (len(prompts_list) if prompts_list else 1)
        progress_msg = (lambda p: f"  Completed: {p}") if (not quiet and total_config_runs > 1) else (lambda p: None)
        summary: list[Dict[str, Any]] = []
        sem = asyncio.Semaphore(parallel) if parallel > 1 else None
        tasks = []
        for persona_name in personas:
            if not isinstance(persona_name, str):
                continue
            if prompts_list:
                for pname, ptext in prompts_list:
                    tasks.append(
                        _run_one(
                            persona_name,
                            args,
                            sut_model,
                            judge_model,
                            mock,
                            output_dir,
                            quiet,
                            write_md,
                            criterion_ids,
                            log_path,
                            extra_criterion_specs,
                            ptext,
                            pname,
                            report_html,
                            sem,
                            sut_backend,
                            sut_options,
                            history_path,
                            run_id=run_id,
                            run_timeout=run_timeout,
                            on_complete_msg=progress_msg(persona_name),
                            judge_backend=judge_backend,
                            judge_temperature=judge_temperature,
                            cache_dir=cache_dir,
                            profile=profile,
                            redact=redact,
                            criterion_weights=criterion_weights,
                        )
                    )
            else:
                tasks.append(
                    _run_one(
                        persona_name,
                        args,
                        sut_model,
                        judge_model,
                        mock,
                        output_dir,
                        quiet,
                        write_md,
                        criterion_ids,
                        log_path,
                        extra_criterion_specs,
                        system_prompt,
                        None,
                        report_html,
                        sem,
                        sut_backend,
                        sut_options,
                        history_path,
                        run_id=run_id,
                        run_timeout=run_timeout,
                        on_complete_msg=progress_msg(persona_name),
                        judge_backend=judge_backend,
                        judge_temperature=judge_temperature,
                        cache_dir=cache_dir,
                        profile=profile,
                        redact=redact,
                        criterion_weights=criterion_weights,
                    )
                )
        if tasks:
            summary = await _gather_with_progress(tasks, quiet)
        else:
            summary = []

        if batch_summary and len(summary) > 1:
            _write_batch_summary(
                output_dir,
                summary,
                write_md=write_md,
                write_csv=write_csv,
                tags_dir=tags_dir,
                fail_under=getattr(args, "fail_under", None),
                run_id=run_id,
            )
        if getattr(args, "junit", None):
            _write_junit(Path(args.junit), summary, getattr(args, "fail_under", None))

        fail_under_cfg = getattr(args, "fail_under", None)
        if not quiet and len(summary) > 1:
            if getattr(args, "failures_only", False):
                _print_failed_runs(summary, fail_under_cfg)
                _print_batch_stats(summary, fail_under_cfg)
            else:
                table = Table(
                    title="Batch Run Summary",
                    box=box.SIMPLE_HEAVY,
                    show_lines=True,
                )
                table.add_column("Persona", style="cyan")
                table.add_column("Score", style="white")
                table.add_column("Result File", style="green")
                table.add_column("Error", style="red")
                for item in summary:
                    persona_name = item.get("persona_name", "")
                    error = item.get("error")
                    if error:
                        table.add_row(persona_name, "-", "-", error)
                    else:
                        score = item.get("score")
                        score_text = _style_score(int(score)) if score is not None else Text("?", style="yellow")
                        result_path = item.get("result_path", "")
                        table.add_row(persona_name, str(score_text), result_path, "")
                console.print()
                console.print(table)
                _print_batch_stats(summary, fail_under_cfg)
                _print_failed_runs(summary, fail_under_cfg)
                _print_tag_summary(summary, tags_dir, fail_under_cfg)

        if prompts_list and len(summary) > 0 and not quiet:
            _print_prompt_comparison_table(summary, prompts_list)

        fail_under = getattr(args, "fail_under", None)
        if fail_under is not None:
            for item in summary:
                if "error" in item:
                    _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                    return 1
                s = item.get("score")
                if s is not None and int(s) < fail_under:
                    if not quiet:
                        console.print(f"[bold red]Score {s} below --fail-under {fail_under}[/bold red]")
                    _notify_failure(notify_webhook, f"Safety tester failed: score {s} below --fail-under {fail_under}.", summary, notify_format)
                    return 1
        if fail_under_criteria:
            for item in summary:
                if "error" in item:
                    _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                    return 1
                scores = item.get("criterion_scores") or {}
                for cid, min_score in fail_under_criteria.items():
                    if scores.get(cid, 0) < min_score:
                        if not quiet:
                            console.print(f"[bold red]Criterion {cid} score {scores.get(cid, 0)} below --fail-under-criteria {cid}={min_score}[/bold red]")
                        _notify_failure(notify_webhook, f"Safety tester failed: criterion {cid} below threshold.", summary, notify_format)
                        return 1
        if compare_baseline:
            for item in summary:
                if "error" in item:
                    return 1
                pname = item.get("persona_name", "")
                if baseline_path_or_dir:
                    bp = Path(baseline_path_or_dir)
                    baseline_path = bp if bp.is_file() else bp / f"baseline_{pname}.json"
                else:
                    baseline_path = output_dir / f"baseline_{pname}.json"
                baseline_scores = _load_baseline(baseline_path)
                if baseline_scores and not _check_baseline(pname, item.get("criterion_scores") or {}, baseline_scores, quiet):
                    _notify_failure(notify_webhook, "Safety tester failed: regression vs baseline.", summary, notify_format)
                    return 1
        _maybe_save_baseline_and_notify_success(args, output_dir, summary, notify_webhook, quiet)
        return 0

    # Single-persona or --personas batch (no config file)
    if personas_dir is not None:
        persona_list = _discover_personas_from_dir(personas_dir)
        if not persona_list:
            console.print("[bold red]No persona JSON files found in --personas-dir.[/bold red]")
            return 1
    elif personas_override is not None:
        persona_list = personas_override
    else:
        persona_list = [args.persona]
    tags_dir = personas_dir if personas_dir is not None else project_root / "personas"
    persona_list = _filter_personas_by_tags(persona_list, persona_tags_requested or [], tags_dir)
    if not persona_list:
        console.print("[bold red]No personas match --persona-tags.[/bold red]")
        return 1
    persona_list = sorted(persona_list)
    shard_arg = getattr(args, "shard", None)
    shard = _parse_shard(shard_arg)
    if shard_arg and not shard:
        console.print("[bold red]Invalid --shard; use N/M with 0 <= N < M (e.g. 0/4).[/bold red]")
        return 1
    if shard:
        persona_list = _apply_shard(persona_list, shard)
        if not quiet:
            console.print(f"[dim]Shard {shard[0]}/{shard[1]}: running {len(persona_list)} persona(s).[/dim]")
    max_runs = getattr(args, "max_runs", None) or defaults.get("max_runs")
    if max_runs is not None and max_runs > 0:
        persona_list = persona_list[:max_runs]
        if not quiet:
            console.print(f"[dim]Capped to --max-runs {max_runs}: running {len(persona_list)} persona(s).[/dim]")

    if getattr(args, "dry_run", False):
        _print_dry_run(
            persona_list,
            prompts_list,
            criterion_ids,
            len(extra_criterion_specs) if extra_criterion_specs else 0,
            sut_backend,
            sut_model,
            judge_model,
            mock,
        )
        return 0

    run_id = _generate_run_id()
    total_runs = len(persona_list) * (len(prompts_list) if prompts_list else 1)
    progress_msg = (lambda p: f"  Completed: {p}") if (not quiet and total_runs > 1) else (lambda p: None)
    sem = asyncio.Semaphore(parallel) if parallel > 1 else None
    tasks = []
    for persona_name in persona_list:
        if prompts_list:
            for pname, ptext in prompts_list:
                tasks.append(
                    _run_one(
                        persona_name,
                        args,
                        sut_model,
                        judge_model,
                        mock,
                        output_dir,
                        quiet,
                        write_md,
                        criterion_ids,
                        log_path,
                        extra_criterion_specs,
                        ptext,
                        pname,
                        report_html,
                        sem,
                        sut_backend,
                        sut_options,
                        history_path,
                        run_id=run_id,
                        run_timeout=run_timeout,
                        on_complete_msg=progress_msg(persona_name),
                        judge_backend=judge_backend,
                        judge_temperature=judge_temperature,
                        cache_dir=cache_dir,
                        profile=profile,
                        redact=redact,
                        criterion_weights=criterion_weights,
                    )
                )
        else:
            tasks.append(
                _run_one(
                    persona_name,
                    args,
                    sut_model,
                    judge_model,
                    mock,
                    output_dir,
                    quiet,
                    write_md,
                    criterion_ids,
                    log_path,
                    extra_criterion_specs,
                    system_prompt,
                    None,
                    report_html,
                    sem,
                    sut_backend,
                    sut_options,
                    history_path,
                    run_id=run_id,
                    run_timeout=run_timeout,
                    on_complete_msg=progress_msg(persona_name),
                    judge_backend=judge_backend,
                    judge_temperature=judge_temperature,
                    cache_dir=cache_dir,
                    profile=profile,
                    redact=redact,
                    criterion_weights=criterion_weights,
                )
            )
    summary = await _gather_with_progress(tasks, quiet) if tasks else []

    if batch_summary and len(summary) > 1:
        _write_batch_summary(
            output_dir,
            summary,
            write_md=write_md,
            write_csv=write_csv,
            tags_dir=tags_dir,
            fail_under=getattr(args, "fail_under", None),
            run_id=run_id,
        )
    if getattr(args, "junit", None) and summary:
        _write_junit(Path(args.junit), summary, getattr(args, "fail_under", None))

    fail_under = getattr(args, "fail_under", None)
    if not quiet and len(summary) > 1:
        if getattr(args, "failures_only", False):
            _print_failed_runs(summary, fail_under)
            _print_batch_stats(summary, fail_under)
        else:
            table = Table(
                title="Batch Run Summary",
                box=box.SIMPLE_HEAVY,
                show_lines=True,
            )
            table.add_column("Persona", style="cyan")
            show_severity = any((item.get("persona_meta") or {}).get("severity") for item in summary)
            if show_severity:
                table.add_column("Severity", style="dim")
            table.add_column("Score", style="white")
            table.add_column("Result File", style="green")
            table.add_column("Error", style="red")
            for item in summary:
                persona_name = item.get("persona_name", "")
                error = item.get("error")
                sev = (item.get("persona_meta") or {}).get("severity") or ""
                if error:
                    row = [persona_name]
                    if show_severity:
                        row.append(sev)
                    row.extend(["-", "-", error])
                    table.add_row(*row)
                else:
                    score = item.get("score")
                    score_text = _style_score(int(score)) if score is not None else Text("?", style="yellow")
                    row = [persona_name]
                    if show_severity:
                        row.append(sev)
                    row.extend([str(score_text), item.get("result_path", ""), ""])
                    table.add_row(*row)
            console.print()
            console.print(table)
            _print_batch_stats(summary, fail_under)
            _print_failed_runs(summary, fail_under)
            if profile and len(summary) >= 1:
                _print_profile_table(summary)
            _print_tag_summary(summary, tags_dir, fail_under)
        if getattr(args, "ndjson", False) and summary:
            for item in summary:
                print(json.dumps(item, ensure_ascii=False))

    if prompts_list and len(summary) > 0 and not quiet:
        _print_prompt_comparison_table(summary, prompts_list)

    fail_under = getattr(args, "fail_under", None)
    if fail_under is not None:
        for item in summary:
            if "error" in item:
                _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                return 1
            s = item.get("score")
            if s is not None and int(s) < fail_under:
                if not quiet:
                    console.print(f"[bold red]Score {s} below --fail-under {fail_under}[/bold red]")
                _notify_failure(notify_webhook, f"Safety tester failed: score {s} below --fail-under {fail_under}.", summary, notify_format)
                return 1
    if fail_under_criteria:
        for item in summary:
            if "error" in item:
                _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                return 1
            scores = item.get("criterion_scores") or {}
            for cid, min_score in fail_under_criteria.items():
                if scores.get(cid, 0) < min_score:
                    if not quiet:
                        console.print(f"[bold red]Criterion {cid} score {scores.get(cid, 0)} below threshold {min_score}[/bold red]")
                    _notify_failure(notify_webhook, f"Safety tester failed: criterion {cid} below threshold.", summary, notify_format)
                    return 1
    if compare_baseline:
        for item in summary:
            if "error" in item:
                _notify_failure(notify_webhook, "Safety tester failed (run error).", summary, notify_format)
                return 1
            pname = item.get("persona_name", "")
            if baseline_path_or_dir:
                bp = Path(baseline_path_or_dir)
                baseline_path = bp if bp.is_file() else bp / f"baseline_{pname}.json"
            else:
                baseline_path = output_dir / f"baseline_{pname}.json"
            baseline_scores = _load_baseline(baseline_path)
            if baseline_scores and not _check_baseline(pname, item.get("criterion_scores") or {}, baseline_scores, quiet):
                _notify_failure(notify_webhook, "Safety tester failed: regression vs baseline.", summary, notify_format)
                return 1
    _maybe_save_baseline_and_notify_success(args, output_dir, summary, notify_webhook, quiet)
    return 0


def _list_personas() -> None:
    """Print persona JSON files in personas/ (exclude batch_config, example_criterion, persona_tags)."""
    project_root = Path(__file__).resolve().parent
    personas_dir = project_root / "personas"
    if not personas_dir.is_dir():
        console.print("No personas/ directory found.")
        return
    exclude = _NON_PERSONA_JSON
    files = sorted(p for p in personas_dir.glob("*.json") if p.name not in exclude)
    console.print("Available personas:")
    for p in files:
        console.print(f"  {p.name}")
    if not files:
        console.print("  (none)")


def _list_tags(tags_dir: Path) -> None:
    """Print tags from persona_tags.json and which personas have each tag."""
    tag_map = _load_persona_tags(tags_dir)
    if not tag_map:
        console.print("No persona_tags.json found or it is empty.")
        console.print(f"Expected: {tags_dir / 'persona_tags.json'}")
        return
    # Invert: tag -> [personas]
    by_tag: Dict[str, List[str]] = {}
    for persona, tags in tag_map.items():
        for t in tags if isinstance(tags, list) else []:
            t = (t or "").strip()
            if t:
                by_tag.setdefault(t, []).append(persona)
    console.print("Tags and personas (from persona_tags.json):")
    for tag in sorted(by_tag.keys()):
        console.print(f"  [bold]{tag}[/bold]")
        for p in sorted(by_tag[tag]):
            console.print(f"    {p}")
    untagged = [p for p in tag_map if not (tag_map.get(p) or [])]
    if untagged:
        console.print("  (no tag):")
        for p in sorted(untagged):
            console.print(f"    {p}")


def _run_validate_personas(args: argparse.Namespace) -> int:
    """Load each persona in personas/ (or --personas-dir), validate schema; return 0 if all OK else 1."""
    project_root = Path(__file__).resolve().parent
    personas_dir = Path(args.personas_dir) if getattr(args, "personas_dir", None) else (project_root / "personas")
    if not personas_dir.is_dir():
        console.print(f"[bold red]Not a directory: {personas_dir}[/bold red]")
        return 1
    names = _discover_personas_from_dir(personas_dir)
    if not names:
        console.print("[yellow]No persona JSON files found.[/yellow]")
        return 0
    failed = 0
    for name in sorted(names):
        path = personas_dir / name if (personas_dir / name).is_file() else resolve_persona_path(name)
        try:
            load_persona(path)
            console.print(f"  [green]OK[/green] {name}")
        except ConversationError as e:
            console.print(f"  [red]FAIL[/red] {name}: {e}")
            failed += 1
    if failed:
        console.print(f"\n[bold red]{failed} persona(s) failed validation.[/bold red]")
        return 1
    console.print(f"\n[green]All {len(names)} persona(s) valid.[/green]")
    return 0


def _print_tag_summary(
    summary: List[Dict[str, Any]],
    tags_dir: Path,
    fail_under: Optional[int],
) -> None:
    """Print a short summary of pass/fail counts by tag (when persona_tags.json exists)."""
    tag_map = _load_persona_tags(tags_dir)
    if not tag_map:
        return
    by_tag: Dict[str, List[Dict[str, Any]]] = {}
    for item in summary:
        pname = item.get("persona_name", "")
        key = pname if pname.endswith(".json") else f"{pname}.json"
        tags = tag_map.get(key) or tag_map.get(pname) or []
        for t in (tags if isinstance(tags, list) else []) or []:
            t = (t or "").strip()
            if t:
                by_tag.setdefault(t, []).append(item)
    if not by_tag:
        return
    console.print()
    table = Table(title="Summary by tag", box=box.SIMPLE, show_header=True)
    table.add_column("Tag", style="cyan")
    table.add_column("Passed", style="green")
    table.add_column("Failed", style="red")
    table.add_column("Total", style="white")
    for tag in sorted(by_tag.keys()):
        items = by_tag[tag]
        passed = sum(
            1
            for i in items
            if not i.get("error")
            and (fail_under is None or (i.get("score") is not None and int(i["score"]) >= fail_under))
        )
        failed = len(items) - passed
        table.add_row(tag, str(passed), str(failed), str(len(items)))
    console.print(table)


def _print_batch_stats(summary: List[Dict[str, Any]], fail_under: Optional[int]) -> None:
    """Print pass rate and min/max/mean score for batch summary."""
    if not summary:
        return
    scores = [int(item["score"]) for item in summary if item.get("score") is not None and item.get("error") is None]
    passed = sum(
        1
        for item in summary
        if not item.get("error")
        and (fail_under is None or (item.get("score") is not None and int(item["score"]) >= fail_under))
    )
    total = len(summary)
    console.print()
    console.print(f"[bold]Batch stats:[/bold] {passed}/{total} passed" + (f" (fail-under {fail_under})" if fail_under is not None else ""))
    if scores:
        console.print(f"  Score — min: {min(scores)}, max: {max(scores)}, mean: {sum(scores) / len(scores):.2f}")
    errors = sum(1 for item in summary if item.get("error"))
    if errors:
        console.print(f"  Errors: {errors}")


def _print_profile_table(summary: List[Dict[str, Any]]) -> None:
    """Print timing per run (SUT and judge seconds) and total."""
    rows = []
    total_sut = 0.0
    total_judge = 0.0
    for item in summary:
        name = item.get("persona_name", "?")
        if item.get("run_label"):
            name = f"{name}({item.get('run_label')})"
        sut_s = item.get("sut_seconds")
        judge_s = item.get("judge_seconds")
        if sut_s is not None:
            total_sut += sut_s
        if judge_s is not None:
            total_judge += judge_s
        rows.append((name, sut_s if sut_s is not None else "-", judge_s if judge_s is not None else "-"))
    if not rows:
        return
    console.print()
    table = Table(title="Profile (seconds)", box=box.SIMPLE, show_header=True)
    table.add_column("Persona", style="cyan")
    table.add_column("SUT", style="white")
    table.add_column("Judge", style="white")
    for name, sut_s, judge_s in rows:
        table.add_row(name, str(sut_s), str(judge_s))
    table.add_row("[bold]Total[/bold]", f"{total_sut:.2f}", f"{total_judge:.2f}")
    console.print(table)


def _print_failed_runs(summary: List[Dict[str, Any]], fail_under: Optional[int]) -> None:
    """Print only failed runs (error or score below fail_under) with reason."""
    failed = []
    for item in summary:
        err = item.get("error")
        if err:
            failed.append((item.get("persona_name", "?"), f"error: {err}"))
            continue
        score = item.get("score")
        if fail_under is not None and score is not None and int(score) < fail_under:
            failed.append((item.get("persona_name", "?"), f"score {score} below {fail_under}"))
    if not failed:
        return
    console.print()
    console.print("[bold red]Failed runs[/bold red]")
    for name, reason in failed:
        console.print(f"  • {name}: {reason}")


def _print_dry_run(
    persona_names: List[str],
    prompts_list: Optional[List[Tuple[str, str]]],
    criterion_ids: Optional[List[str]],
    extra_criteria_count: int,
    sut_backend: str,
    sut_model: str,
    judge_model: str,
    mock: bool,
) -> None:
    """Print what would run and exit (used with --dry-run)."""
    console.print("[bold cyan]Dry run — no API calls[/bold cyan]")
    console.print(f"  SUT backend: {sut_backend}")
    console.print(f"  SUT model:   {sut_model}")
    console.print(f"  Judge model: {judge_model}")
    console.print(f"  Mock:        {mock}")
    criteria = criterion_ids if criterion_ids else ["(all built-in)"]
    if extra_criteria_count:
        criteria = list(criteria) + [f"+ {extra_criteria_count} from file"]
    console.print(f"  Criteria:    {criteria}")
    if prompts_list:
        console.print(f"  SUT prompts: {[p[0] for p in prompts_list]}")
    n_runs = len(persona_names) * (len(prompts_list) if prompts_list else 1)
    console.print(f"  Personas:   {persona_names}")
    console.print(f"  Total runs:  {n_runs}")


def _list_criteria() -> None:
    """Print criterion IDs and short description."""
    console.print("Available criteria:")
    for c in CRITERIA:
        text = c["criterion"]
        short = (text[:60] + "...") if len(text) > 60 else text
        console.print(f"  {c['id']}: {short}")
    console.print("  (use --criteria id1,id2 to run a subset)")


def _get_version() -> str:
    """Read version from pyproject.toml in the same directory as this file."""
    import re
    project_root = Path(__file__).resolve().parent
    pyproject = project_root / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            return m.group(1)
    return "0.0.0"


def main() -> None:
    global console
    args = parse_args()
    if getattr(args, "no_color", False):
        console = Console(no_color=True)
    if getattr(args, "version", False):
        print(_get_version())
        raise SystemExit(0)
    if getattr(args, "health_check", False):
        # Run one mock persona; exit 0 if pipeline works
        args.mock = True
        args.quiet = True
        args.persona = "passive_ideation.json"
        args.config = None
        args.personas = None
        exit_code = asyncio.run(main_async(args))
        raise SystemExit(exit_code)
    if getattr(args, "list_personas", False):
        _list_personas()
        raise SystemExit(0)
    if getattr(args, "list_tags", False):
        _list_tags(Path(__file__).resolve().parent / "personas")
        raise SystemExit(0)
    if getattr(args, "list_criteria", False):
        _list_criteria()
        raise SystemExit(0)
    if getattr(args, "validate_personas", False):
        exit_code = _run_validate_personas(args)
        raise SystemExit(exit_code)
    exit_code = asyncio.run(main_async(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
