import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from runner import ConversationError, load_persona, run_conversation
from judge import CRITERIA, get_criteria_specs, score_all_criteria


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
        help="Run in mock mode without calling the Anthropic API (uses canned responses).",
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
    return parser.parse_args()


def resolve_persona_path(persona_arg: str) -> Path:
    candidate = Path(persona_arg)
    if candidate.is_file():
        return candidate

    project_root = Path(__file__).resolve().parent
    persona_path = project_root / "personas" / persona_arg
    return persona_path


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


def save_result_json(
    results_dir: Path,
    persona_name: str,
    conversation: Dict[str, Any],
    judge_results: List[Dict[str, Any]],
    timestamp: Optional[str] = None,
    run_label: Optional[str] = None,
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
    final_score = min(criterion_scores.values()) if criterion_scores else 0

    payload = {
        "timestamp_utc": timestamp,
        "persona_name": persona_name,
        "conversation": conversation,
        "judge_results": judge_results,
        "criterion_scores": criterion_scores,
        "final_score": final_score,
    }

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
) -> Dict[str, Any]:
    persona_path = resolve_persona_path(persona_name)

    if mock:
        conversation = _mock_conversation(persona_name)
    else:
        try:
            conversation = await run_conversation(
                persona_path, model=sut_model, system_prompt=system_prompt
            )
        except ConversationError as e:
            console.print(f"[bold red]Conversation error for persona '{persona_name}':[/bold red] {e}")
            _log_line(log_path, f"{datetime.utcnow().isoformat()}Z\t{persona_name}\terror=ConversationError\t{e}")
            return {"persona_name": persona_name, "error": str(e)}

    if not quiet:
        console.rule(f"[bold cyan]Persona: {conversation.get('persona_name', persona_name)}[/bold cyan]")
        print_conversation(conversation)

    if mock:
        judge_results = _mock_judge_all(criterion_ids=criterion_ids, extra_specs=extra_criterion_specs)
    else:
        try:
            judge_results = await score_all_criteria(
                conversation["conversation_for_judge"],
                model=judge_model,
                criterion_ids=criterion_ids,
                extra_specs=extra_criterion_specs,
            )
        except Exception as e:
            console.print(f"[bold red]Judge error for persona '{persona_name}':[/bold red] {e}")
            pname = conversation.get("persona_name", persona_name)
            _log_line(log_path, f"{datetime.utcnow().isoformat()}Z\t{pname}\terror=JudgeError\t{e}")
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


def _log_line(log_path: Optional[Path], line: str) -> None:
    """Append a line to the log file if --log was set."""
    if not log_path:
        return
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _write_batch_summary(
    output_dir: Path,
    summary: List[Dict[str, Any]],
    write_md: bool,
) -> None:
    """Write batch_summary_TIMESTAMP.json and optionally .md to output_dir."""
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rows = []
    for item in summary:
        rows.append({
            "persona": item.get("persona_name", ""),
            "score": item.get("score"),
            "error": item.get("error"),
            "result_path": item.get("result_path"),
            "criterion_scores": item.get("criterion_scores"),
        })
    path = output_dir / f"batch_summary_{timestamp}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump({"timestamp_utc": timestamp, "runs": rows}, f, indent=2, ensure_ascii=False)
    if write_md:
        md_path = output_dir / f"batch_summary_{timestamp}.md"
        lines = [f"# Batch summary — {timestamp}", ""]
        for r in rows:
            lines.append(f"## {r['persona']}")
            lines.append(f"- **Score:** {r['score']}")
            if r.get("error"):
                lines.append(f"- **Error:** {r['error']}")
            if r.get("result_path"):
                lines.append(f"- **Result:** {r['result_path']}")
            lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")


async def main_async(args: argparse.Namespace) -> int:
    sut_model = args.sut_model or os.getenv("SUT_MODEL", "claude-haiku-4-5-20251001")
    judge_model = args.judge_model or os.getenv("JUDGE_MODEL", "claude-sonnet-4-6")
    mock_env = os.getenv("SAFETY_TESTER_MOCK", "").lower() in {"1", "true", "yes"}
    mock = args.mock or mock_env
    output_dir = get_output_dir(args)
    quiet = getattr(args, "quiet", False)
    write_md = getattr(args, "md", False)
    criterion_ids = _parse_list_arg(getattr(args, "criteria", None))
    personas_override = _parse_list_arg(getattr(args, "personas", None))
    log_path = None
    if getattr(args, "log", None):
        log_path = Path(args.log)
    batch_summary = getattr(args, "batch_summary", False)

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

    extra_criterion_specs: Optional[List[Dict[str, Any]]] = None
    if getattr(args, "criterion_file", None):
        try:
            extra_criterion_specs = _load_criterion_file(Path(args.criterion_file))
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[bold red]Criterion file: {e}[/bold red]")
            return 1
    if criterion_ids:
        try:
            get_criteria_specs(criterion_ids, extra_criterion_specs)
        except ValueError as e:
            console.print(f"[bold red]{e}[/bold red]")
            return 1

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

        summary: list[Dict[str, Any]] = []
        for persona_name in personas:
            if not isinstance(persona_name, str):
                console.print(f"[bold yellow]Skipping non-string persona entry in config:[/bold yellow] {persona_name}")
                continue

            if prompts_list:
                for pname, ptext in prompts_list:
                    result = await run_single_persona(
                        persona_name,
                        verbose=args.verbose,
                        sut_model=sut_model,
                        judge_model=judge_model,
                        mock=mock,
                        output_dir=output_dir,
                        quiet=quiet,
                        write_md=write_md,
                        system_prompt=ptext,
                        criterion_ids=criterion_ids,
                        log_path=log_path,
                        extra_criterion_specs=extra_criterion_specs,
                        run_label=pname,
                        report_html=report_html,
                    )
                    summary.append(result)
            else:
                result = await run_single_persona(
                    persona_name,
                    verbose=args.verbose,
                    sut_model=sut_model,
                    judge_model=judge_model,
                    mock=mock,
                    output_dir=output_dir,
                    quiet=quiet,
                    write_md=write_md,
                    system_prompt=system_prompt,
                    criterion_ids=criterion_ids,
                    log_path=log_path,
                    extra_criterion_specs=extra_criterion_specs,
                    report_html=report_html,
                )
                summary.append(result)

        if batch_summary and len(summary) > 1:
            _write_batch_summary(output_dir, summary, write_md=write_md)

        if not quiet:
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

        if prompts_list and len(summary) > 0 and not quiet:
            _print_prompt_comparison_table(summary, prompts_list)

        fail_under = getattr(args, "fail_under", None)
        if fail_under is not None:
            for item in summary:
                if "error" in item:
                    return 1
                s = item.get("score")
                if s is not None and int(s) < fail_under:
                    if not quiet:
                        console.print(f"[bold red]Score {s} below --fail-under {fail_under}[/bold red]")
                    return 1
        if fail_under_criteria:
            for item in summary:
                if "error" in item:
                    return 1
                scores = item.get("criterion_scores") or {}
                for cid, min_score in fail_under_criteria.items():
                    if scores.get(cid, 0) < min_score:
                        if not quiet:
                            console.print(f"[bold red]Criterion {cid} score {scores.get(cid, 0)} below --fail-under-criteria {cid}={min_score}[/bold red]")
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
                    return 1
        return 0

    # Single-persona or --personas batch (no config file)
    if personas_override is not None:
        persona_list = personas_override
    else:
        persona_list = [args.persona]

    summary = []
    for persona_name in persona_list:
        if prompts_list:
            for pname, ptext in prompts_list:
                result = await run_single_persona(
                    persona_name,
                    verbose=args.verbose,
                    sut_model=sut_model,
                    judge_model=judge_model,
                    mock=mock,
                    output_dir=output_dir,
                    quiet=quiet,
                    write_md=write_md,
                    system_prompt=ptext,
                    criterion_ids=criterion_ids,
                    log_path=log_path,
                    extra_criterion_specs=extra_criterion_specs,
                    run_label=pname,
                    report_html=report_html,
                )
                summary.append(result)
        else:
            result = await run_single_persona(
                persona_name,
                verbose=args.verbose,
                sut_model=sut_model,
                judge_model=judge_model,
                mock=mock,
                output_dir=output_dir,
                quiet=quiet,
                write_md=write_md,
                system_prompt=system_prompt,
                criterion_ids=criterion_ids,
                log_path=log_path,
                extra_criterion_specs=extra_criterion_specs,
                report_html=report_html,
            )
            summary.append(result)

    if batch_summary and len(summary) > 1:
        _write_batch_summary(output_dir, summary, write_md=write_md)

    if not quiet and len(summary) > 1:
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
                table.add_row(persona_name, str(score_text), item.get("result_path", ""), "")
        console.print()
        console.print(table)

    if prompts_list and len(summary) > 0 and not quiet:
        _print_prompt_comparison_table(summary, prompts_list)

    fail_under = getattr(args, "fail_under", None)
    if fail_under is not None:
        for item in summary:
            if "error" in item:
                return 1
            s = item.get("score")
            if s is not None and int(s) < fail_under:
                if not quiet:
                    console.print(f"[bold red]Score {s} below --fail-under {fail_under}[/bold red]")
                return 1
    if fail_under_criteria:
        for item in summary:
            if "error" in item:
                return 1
            scores = item.get("criterion_scores") or {}
            for cid, min_score in fail_under_criteria.items():
                if scores.get(cid, 0) < min_score:
                    if not quiet:
                        console.print(f"[bold red]Criterion {cid} score {scores.get(cid, 0)} below threshold {min_score}[/bold red]")
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
                return 1
    return 0


def _list_personas() -> None:
    """Print persona JSON files in personas/ (exclude batch_config and example criterion)."""
    project_root = Path(__file__).resolve().parent
    personas_dir = project_root / "personas"
    if not personas_dir.is_dir():
        console.print("No personas/ directory found.")
        return
    exclude = {"batch_config.json", "example_criterion.json"}
    files = sorted(p for p in personas_dir.glob("*.json") if p.name not in exclude)
    console.print("Available personas:")
    for p in files:
        console.print(f"  {p.name}")
    if not files:
        console.print("  (none)")


def _list_criteria() -> None:
    """Print criterion IDs and short description."""
    console.print("Available criteria:")
    for c in CRITERIA:
        text = c["criterion"]
        short = (text[:60] + "...") if len(text) > 60 else text
        console.print(f"  {c['id']}: {short}")
    console.print("  (use --criteria id1,id2 to run a subset)")


def main() -> None:
    args = parse_args()
    if getattr(args, "list_personas", False):
        _list_personas()
        raise SystemExit(0)
    if getattr(args, "list_criteria", False):
        _list_criteria()
        raise SystemExit(0)
    exit_code = asyncio.run(main_async(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
