"""Integration-style tests for parameterized personas (mock mode, subprocess)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAFETY_TESTER_MOCK", "1")


def test_mock_batch_respects_persona_var_and_writes_variables(tmp_path: Path) -> None:
    """Batch run applies --persona-var; result JSON includes persona_variables."""
    pdir = tmp_path / "personas"
    pdir.mkdir()
    persona = {
        "meta": {"variables": {"topic": "default_topic"}},
        "turns": [
            {"turn": 1, "message": "About {{topic}}", "expected_behavior": "Support."},
            {"turn": 2, "message": "Thanks", "expected_behavior": "Close."},
        ],
    }
    (pdir / "param.json").write_text(json.dumps(persona), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--personas-dir",
        str(pdir),
        "--output-dir",
        str(out),
        "--mock",
        "--quiet",
        "--batch-summary",
        "--persona-var",
        "topic=custom_topic",
        "--criteria",
        "crisis_urgency",
    ]
    env = {**os.environ, "SAFETY_TESTER_MOCK": "1"}
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    results = [p for p in out.glob("*.json") if "batch_summary" not in p.name]
    assert results, "expected result JSON"
    data = json.loads(results[0].read_text(encoding="utf-8"))
    assert data.get("persona_variables", {}).get("topic") == "custom_topic"
    conv = data.get("conversation") or {}
    cj = conv.get("conversation_for_judge") or []
    user_text = " ".join(x.get("content", "") for x in cj if x.get("role") == "user")
    assert "custom_topic" in user_text
    assert "{{" not in user_text


def test_dry_run_prints_resolved_vars(tmp_path: Path) -> None:
    pdir = tmp_path / "personas"
    pdir.mkdir()
    (pdir / "a.json").write_text(
        json.dumps([{"turn": 1, "message": "m", "expected_behavior": "e"}]),
        encoding="utf-8",
    )
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--personas-dir",
        str(pdir),
        "--dry-run",
        "--mock",
    ]
    env = {**os.environ, "SAFETY_TESTER_MOCK": "1"}
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "Planned runs" in r.stdout
    assert "a.json" in r.stdout


def test_validate_include_example_personas(tmp_path: Path) -> None:
    """--include-example-personas validates the example template file."""
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--validate-personas",
        "--include-example-personas",
    ]
    env = {**os.environ}
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "example_parameterized_persona.json" in r.stdout


def test_lint_script_exits_zero() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "lint_persona_templates.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "OK" in r.stdout


def test_dry_run_lists_prompt_times_persona_rows(tmp_path: Path) -> None:
    """--dry-run with --sut-prompts prints one line per (prompt, persona) pair."""
    pdir = tmp_path / "personas"
    pdir.mkdir()
    (pdir / "one.json").write_text(
        json.dumps([{"turn": 1, "message": "Hi", "expected_behavior": "B"}]),
        encoding="utf-8",
    )
    pa = tmp_path / "prompt_a.txt"
    pb = tmp_path / "prompt_b.txt"
    pa.write_text("You are prompt A.", encoding="utf-8")
    pb.write_text("You are prompt B.", encoding="utf-8")
    cmd = [
        sys.executable,
        str(ROOT / "main.py"),
        "--personas-dir",
        str(pdir),
        "--sut-prompts",
        f"{pa},{pb}",
        "--dry-run",
        "--mock",
    ]
    env = {**os.environ, "SAFETY_TESTER_MOCK": "1"}
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "prompt_a" in r.stdout
    assert "prompt_b" in r.stdout
    assert r.stdout.count("one.json") >= 2
