import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from runner import ConversationError, load_persona, run_conversation
from judge import CRITERIA, score_all_criteria


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


def save_result_json(
    results_dir: Path,
    persona_name: str,
    conversation: Dict[str, Any],
    judge_results: List[Dict[str, Any]],
    timestamp: Optional[str] = None,
) -> Path:
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_persona = persona_name.replace(" ", "_")
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


def _mock_judge_all() -> List[Dict[str, Any]]:
    """Return one mock judge result per criterion."""
    rationale = (
        "MOCK MODE: This is a fake judge response for testing the pipeline without calling the "
        "Anthropic API. No real clinical evaluation was performed."
    )
    results = []
    for spec in CRITERIA:
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
) -> Dict[str, Any]:
    persona_path = resolve_persona_path(persona_name)

    if mock:
        conversation = _mock_conversation(persona_name)
    else:
        try:
            conversation = await run_conversation(persona_path, model=sut_model)
        except ConversationError as e:
            console.print(f"[bold red]Conversation error for persona '{persona_name}':[/bold red] {e}")
            return {"persona_name": persona_name, "error": str(e)}

    if not quiet:
        console.rule(f"[bold cyan]Persona: {conversation.get('persona_name', persona_name)}[/bold cyan]")
        print_conversation(conversation)

    if mock:
        judge_results = _mock_judge_all()
    else:
        try:
            judge_results = await score_all_criteria(
                conversation["conversation_for_judge"],
                model=judge_model,
            )
        except Exception as e:
            console.print(f"[bold red]Judge error for persona '{persona_name}':[/bold red] {e}")
            return {
                "persona_name": conversation.get("persona_name", persona_name),
                "error": str(e),
            }

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

    if not quiet:
        console.print(f"\n[bold green]Results saved to:[/bold green] {result_path}")
    else:
        criterion_scores = {r.get("criterion_id", i): r.get("parsed", {}).get("score", 0) for i, r in enumerate(judge_results)}
        final_score = min(criterion_scores.values()) if criterion_scores else 0
        console.print(f"persona={persona_display} score={final_score} criterion_scores={criterion_scores} path={result_path}")

    criterion_scores = {r.get("criterion_id", f"c{i}"): r.get("parsed", {}).get("score", 0) for i, r in enumerate(judge_results)}
    final_score = min(criterion_scores.values()) if criterion_scores else 0

    return {
        "persona_name": persona_display,
        "score": final_score,
        "criterion_scores": criterion_scores,
        "result_path": str(result_path),
    }


async def main_async(args: argparse.Namespace) -> int:
    sut_model = args.sut_model or os.getenv("SUT_MODEL", "claude-haiku-4-5-20251001")
    judge_model = args.judge_model or os.getenv("JUDGE_MODEL", "claude-sonnet-4-6")
    mock_env = os.getenv("SAFETY_TESTER_MOCK", "").lower() in {"1", "true", "yes"}
    mock = args.mock or mock_env
    output_dir = get_output_dir(args)
    quiet = getattr(args, "quiet", False)
    write_md = getattr(args, "md", False)

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

        summary: list[Dict[str, Any]] = []
        for persona_name in personas:
            if not isinstance(persona_name, str):
                console.print(f"[bold yellow]Skipping non-string persona entry in config:[/bold yellow] {persona_name}")
                continue

            result = await run_single_persona(
                persona_name,
                verbose=args.verbose,
                sut_model=sut_model,
                judge_model=judge_model,
                mock=mock,
                output_dir=output_dir,
                quiet=quiet,
                write_md=write_md,
            )
            summary.append(result)

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
        return 0

    await run_single_persona(
        args.persona,
        verbose=args.verbose,
        sut_model=sut_model,
        judge_model=judge_model,
        mock=mock,
        output_dir=output_dir,
        quiet=quiet,
        write_md=write_md,
    )
    return 0


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(main_async(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
