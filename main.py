import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from runner import ConversationError, load_persona, run_conversation
from judge import score_conversation


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
    return parser.parse_args()


def resolve_persona_path(persona_arg: str) -> Path:
    candidate = Path(persona_arg)
    if candidate.is_file():
        return candidate

    project_root = Path(__file__).resolve().parent
    persona_path = project_root / "personas" / persona_arg
    return persona_path


def ensure_results_dir() -> Path:
    project_root = Path(__file__).resolve().parent
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def save_result_json(
    results_dir: Path,
    persona_name: str,
    criterion: str,
    conversation: Dict[str, Any],
    judge_result: Dict[str, Any],
) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_persona = persona_name.replace(" ", "_")
    filename = f"{timestamp}_{safe_persona}.json"
    path = results_dir / filename

    payload = {
        "timestamp_utc": timestamp,
        "persona_name": persona_name,
        "criterion": criterion,
        "conversation": conversation,
        "judge": judge_result,
        "final_score": judge_result.get("parsed", {}).get("score"),
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

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

    score_text = _style_score(score)

    header = Panel(
        Text("AI Mental Health Safety Evaluation", style="bold white"),
        style="bold blue",
    )
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
        # Simple canned assistant response referencing expected behavior.
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


def _mock_judge(conversation: Dict[str, Any], criterion: str) -> Dict[str, Any]:
    rationale = (
        "MOCK MODE: This is a fake judge response for testing the pipeline without calling the "
        "Anthropic API. No real clinical evaluation was performed."
    )
    parsed = {
        "score": 2,
        "rationale": rationale,
        "critical_failures": [],
        "positive_behaviors": [
            "Mock mode always returns a passing score to verify plumbing.",
        ],
    }
    raw_text = json.dumps(parsed, indent=2)
    return {
        "raw_text": raw_text,
        "parsed": parsed,
        "criterion": criterion,
    }


async def run_single_persona(
    persona_name: str,
    verbose: bool,
    sut_model: str,
    judge_model: str,
    mock: bool,
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

    console.rule(f"[bold cyan]Persona: {conversation.get('persona_name', persona_name)}[/bold cyan]")
    print_conversation(conversation)

    if mock:
        judge_result = _mock_judge(conversation, criterion="MOCK_CRITERION")
    else:
        try:
            judge_result = await score_conversation(
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
        console.print("\n[bold magenta]Raw judge response:[/bold magenta]")
        console.print(judge_result.get("raw_text", ""))
        console.print()

    print_results(judge_result)

    results_dir = ensure_results_dir()
    result_path = save_result_json(
        results_dir=results_dir,
        persona_name=conversation.get("persona_name", persona_name),
        criterion=judge_result.get("criterion", ""),
        conversation=conversation,
        judge_result=judge_result,
    )

    console.print(f"\n[bold green]Results saved to:[/bold green] {result_path}")

    parsed = judge_result.get("parsed", {})
    score = int(parsed.get("score", 0))

    return {
        "persona_name": conversation.get("persona_name", persona_name),
        "score": score,
        "result_path": str(result_path),
    }


async def main_async(args: argparse.Namespace) -> int:
    # Determine model configuration and mock mode.
    sut_model = args.sut_model or os.getenv("SUT_MODEL", "claude-haiku-4-5-20251001")
    judge_model = args.judge_model or os.getenv("JUDGE_MODEL", "claude-sonnet-4-6")
    mock_env = os.getenv("SAFETY_TESTER_MOCK", "").lower() in {"1", "true", "yes"}
    mock = args.mock or mock_env

    # If a config file is provided, run all personas listed there in sequence.
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
            )
            summary.append(result)

        # Print a compact summary table for the batch run.
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

    # Single persona mode (default).
    _ = await run_single_persona(
        args.persona,
        verbose=args.verbose,
        sut_model=sut_model,
        judge_model=judge_model,
        mock=mock,
    )
    return 0


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(main_async(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

