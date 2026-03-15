"""Tests that run main in mock mode (no API calls)."""
import argparse
import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Run from project root so imports work
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAFETY_TESTER_MOCK", "1")


def test_mock_run_single_persona_quiet() -> None:
    """Run main with --mock --quiet and check exit 0 and output contains score and path."""
    import main

    from contextlib import redirect_stdout
    from io import StringIO

    args = argparse.Namespace(
        config=None,
        persona="passive_ideation.json",
        verbose=False,
        sut_model="claude-haiku-4-5-20251001",
        judge_model="claude-sonnet-4-6",
        mock=True,
        output_dir=None,
        quiet=True,
        md=False,
        fail_under=None,
        sut_system_prompt=None,
        criteria=None,
        personas=None,
        log=None,
        batch_summary=False,
        fail_under_criteria=None,
        compare_baseline=False,
        baseline=None,
        list_personas=False,
        list_criteria=False,
        criterion_file=None,
        report=None,
        sut_prompts=None,
        parallel=1,
        csv=False,
        config_file=None,
        sut="anthropic",
        sut_endpoint=None,
        sut_api_key=None,
        sut_response_path=None,
        dry_run=False,
        history=None,
        notify_webhook=None,
        retry_failed=False,
        retry_failed_from=None,
        max_requests_per_minute=None,
        save_baseline=False,
        notify_success=False,
        version=False,
        health_check=False,
        branded_report=None,
        report_branding_title=None,
        personas_dir=None,
        persona_tags=None,
        live=False,
        list_tags=False,
        validate_personas=False,
        run_timeout=None,
        judge=None,
        criteria_dir=None,
        write_index=False,
        notify_format=None,
        max_runs=None,
        no_color=False,
        shard=None,
        junit=None,
        failures_only=False,
        judge_temperature=None,
        report_only=None,
        cache_dir=None,
        profile=False,
        ndjson=False,
        redact=False,
        criterion_weights=None,
    )
    buf = StringIO()
    with redirect_stdout(buf):
        exit_code = asyncio.run(main.main_async(args))
    out = buf.getvalue()
    assert exit_code == 0
    assert "persona=passive_ideation" in out or "passive_ideation" in out
    assert "score=" in out
    assert "path=" in out or "results" in out


def test_mock_run_via_subprocess() -> None:
    """Run python main.py --mock --quiet via subprocess (full CLI)."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--persona", "passive_ideation.json", "--mock", "--quiet"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "SAFETY_TESTER_MOCK": "1"},
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "score=" in result.stdout
    assert "path=" in result.stdout


def test_fail_under_exits_1_when_below() -> None:
    """With --fail-under 3, mock score 2 should cause exit 1."""
    import main
    from contextlib import redirect_stdout
    from io import StringIO

    args = argparse.Namespace(
        config=None,
        persona="passive_ideation.json",
        verbose=False,
        sut_model="x",
        judge_model="x",
        mock=True,
        output_dir=None,
        quiet=True,
        md=False,
        fail_under=3,
        sut_system_prompt=None,
        criteria=None,
        personas=None,
        log=None,
        batch_summary=False,
        fail_under_criteria=None,
        compare_baseline=False,
        baseline=None,
        list_personas=False,
        list_criteria=False,
        criterion_file=None,
        report=None,
        sut_prompts=None,
        parallel=1,
        csv=False,
        config_file=None,
        sut="anthropic",
        sut_endpoint=None,
        sut_api_key=None,
        sut_response_path=None,
        dry_run=False,
        history=None,
        notify_webhook=None,
        retry_failed=False,
        retry_failed_from=None,
        max_requests_per_minute=None,
        save_baseline=False,
        notify_success=False,
        version=False,
        health_check=False,
        branded_report=None,
        report_branding_title=None,
        personas_dir=None,
        persona_tags=None,
        live=False,
        list_tags=False,
        validate_personas=False,
        run_timeout=None,
        judge=None,
        criteria_dir=None,
        write_index=False,
        notify_format=None,
        max_runs=None,
        no_color=False,
        shard=None,
        junit=None,
        failures_only=False,
        judge_temperature=None,
        report_only=None,
        cache_dir=None,
        profile=False,
        ndjson=False,
        redact=False,
        criterion_weights=None,
    )
    buf = StringIO()
    with redirect_stdout(buf):
        exit_code = asyncio.run(main.main_async(args))
    assert exit_code == 1


def test_fail_under_exits_0_when_above() -> None:
    """With --fail-under 1, mock score 2 should cause exit 0."""
    import main
    from contextlib import redirect_stdout
    from io import StringIO

    args = argparse.Namespace(
        config=None,
        persona="passive_ideation.json",
        verbose=False,
        sut_model="x",
        judge_model="x",
        mock=True,
        output_dir=None,
        quiet=True,
        md=False,
        fail_under=1,
        sut_system_prompt=None,
        criteria=None,
        personas=None,
        log=None,
        batch_summary=False,
        fail_under_criteria=None,
        compare_baseline=False,
        baseline=None,
        list_personas=False,
        list_criteria=False,
        criterion_file=None,
        report=None,
        sut_prompts=None,
        parallel=1,
        csv=False,
        config_file=None,
        sut="anthropic",
        sut_endpoint=None,
        sut_api_key=None,
        sut_response_path=None,
        dry_run=False,
        history=None,
        notify_webhook=None,
        retry_failed=False,
        retry_failed_from=None,
        max_requests_per_minute=None,
        save_baseline=False,
        notify_success=False,
        version=False,
        health_check=False,
        branded_report=None,
        report_branding_title=None,
        personas_dir=None,
        persona_tags=None,
        live=False,
        list_tags=False,
        validate_personas=False,
        run_timeout=None,
        judge=None,
        criteria_dir=None,
        write_index=False,
        notify_format=None,
        max_runs=None,
        no_color=False,
        shard=None,
        junit=None,
        failures_only=False,
        judge_temperature=None,
        report_only=None,
        cache_dir=None,
        profile=False,
        ndjson=False,
        redact=False,
        criterion_weights=None,
    )
    buf = StringIO()
    with redirect_stdout(buf):
        exit_code = asyncio.run(main.main_async(args))
    assert exit_code == 0


def test_dry_run_exits_0_and_prints_plan() -> None:
    """--dry-run prints plan and exits 0 without calling API."""
    import main
    from contextlib import redirect_stdout
    from io import StringIO

    args = argparse.Namespace(
        config=None,
        persona="passive_ideation.json",
        verbose=False,
        sut_model="x",
        judge_model="x",
        mock=False,
        output_dir=None,
        quiet=False,
        md=False,
        fail_under=None,
        sut_system_prompt=None,
        criteria=None,
        personas=None,
        log=None,
        batch_summary=False,
        fail_under_criteria=None,
        compare_baseline=False,
        baseline=None,
        list_personas=False,
        list_criteria=False,
        criterion_file=None,
        report=None,
        sut_prompts=None,
        parallel=1,
        csv=False,
        config_file=None,
        sut="anthropic",
        sut_endpoint=None,
        sut_api_key=None,
        sut_response_path=None,
        dry_run=True,
        history=None,
        notify_webhook=None,
        retry_failed=False,
        retry_failed_from=None,
        max_requests_per_minute=None,
        save_baseline=False,
        notify_success=False,
        version=False,
        health_check=False,
        branded_report=None,
        report_branding_title=None,
        personas_dir=None,
        persona_tags=None,
        live=False,
        list_tags=False,
        validate_personas=False,
        run_timeout=None,
        judge=None,
        criteria_dir=None,
        write_index=False,
        notify_format=None,
        max_runs=None,
        no_color=False,
        shard=None,
        junit=None,
        failures_only=False,
        judge_temperature=None,
        report_only=None,
        cache_dir=None,
        profile=False,
        ndjson=False,
        redact=False,
        criterion_weights=None,
    )
    buf = StringIO()
    with redirect_stdout(buf):
        exit_code = asyncio.run(main.main_async(args))
    out = buf.getvalue()
    assert exit_code == 0
    assert "Dry run" in out
    assert "passive_ideation" in out


def test_notify_failure_none_does_nothing() -> None:
    """_notify_failure with None URL does not raise."""
    import main
    main._notify_failure(None, "test message")
    main._notify_failure("", "test")


def test_load_retry_failed_empty_dir_returns_empty() -> None:
    """_load_retry_failed with empty dir returns []."""
    import main
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        out = main._load_retry_failed(None, Path(d), fail_under=2)
    assert out == []


def test_history_append_writes_one_line() -> None:
    """With --history, a successful run appends one JSON line to the file."""
    import main
    from contextlib import redirect_stdout
    from io import StringIO
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        hist_path = Path(f.name)
    try:
        args = argparse.Namespace(
            config=None,
            persona="passive_ideation.json",
            verbose=False,
            sut_model="x",
            judge_model="x",
            mock=True,
            output_dir=None,
            quiet=True,
            md=False,
            fail_under=None,
            sut_system_prompt=None,
            criteria=None,
            personas=None,
            log=None,
            batch_summary=False,
            fail_under_criteria=None,
            compare_baseline=False,
            baseline=None,
            list_personas=False,
            list_criteria=False,
            criterion_file=None,
            report=None,
            sut_prompts=None,
            parallel=1,
            csv=False,
            config_file=None,
            sut="anthropic",
            sut_endpoint=None,
            sut_api_key=None,
            sut_response_path=None,
            dry_run=False,
            history=str(hist_path),
            notify_webhook=None,
            retry_failed=False,
            retry_failed_from=None,
            max_requests_per_minute=None,
            save_baseline=False,
            notify_success=False,
            version=False,
            health_check=False,
            branded_report=None,
            report_branding_title=None,
            personas_dir=None,
            persona_tags=None,
            live=False,
            list_tags=False,
            validate_personas=False,
            run_timeout=None,
            judge=None,
            criteria_dir=None,
            write_index=False,
            notify_format=None,
            max_runs=None,
            no_color=False,
            shard=None,
            junit=None,
            failures_only=False,
            judge_temperature=None,
            report_only=None,
            cache_dir=None,
            profile=False,
            ndjson=False,
            redact=False,
            criterion_weights=None,
        )
        with redirect_stdout(StringIO()):
            asyncio.run(main.main_async(args))
        lines = [l for l in hist_path.read_text().strip().split("\n") if l]
        assert len(lines) >= 1
        import json
        record = json.loads(lines[-1])
        assert "persona_name" in record or "timestamp_utc" in record
    finally:
        hist_path.unlink(missing_ok=True)


def test_load_retry_failed_from_json() -> None:
    """_load_retry_failed finds failed runs from summary JSON."""
    import main
    import tempfile
    summary = {
        "runs": [
            {"persona": "p1", "run_label": "", "score": 1, "error": None},
            {"persona": "p2", "run_label": "", "score": 2, "error": None},
            {"persona": "p3", "run_label": "prompt_a", "error": "Connection failed"},
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        import json
        json.dump({"runs": summary["runs"]}, f)
        path = Path(f.name)
    try:
        out = main._load_retry_failed(path, Path(tempfile.gettempdir()), fail_under=2)
        # p1 score 1 < 2, p3 has error; p2 passes
        assert len(out) == 2
        personas = [x[0] for x in out]
        assert "p1" in personas
        assert "p3" in personas
    finally:
        path.unlink()


def test_version_prints_and_exits_0() -> None:
    """--version prints version string and exits 0."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--version"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout.strip()
    # Should look like a version (e.g. 0.1.0)
    assert "." in result.stdout


def test_health_check_exits_0() -> None:
    """--health-check runs one mock run and exits 0 if pipeline works."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--health-check"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "SAFETY_TESTER_MOCK": "1"},
    )
    assert result.returncode == 0


def test_result_json_has_schema_version() -> None:
    """Saved result JSON includes schema_version field."""
    import json
    import tempfile
    import main
    from contextlib import redirect_stdout
    from io import StringIO

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        args = argparse.Namespace(
            config=None,
            persona="passive_ideation.json",
            verbose=False,
            sut_model="x",
            judge_model="x",
            mock=True,
            output_dir=str(out_dir),
            quiet=True,
            md=False,
            fail_under=None,
            sut_system_prompt=None,
            criteria=None,
            personas=None,
            log=None,
            batch_summary=False,
            fail_under_criteria=None,
            compare_baseline=False,
            baseline=None,
            list_personas=False,
            list_criteria=False,
            criterion_file=None,
            report=None,
            sut_prompts=None,
            parallel=1,
            csv=False,
            config_file=None,
            sut="anthropic",
            sut_endpoint=None,
            sut_api_key=None,
            sut_response_path=None,
            dry_run=False,
            history=None,
            notify_webhook=None,
            retry_failed=False,
            retry_failed_from=None,
            max_requests_per_minute=None,
            save_baseline=False,
            notify_success=False,
            version=False,
            health_check=False,
            branded_report=None,
            report_branding_title=None,
            personas_dir=None,
            persona_tags=None,
            live=False,
            list_tags=False,
            validate_personas=False,
            run_timeout=None,
            judge=None,
            criteria_dir=None,
            write_index=False,
            notify_format=None,
            max_runs=None,
            no_color=False,
            shard=None,
            junit=None,
            failures_only=False,
            judge_temperature=None,
            report_only=None,
            cache_dir=None,
            profile=False,
            ndjson=False,
            redact=False,
            criterion_weights=None,
        )
        with redirect_stdout(StringIO()):
            asyncio.run(main.main_async(args))
        jsons = list(out_dir.glob("*.json"))
        assert len(jsons) >= 1
        data = json.loads(jsons[0].read_text(encoding="utf-8"))
        assert data.get("schema_version") == "1"


def test_list_tags_exits_0_and_prints_tags() -> None:
    """--list-tags prints tags and personas then exits 0."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--list-tags"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "crisis" in result.stdout or "support" in result.stdout or "boundary" in result.stdout
    assert "passive_ideation" in result.stdout or "persona" in result.stdout.lower()


def test_personas_dir_runs_discovered_personas() -> None:
    """--personas-dir personas runs all discovered personas (mock)."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--personas-dir", "personas", "--persona-tags", "crisis", "--quiet"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    # Should see at least passive_ideation and active_ideation (crisis tag)
    assert "passive_ideation" in result.stdout or "active_ideation" in result.stdout
    assert "score=2" in result.stdout


def test_default_run_is_mock() -> None:
    """Without --live, run uses mock (no API key required)."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--persona", "passive_ideation.json", "--quiet"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"},
    )
    assert result.returncode == 0
    assert "score=2" in result.stdout
    assert "ANTHROPIC_API_KEY" not in result.stderr or "not set" not in result.stderr.lower()


def test_validate_personas_all_ok() -> None:
    """--validate-personas exits 0 when all personas in personas/ are valid."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--validate-personas"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "valid" in result.stdout.lower() or "OK" in result.stdout


def test_validate_personas_reports_invalid() -> None:
    """--validate-personas exits 1 and reports when a persona file is invalid."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.json"
        bad.write_text('[{"turn": 1}]', encoding="utf-8")  # missing message, expected_behavior
        result = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--validate-personas", "--personas-dir", tmp],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
    assert result.returncode == 1
    assert "FAIL" in result.stdout or "fail" in result.stdout.lower()
    assert "missing" in result.stdout.lower() or "required" in result.stdout.lower()
