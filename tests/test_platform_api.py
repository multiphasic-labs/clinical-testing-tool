"""Tests for initial platform API scaffold."""
from pathlib import Path
import sys

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_api.app import app  # noqa: E402


client = TestClient(app)


def test_health_ok() -> None:
    r_root = client.get("/")
    assert r_root.status_code == 200
    assert r_root.json()["status"] == "ok"
    assert r_root.json()["docs"] == "/docs"

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    ui = client.get("/ui")
    assert ui.status_code == 200
    assert "Mental Health Safety Platform" in ui.text


def test_run_lifecycle_minimal() -> None:
    create = client.post(
        "/runs",
        json={
            "trigger_type": "manual",
            "model_name": "claude-sonnet-4-6",
            "prompt_version": "v1",
            "scenario_set": "core-250",
        },
    )
    assert create.status_code == 201
    run = create.json()
    rid = run["id"]
    assert run["status"] == "queued"

    listing = client.get("/runs")
    assert listing.status_code == 200
    assert any(x["id"] == rid for x in listing.json())

    detail = client.get(f"/runs/{rid}")
    assert detail.status_code == 200
    assert detail.json()["id"] == rid

    items = client.get(f"/runs/{rid}/items")
    assert items.status_code == 200
    assert items.json() == []

    findings = client.get(f"/runs/{rid}/findings")
    assert findings.status_code == 200
    assert findings.json() == []

    artifacts = client.get(f"/runs/{rid}/artifacts")
    assert artifacts.status_code == 200
    assert artifacts.json() == []

    retry = client.post(f"/runs/{rid}/retry-failed")
    assert retry.status_code == 202
    assert retry.json()["id"] != rid


def test_api_key_protection_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("SAFETY_PLATFORM_API_KEY", "secret-key")
    no_key = client.get("/runs")
    assert no_key.status_code == 401

    bad = client.get("/runs", headers={"x-api-key": "wrong"})
    assert bad.status_code == 401

    ok = client.get("/runs", headers={"x-api-key": "secret-key"})
    assert ok.status_code == 200
    monkeypatch.delenv("SAFETY_PLATFORM_API_KEY", raising=False)


def test_execute_uses_queue_when_enqueue_available(monkeypatch) -> None:
    # If enqueue returns True, we should not run inline in BackgroundTasks.
    import platform_api.app as appmod

    called = {"enqueue": 0}

    def _enqueue(_run_id: str) -> bool:
        called["enqueue"] += 1
        return True

    def _should_not_run(_run_id: str) -> None:
        raise AssertionError("run_evaluation_job should not be called when queued")

    monkeypatch.setattr(appmod, "enqueue_run", _enqueue)
    monkeypatch.setattr(appmod, "run_evaluation_job", _should_not_run)

    r = client.post("/runs", json={"execute": True})
    assert r.status_code == 201
    assert called["enqueue"] == 1

