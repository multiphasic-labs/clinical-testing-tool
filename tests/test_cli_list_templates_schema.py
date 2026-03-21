"""CLI: --list-personas --templates and JSON Schema validation."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_list_templates_shows_example_when_in_personas_dir() -> None:
    """example_parameterized is in personas/ but excluded from default list; --templates scans files on disk."""
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            "--list-personas",
            "--templates",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "example_parameterized_persona.json" in r.stdout


def test_templates_requires_list_personas() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--templates"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2


def test_validate_schema_rejects_bad_shape(tmp_path: Path) -> None:
    pytest.importorskip("jsonschema")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not_turns": []}), encoding="utf-8")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "main.py"),
            "--validate-personas",
            "--validate-schema",
            "--personas-dir",
            str(tmp_path),
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "FAIL" in r.stdout or "bad.json" in r.stdout


def test_persona_file_has_placeholder_helper() -> None:
    import main
    from pathlib import Path

    ex = ROOT / "personas" / "example_parameterized_persona.json"
    assert main._persona_file_has_template_placeholders(ex) is True
    plain = ROOT / "personas" / "passive_ideation.json"
    assert main._persona_file_has_template_placeholders(plain) is False
