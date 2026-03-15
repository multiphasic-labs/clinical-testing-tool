"""Tests that run main in mock mode (no API calls)."""
import argparse
import asyncio
import os
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
    )
    buf = StringIO()
    with redirect_stdout(buf):
        exit_code = asyncio.run(main.main_async(args))
    assert exit_code == 0
