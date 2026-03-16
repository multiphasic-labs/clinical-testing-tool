"""Integration tests for --report-only and --cache-dir."""
import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _make_args(**overrides):
    """Minimal argparse.Namespace for main_async (avoids parse_args() reading sys.argv)."""
    defaults = dict(
        config=None, persona="passive_ideation.json", verbose=False,
        sut_model="x", judge_model="x", mock=True, output_dir=None, quiet=True, md=False,
        fail_under=None, sut_system_prompt=None, criteria=None, personas=None, log=None,
        batch_summary=False, fail_under_criteria=None, compare_baseline=False, baseline=None,
        list_personas=False, list_criteria=False, criterion_file=None, report=None, sut_prompts=None,
        parallel=1, csv=False, config_file=None, sut="anthropic", sut_endpoint=None, sut_api_key=None,
        sut_response_path=None, dry_run=False, history=None, notify_webhook=None, retry_failed=False,
        retry_failed_from=None, max_requests_per_minute=None, save_baseline=False, notify_success=False,
        version=False, health_check=False, branded_report=None, report_branding_title=None,
        personas_dir=None, persona_tags=None, live=False, list_tags=False, validate_personas=False,
        run_timeout=None, judge=None, criteria_dir=None, write_index=False, notify_format=None, max_runs=None,
        no_color=False, shard=None, junit=None, failures_only=False, judge_temperature=None,
        report_only=None, cache_dir=None, profile=False, ndjson=False, redact=False, criterion_weights=None,
        preflight=False, interactive=False, repeat=1, sut_timeout=None, judge_timeout=None, log_format="text",
        config_profile=None, persona_difficulty=None,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def test_report_only_updates_result_file() -> None:
    """--report-only on a fixture result JSON updates judge_results and final_score."""
    import main
    fixture = ROOT / "tests" / "fixtures" / "sample_result_for_report_only.json"
    assert fixture.is_file(), f"Fixture missing: {fixture}"
    with tempfile.TemporaryDirectory() as tmp:
        result_path = Path(tmp) / "result.json"
        result_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
        args = _make_args(report_only=str(result_path), mock=True, quiet=True, live=False)
        exit_code = asyncio.run(main.main_async(args))
        assert exit_code == 0
        data = json.loads(result_path.read_text(encoding="utf-8"))
        assert "judge_results" in data
        assert len(data["judge_results"]) > 0
        assert "criterion_scores" in data
        assert "final_score" in data
        assert data["final_score"] >= 0


def test_cache_dir_run_completes() -> None:
    """With --cache-dir and mock, run completes without error (cache not used in mock)."""
    import main
    with tempfile.TemporaryDirectory() as tmp:
        cache_dir = Path(tmp) / "cache"
        cache_dir.mkdir()
        out_dir = Path(tmp) / "out"
        out_dir.mkdir()
        args = _make_args(
            persona="passive_ideation.json", mock=True, live=False,
            cache_dir=str(cache_dir), output_dir=str(out_dir), quiet=True,
        )
        exit_code = asyncio.run(main.main_async(args))
        assert exit_code == 0
        assert cache_dir.is_dir()


def test_report_only_directory() -> None:
    """--report-only on a directory finds result JSONs and re-scores them."""
    import main
    fixture = ROOT / "tests" / "fixtures" / "sample_result_for_report_only.json"
    with tempfile.TemporaryDirectory() as tmp:
        dir_path = Path(tmp)
        (dir_path / "20260101T120000Z_passive_ideation.json").write_text(
            fixture.read_text(encoding="utf-8"), encoding="utf-8"
        )
        args = _make_args(report_only=str(dir_path), mock=True, quiet=True)
        exit_code = asyncio.run(main.main_async(args))
        assert exit_code == 0
        data = json.loads((dir_path / "20260101T120000Z_passive_ideation.json").read_text(encoding="utf-8"))
        assert data.get("final_score") is not None
        assert len(data.get("judge_results", [])) > 0
