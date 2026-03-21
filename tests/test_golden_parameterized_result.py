"""
Golden-shape test: parameterized mock run produces stable top-level keys in saved result JSON.
Guards against regressions dropping persona_source_file / persona_variables / etc.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_RESULT_KEYS = {
    "schema_version",
    "timestamp_utc",
    "persona_name",
    "conversation",
    "judge_results",
    "criterion_scores",
    "final_score",
    "persona_source_file",
    "persona_variables",
}


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAFETY_TESTER_MOCK", "1")


def test_saved_result_json_shape_parameterized_mock(tmp_path: Path) -> None:
    pdir = tmp_path / "personas"
    pdir.mkdir()
    persona = {
        "meta": {"variables": {"topic": "default_topic"}},
        "turns": [
            {"turn": 1, "message": "Topic: {{topic}}", "expected_behavior": "Support."},
            {"turn": 2, "message": "Bye", "expected_behavior": "Close."},
        ],
    }
    (pdir / "golden_param.json").write_text(json.dumps(persona), encoding="utf-8")
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
        "--persona-var",
        "topic=golden_value",
        "--criteria",
        "crisis_urgency",
    ]
    env = {**os.environ, "SAFETY_TESTER_MOCK": "1"}
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr + r.stdout
    result_files = [p for p in out.glob("*.json") if "batch_summary" not in p.name]
    assert len(result_files) == 1
    data = json.loads(result_files[0].read_text(encoding="utf-8"))
    missing = REQUIRED_RESULT_KEYS - set(data.keys())
    assert not missing, f"missing keys: {missing}"
    assert data["persona_variables"].get("topic") == "golden_value"
    assert data["persona_source_file"] == "golden_param.json"
    assert isinstance(data["conversation"], dict)
    assert isinstance(data["judge_results"], list)
