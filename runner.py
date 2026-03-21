import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from sut_backends import ConversationError, get_backend

# Placeholders use Mustache-style double braces: {{variable_name}}
_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z][a-zA-Z0-9_]*)\s*\}\}")

# Private-use chars so literal braces never collide with real user text
_LIT_OPEN = "\ue000"
_LIT_CLOSE = "\ue001"
# In JSON use "\\{{" and "\\}}" in strings → one backslash + braces in the loaded text
_LITERAL_OPEN_RE = re.compile(r"\\\{\{")
_LITERAL_CLOSE_RE = re.compile(r"\\\}\}")


def _protect_literal_braces(text: str) -> str:
    """Replace \\{{ and \\}} so they are not treated as template placeholders."""
    t = _LITERAL_OPEN_RE.sub(_LIT_OPEN, text)
    return _LITERAL_CLOSE_RE.sub(_LIT_CLOSE, t)


def _unprotect_literal_braces(text: str) -> str:
    return text.replace(_LIT_OPEN, "{{").replace(_LIT_CLOSE, "}}")

# Re-export for callers that import from runner
__all__ = [
    "ConversationError",
    "load_persona",
    "load_persona_metadata",
    "run_conversation",
    "substitute_persona_placeholders",
    "merge_persona_variable_defaults",
    "collect_persona_placeholders",
    "lint_persona_template_file",
]


def collect_persona_placeholders(turns: List[Dict[str, Any]]) -> Set[str]:
    """Return set of placeholder names used in message and expected_behavior strings."""
    names: Set[str] = set()
    for turn in turns:
        for key in ("message", "expected_behavior"):
            text = _protect_literal_braces(str(turn.get(key, "")))
            names.update(m.group(1) for m in _PLACEHOLDER_RE.finditer(text))
    return names


def merge_persona_variable_defaults(meta: Dict[str, Any], override: Optional[Dict[str, str]]) -> Dict[str, str]:
    """
    Merge meta.variables (defaults from persona file) with override (CLI or batch instance).
    Later keys win. All values are stringified.
    """
    defaults: Dict[str, str] = {}
    raw = meta.get("variables")
    if isinstance(raw, dict):
        for k, v in raw.items():
            defaults[str(k)] = str(v)
    merged = {**defaults}
    if override:
        for k, v in override.items():
            merged[str(k)] = str(v)
    return merged


def substitute_persona_placeholders(text: str, variables: Dict[str, str]) -> str:
    """Replace {{name}} placeholders; raise ConversationError if a name is missing."""

    def repl(m: re.Match[str]) -> str:
        key = m.group(1)
        if key not in variables:
            raise ConversationError(
                f"Missing value for persona placeholder '{{{{{key}}}}}' (provided keys: {sorted(variables.keys())})"
            )
        return variables[key]

    t = _protect_literal_braces(text)
    t = _PLACEHOLDER_RE.sub(repl, t)
    return _unprotect_literal_braces(t)


def _apply_variables_to_turns(turns: List[Dict[str, Any]], variables: Dict[str, str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for turn in turns:
        new_turn = dict(turn)
        new_turn["message"] = substitute_persona_placeholders(str(turn.get("message", "")), variables)
        new_turn["expected_behavior"] = substitute_persona_placeholders(
            str(turn.get("expected_behavior", "")), variables
        )
        out.append(new_turn)
    return out


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


def _read_persona_json(persona_path: Path) -> Any:
    """Load and return raw JSON from persona file."""
    if not persona_path.exists():
        raise ConversationError(f"Persona file not found: {persona_path}")
    try:
        with persona_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ConversationError(f"Failed to parse persona JSON: {e}") from e


def _split_root_persona_data(data: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Return (turns list, meta dict)."""
    if isinstance(data, dict) and "turns" in data:
        turns = data["turns"]
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    elif isinstance(data, list):
        turns = data
        meta = {}
    else:
        raise ConversationError(
            "Persona JSON must be a list of turns or an object with a 'turns' array (and optional 'meta')."
        )
    if not isinstance(turns, list):
        raise ConversationError("Persona 'turns' must be a list.")
    return turns, meta


def load_persona_metadata(persona_path: Path) -> Dict[str, Any]:
    """Return optional metadata from persona JSON. If root is object with 'meta', return it; else return {}."""
    data = _read_persona_json(persona_path)
    if isinstance(data, dict) and "meta" in data:
        meta = data["meta"]
        return meta if isinstance(meta, dict) else {}
    return {}


def load_persona(persona_path: Path, variables: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    Load persona turns. Supports root as list of turns or object with 'turns' (and optional 'meta').

    If messages use {{placeholder}} tokens, values must be provided via variables= and/or meta.variables
    defaults in the JSON file. Missing keys raise ConversationError.
    """
    data = _read_persona_json(persona_path)
    turns, meta = _split_root_persona_data(data)
    _validate_persona_turns(turns, persona_path)
    merged = merge_persona_variable_defaults(meta, variables)
    needed = collect_persona_placeholders(turns)
    missing = needed - set(merged.keys())
    if missing:
        raise ConversationError(
            f"Persona {persona_path.name}: missing variable values for placeholders: {sorted(missing)}. "
            f"Set meta.variables in the file and/or pass variables when loading."
        )
    if not needed:
        return list(turns)
    return _apply_variables_to_turns(turns, merged)


async def run_conversation(
    persona_path: Path,
    model: str = "claude-haiku-4-5-20251001",
    system_prompt: Optional[str] = None,
    sut_backend: str = "anthropic",
    sut_options: Optional[Dict[str, Any]] = None,
    variables: Optional[Dict[str, str]] = None,
    persona_display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run the scripted conversation against the system under test.

    sut_backend: "anthropic" | "openai" | "custom"
    sut_options: optional dict passed to the backend (e.g. endpoint, api_key for custom).
    variables: optional map for {{placeholder}} substitution in persona messages.
    persona_display_name: label for results (defaults to persona file stem).

    Returns a structured dictionary containing:
      - persona_name
      - turns: list of {turn, user_message, expected_behavior, system_response}
      - conversation_for_judge: list of {role, turn, content} for the judge
    """
    adapter = get_backend(sut_backend)
    opts = sut_options or {}

    persona = load_persona(persona_path, variables=variables)
    display = persona_display_name if persona_display_name else persona_path.stem

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
        "persona_name": display,
        "turns": turns_output,
        "conversation_for_judge": conversation_for_judge,
    }


def lint_persona_template_file(persona_path: Path, strict: bool = False) -> List[str]:
    """
    Return list of issues for template hygiene (empty = OK).

    - Default: if any {{placeholders}} exist, require a meta.variables key (value may be {} for batch-only).
    - strict: every placeholder name must appear as a key in meta.variables.
    """
    errors: List[str] = []
    try:
        data = _read_persona_json(persona_path)
    except ConversationError as e:
        return [str(e)]
    try:
        turns, meta = _split_root_persona_data(data)
        _validate_persona_turns(turns, persona_path)
    except ConversationError as e:
        return [str(e)]
    needed = collect_persona_placeholders(turns)
    if not needed:
        return []
    if "variables" not in meta:
        errors.append(
            f"{persona_path.name}: uses {{placeholders}} {sorted(needed)} but meta.variables is missing "
            "(add \"variables\": {{}} under meta for batch-only, or supply defaults)."
        )
        return errors
    if strict:
        raw_vars = meta.get("variables")
        if not isinstance(raw_vars, dict):
            errors.append(f"{persona_path.name}: meta.variables must be a JSON object")
            return errors
        defined = {str(k) for k in raw_vars.keys()}
        missing = needed - defined
        if missing:
            errors.append(
                f"{persona_path.name}: strict lint: meta.variables missing keys for: {sorted(missing)}"
            )
    return errors
