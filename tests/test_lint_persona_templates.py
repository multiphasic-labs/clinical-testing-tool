"""Tests for lint_persona_template_file (template hygiene)."""
import json
from pathlib import Path

from runner import lint_persona_template_file


def test_lint_ok_when_no_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "a.json"
    path.write_text(
        json.dumps([{"turn": 1, "message": "Hi", "expected_behavior": "B"}]),
        encoding="utf-8",
    )
    assert lint_persona_template_file(path) == []


def test_lint_requires_meta_variables_key_when_placeholders(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps({
            "meta": {"notes": "no variables key"},
            "turns": [{"turn": 1, "message": "Hi {{x}}", "expected_behavior": "B"}],
        }),
        encoding="utf-8",
    )
    issues = lint_persona_template_file(path)
    assert len(issues) == 1
    assert "meta.variables" in issues[0]


def test_lint_strict_missing_key(tmp_path: Path) -> None:
    path = tmp_path / "strict.json"
    path.write_text(
        json.dumps({
            "meta": {"variables": {"a": "1"}},
            "turns": [{"turn": 1, "message": "{{a}} {{b}}", "expected_behavior": "B"}],
        }),
        encoding="utf-8",
    )
    assert lint_persona_template_file(path, strict=False) == []
    issues = lint_persona_template_file(path, strict=True)
    assert any("b" in i for i in issues)
