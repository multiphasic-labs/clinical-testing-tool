"""Tests for JUnit writer and _gather_with_progress order."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main


def test_write_junit_all_pass() -> None:
    summary = [
        {"persona_name": "p1", "score": 2, "error": None},
        {"persona_name": "p2", "score": 2, "error": None},
    ]
    path = Path(__file__).parent / "out_junit_all_pass.xml"
    try:
        main._write_junit(path, summary, fail_under=2)
        content = path.read_text(encoding="utf-8")
        assert 'tests="2"' in content
        assert 'failures="0"' in content
        assert "<testcase name=" in content
        assert "p1" in content and "p2" in content
    finally:
        if path.exists():
            path.unlink()


def test_write_junit_with_failures() -> None:
    summary = [
        {"persona_name": "passive_ideation", "score": 1, "error": None},
        {"persona_name": "active_ideation", "score": 2, "error": None},
    ]
    path = Path(__file__).parent / "out_junit_fail.xml"
    try:
        main._write_junit(path, summary, fail_under=2)
        content = path.read_text(encoding="utf-8")
        assert 'tests="2"' in content
        assert 'failures="1"' in content
        assert "<failure" in content
        assert "passive_ideation" in content
    finally:
        if path.exists():
            path.unlink()


def test_write_junit_with_error() -> None:
    summary = [
        {"persona_name": "bad", "score": None, "error": "Run timed out"},
    ]
    path = Path(__file__).parent / "out_junit_err.xml"
    try:
        main._write_junit(path, summary, fail_under=None)
        content = path.read_text(encoding="utf-8")
        assert 'failures="1"' in content
        assert "Run timed out" in content
    finally:
        if path.exists():
            path.unlink()


def test_gather_with_progress_preserves_order() -> None:
    import asyncio

    async def make(i: int):
        return {"index": i}

    async def run():
        tasks = [make(0), make(1), make(2)]
        return await main._gather_with_progress(tasks, quiet=True)

    results = asyncio.run(run())
    assert [r["index"] for r in results] == [0, 1, 2]
