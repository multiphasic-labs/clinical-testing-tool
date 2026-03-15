"""Tests for sut_backends (e.g. _get_by_path for custom response path)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sut_backends import _get_by_path


def test_get_by_path_top_level() -> None:
    data = {"content": "hello"}
    assert _get_by_path(data, "content") == "hello"
    assert _get_by_path(data, "missing") is None


def test_get_by_path_nested() -> None:
    data = {"a": {"b": {"c": 1}}}
    assert _get_by_path(data, "a.b.c") == 1
    assert _get_by_path(data, "a.b") == {"c": 1}
    assert _get_by_path(data, "a.x") is None


def test_get_by_path_list_index() -> None:
    data = {"choices": [{"message": {"content": "hi"}}]}
    assert _get_by_path(data, "choices.0.message.content") == "hi"
    assert _get_by_path(data, "choices.1.message.content") is None


def test_get_by_path_empty_path() -> None:
    assert _get_by_path({"a": 1}, "") is None
