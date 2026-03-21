"""Tests for runner module (persona loading, no API calls)."""
import json
import tempfile
from pathlib import Path

import pytest

from runner import ConversationError, load_persona


def test_load_persona_valid(tmp_path: Path) -> None:
    persona = [
        {"turn": 1, "message": "Hello", "expected_behavior": "Say hi back."},
    ]
    path = tmp_path / "valid.json"
    path.write_text(json.dumps(persona), encoding="utf-8")
    loaded = load_persona(path)
    assert loaded == persona


def test_load_persona_file_not_found() -> None:
    with pytest.raises(ConversationError, match="Persona file not found"):
        load_persona(Path("/nonexistent/persona.json"))


def test_load_persona_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not valid json {", encoding="utf-8")
    with pytest.raises(ConversationError, match="Failed to parse persona JSON"):
        load_persona(path)


def test_load_persona_not_list(tmp_path: Path) -> None:
    path = tmp_path / "object.json"
    path.write_text('{"turn": 1}', encoding="utf-8")
    with pytest.raises(ConversationError, match="Persona JSON must be a list"):
        load_persona(path)


def test_load_persona_missing_field(tmp_path: Path) -> None:
    path = tmp_path / "missing_message.json"
    path.write_text(
        json.dumps([{"turn": 1, "expected_behavior": "X"}]),
        encoding="utf-8",
    )
    with pytest.raises(ConversationError, match="missing required field"):
        load_persona(path)


def test_load_persona_duplicate_turn(tmp_path: Path) -> None:
    path = tmp_path / "dup.json"
    path.write_text(
        json.dumps([
            {"turn": 1, "message": "A", "expected_behavior": "B"},
            {"turn": 1, "message": "C", "expected_behavior": "D"},
        ]),
        encoding="utf-8",
    )
    with pytest.raises(ConversationError, match="duplicate turn"):
        load_persona(path)


def test_load_persona_turn_numbers_gaps(tmp_path: Path) -> None:
    path = tmp_path / "gaps.json"
    path.write_text(
        json.dumps([
            {"turn": 1, "message": "A", "expected_behavior": "B"},
            {"turn": 3, "message": "C", "expected_behavior": "D"},
        ]),
        encoding="utf-8",
    )
    with pytest.raises(ConversationError, match="must be 1..N"):
        load_persona(path)


def test_load_persona_object_with_turns(tmp_path: Path) -> None:
    """Persona can be object with 'turns' array (and optional 'meta')."""
    path = tmp_path / "with_meta.json"
    path.write_text(
        json.dumps({
            "meta": {"author": "test", "severity": "crisis"},
            "turns": [
                {"turn": 1, "message": "Hi", "expected_behavior": "Support."},
                {"turn": 2, "message": "Bye", "expected_behavior": "Close."},
            ],
        }),
        encoding="utf-8",
    )
    from runner import load_persona, load_persona_metadata
    turns = load_persona(path)
    assert len(turns) == 2
    assert turns[0]["message"] == "Hi"
    meta = load_persona_metadata(path)
    assert meta == {"author": "test", "severity": "crisis"}


def test_load_persona_metadata_empty_for_array_format(tmp_path: Path) -> None:
    """When persona is a plain array, metadata is empty."""
    path = tmp_path / "array_only.json"
    path.write_text(
        json.dumps([{"turn": 1, "message": "A", "expected_behavior": "B"}]),
        encoding="utf-8",
    )
    from runner import load_persona_metadata
    assert load_persona_metadata(path) == {}


def test_example_parameterized_persona_loads_with_defaults() -> None:
    """Shipped example template resolves {{placeholders}} via meta.variables."""
    root = Path(__file__).resolve().parent.parent
    path = root / "personas" / "example_parameterized_persona.json"
    turns = load_persona(path)
    assert "{{" not in turns[0]["message"]
    assert "work stress" in turns[0]["message"]


def test_literal_braces_escape_with_placeholder(tmp_path: Path) -> None:
    """\\{{ and \\}} become literal braces; normal {{name}} still substitutes."""
    path = tmp_path / "lit.json"
    msg = "L " + "\\{{" + "literal" + "\\}}" + " and {{topic}} end"
    path.write_text(
        json.dumps({
            "meta": {"variables": {"topic": "OK"}},
            "turns": [
                {"turn": 1, "message": msg, "expected_behavior": "B"},
                {"turn": 2, "message": "Bye", "expected_behavior": "C"},
            ],
        }),
        encoding="utf-8",
    )
    turns = load_persona(path)
    assert "{{literal}}" in turns[0]["message"]
    assert "OK" in turns[0]["message"]
    assert "topic}}" not in turns[0]["message"]  # not left as unresolved placeholder text
