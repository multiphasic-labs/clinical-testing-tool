"""Platform worker: ingest batch summary into run_items and findings."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_api.app import app  # noqa: E402

client = TestClient(app)


def _fake_subprocess_run_factory(batch_rows: list[dict], returncode: int = 0):
    def _fake_run(argv, cwd, env, capture_output, text, timeout):  # noqa: ARG001
        out_i = argv.index("--output-dir")
        od = Path(argv[out_i + 1])
        od.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1",
            "timestamp_utc": "20990101T000000Z",
            "runs": batch_rows,
        }
        (od / "batch_summary_20990101T000000Z.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return subprocess.CompletedProcess(argv, returncode=returncode, stdout="ok", stderr="")

    return _fake_run


@patch("platform_api.worker.subprocess.run")
def test_execute_persists_items_and_findings(mock_run, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAFETY_PLATFORM_ARTIFACTS", str(tmp_path))
    rows = [
        {
            "persona": "Alpha",
            "run_label": "",
            "score": 2,
            "error": None,
            "result_path": "/tmp/a.json",
            "criterion_scores": {"crisis_urgency": 2},
            "persona_source_file": "personas/a.json",
            "persona_variables": {"x": "1"},
        },
        {
            "persona": "Beta",
            "run_label": "",
            "score": 0,
            "error": None,
            "result_path": "/tmp/b.json",
            "criterion_scores": {"crisis_urgency": 0},
        },
        {
            "persona": "Gamma",
            "run_label": "",
            "score": None,
            "error": "judge failed",
            "result_path": None,
            "criterion_scores": {},
        },
    ]
    mock_run.side_effect = _fake_subprocess_run_factory(rows, returncode=0)

    create = client.post(
        "/runs",
        json={
            "model_name": "test",
            "execute": True,
            "execution": {
                "mock": True,
                "batch_summary": True,
                "config_path": "personas/batch_config.json",
                "fail_under": 2,
                "timeout_seconds": 60,
            },
        },
    )
    assert create.status_code == 201
    rid = create.json()["id"]

    detail = client.get(f"/runs/{rid}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["status"] == "completed"
    assert body["exit_code"] == 0
    assert body["artifacts_dir"]

    items = client.get(f"/runs/{rid}/items").json()
    assert len(items) == 3
    assert items[0]["persona_display_name"] == "Alpha"
    assert items[0]["persona_variables"] == {"x": "1"}

    findings = client.get(f"/runs/{rid}/findings").json()
    titles = {f["title"] for f in findings}
    assert "Score below threshold" in titles
    assert "Critical criterion failure: crisis_urgency" in titles
    assert "Persona run error" in titles

    artifacts = client.get(f"/runs/{rid}/artifacts")
    assert artifacts.status_code == 200
    files = artifacts.json()
    assert any(f["name"].startswith("batch_summary_") for f in files)


@patch("platform_api.worker.subprocess.run")
def test_retry_re_executes_when_parent_had_execution_config(mock_run, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAFETY_PLATFORM_ARTIFACTS", str(tmp_path))
    mock_run.side_effect = _fake_subprocess_run_factory(
        [
            {
                "persona": "Only",
                "score": 2,
                "error": None,
                "result_path": "/x",
                "criterion_scores": {},
            }
        ],
        returncode=0,
    )

    first = client.post(
        "/runs",
        json={"execute": True, "execution": {"timeout_seconds": 60, "extra_args": ["--max-runs", "1"]}},
    )
    rid = first.json()["id"]
    assert client.get(f"/runs/{rid}").json()["status"] == "completed"

    mock_run.reset_mock()
    mock_run.side_effect = _fake_subprocess_run_factory(
        [
            {
                "persona": "Retry",
                "score": 2,
                "error": None,
                "result_path": "/y",
                "criterion_scores": {},
            }
        ],
        returncode=0,
    )

    retry = client.post(f"/runs/{rid}/retry-failed")
    assert retry.status_code == 202
    rid2 = retry.json()["id"]
    assert rid2 != rid
    assert client.get(f"/runs/{rid2}").json()["status"] == "completed"
    items = client.get(f"/runs/{rid2}/items").json()
    assert len(items) == 1
    assert items[0]["persona_display_name"] == "Retry"
    assert mock_run.called


@patch("platform_api.worker.subprocess.run")
def test_policy_file_overrides_finding_titles(mock_run, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAFETY_PLATFORM_ARTIFACTS", str(tmp_path))
    policy_path = tmp_path / "finding_policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "error_finding": {"enabled": True, "severity": "high", "title": "Execution Error"},
                "score_threshold": {"enabled": True, "severity": "low", "title": "Low score warning"},
                "critical_criteria": {
                    "enabled": True,
                    "match_mode": "contains",
                    "patterns": ["risk"],
                    "trigger_score": 0,
                    "severity": "high",
                    "title_template": "Critical miss: {criterion_id}",
                    "description": "Custom critical description."
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SAFETY_PLATFORM_FINDING_POLICY", str(policy_path))

    rows = [
        {
            "persona": "Policy A",
            "score": 1,
            "error": None,
            "result_path": "/tmp/a.json",
            "criterion_scores": {"risk_handoff": 0},
        },
        {
            "persona": "Policy B",
            "score": None,
            "error": "custom failure",
            "result_path": "/tmp/b.json",
            "criterion_scores": {},
        },
    ]
    mock_run.side_effect = _fake_subprocess_run_factory(rows, returncode=0)

    create = client.post(
        "/runs",
        json={"execute": True, "execution": {"fail_under": 2, "timeout_seconds": 60}},
    )
    assert create.status_code == 201
    rid = create.json()["id"]
    assert client.get(f"/runs/{rid}").json()["status"] == "completed"

    findings = client.get(f"/runs/{rid}/findings").json()
    titles = {f["title"] for f in findings}
    assert "Low score warning" in titles
    assert "Critical miss: risk_handoff" in titles
    assert "Execution Error" in titles
