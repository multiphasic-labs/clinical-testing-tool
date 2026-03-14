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
