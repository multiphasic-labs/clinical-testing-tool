import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from sut_backends import ConversationError, get_backend

# Re-export for callers that import from runner
__all__ = ["ConversationError", "load_persona", "run_conversation"]


def _validate_persona_turns(data: List[Dict[str, Any]], persona_path: Path) -> None:
    """Validate each turn has turn, message, expected_behavior and turns are ordered. Raises ConversationError."""
    if not data:
        raise ConversationError(f"Persona file is empty: {persona_path}")
    seen = set()
    for i, turn in enumerate(data):
        if not isinstance(turn, dict):
            raise ConversationError(
                f"Persona {persona_path.name}: turn at index {i} must be an object, got {type(turn).__name__}."
            )
        for key in ("turn", "message", "expected_behavior"):
            if key not in turn:
                raise ConversationError(
                    f"Persona {persona_path.name}: turn at index {i} missing required field '{key}'."
                )
        t = turn["turn"]
        if t in seen:
            raise ConversationError(
                f"Persona {persona_path.name}: duplicate turn number {t} at index {i}."
            )
        seen.add(t)
    ordered = sorted(seen)
    expected = list(range(1, len(data) + 1))
    if ordered != expected:
        raise ConversationError(
            f"Persona {persona_path.name}: turn numbers must be 1..N with no gaps, got {ordered}."
        )


def load_persona(persona_path: Path) -> List[Dict[str, Any]]:
    if not persona_path.exists():
        raise ConversationError(f"Persona file not found: {persona_path}")

    try:
        with persona_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConversationError(f"Failed to parse persona JSON: {e}") from e

    if not isinstance(data, list):
        raise ConversationError("Persona JSON must be a list of turns.")

    _validate_persona_turns(data, persona_path)
    return data


async def run_conversation(
    persona_path: Path,
    model: str = "claude-haiku-4-5-20251001",
    system_prompt: Optional[str] = None,
    sut_backend: str = "anthropic",
    sut_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the scripted conversation against the system under test.

    sut_backend: "anthropic" | "openai" | "custom"
    sut_options: optional dict passed to the backend (e.g. endpoint, api_key for custom).

    Returns a structured dictionary containing:
      - persona_name
      - turns: list of {turn, user_message, expected_behavior, system_response}
      - conversation_for_judge: list of {role, turn, content} for the judge
    """
    adapter = get_backend(sut_backend)
    opts = sut_options or {}

    persona = load_persona(persona_path)

    turns_output: List[Dict[str, Any]] = []
    # Simple message list: {role, content} (content = string)
    messages: List[Dict[str, Any]] = []

    for turn in persona:
        user_message = str(turn.get("message", ""))
        expected_behavior = str(turn.get("expected_behavior", ""))
        turn_index = turn.get("turn")

        messages.append({"role": "user", "content": user_message})

        try:
            from rate_limit import acquire as rate_limit_acquire, is_active as rate_limit_active
            if rate_limit_active():
                await rate_limit_acquire()
        except ImportError:
            pass
        system_response = await adapter(
            messages,
            system_prompt=system_prompt,
            model=model,
            **opts,
        )

        messages.append({"role": "assistant", "content": system_response})

        turns_output.append(
            {
                "turn": turn_index,
                "user_message": user_message,
                "expected_behavior": expected_behavior,
                "system_response": system_response,
            }
        )

    conversation_for_judge: List[Dict[str, Any]] = []
    for turn in turns_output:
        conversation_for_judge.append(
            {
                "role": "user",
                "turn": turn["turn"],
                "content": turn["user_message"],
            }
        )
        conversation_for_judge.append(
            {
                "role": "assistant",
                "turn": turn["turn"],
                "content": turn["system_response"],
            }
        )

    return {
        "persona_name": persona_path.stem,
        "turns": turns_output,
        "conversation_for_judge": conversation_for_judge,
    }
