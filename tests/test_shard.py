"""Tests for --shard parsing and application."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main


def test_parse_shard_empty_or_none() -> None:
    assert main._parse_shard(None) is None
    assert main._parse_shard("") is None
    assert main._parse_shard("   ") is None


def test_parse_shard_valid() -> None:
    assert main._parse_shard("0/4") == (0, 4)
    assert main._parse_shard("1/4") == (1, 4)
    assert main._parse_shard("3/4") == (3, 4)
    assert main._parse_shard("0/1") == (0, 1)
    assert main._parse_shard(" 2/10 ") == (2, 10)


def test_parse_shard_invalid_format() -> None:
    assert main._parse_shard("0") is None
    assert main._parse_shard("0/4/1") is None
    assert main._parse_shard("0/4/") is None
    assert main._parse_shard("a/4") is None
    assert main._parse_shard("0/b") is None
    assert main._parse_shard("x/y") is None


def test_parse_shard_invalid_n_m() -> None:
    # n >= m invalid
    assert main._parse_shard("4/4") is None
    assert main._parse_shard("5/4") is None
    # n < 0 invalid
    assert main._parse_shard("-1/4") is None
    # m <= 0 invalid
    assert main._parse_shard("0/0") is None
    assert main._parse_shard("0/-1") is None


def test_apply_shard_none_returns_all() -> None:
    items = ["a", "b", "c"]
    assert main._apply_shard(items, None) == items


def test_apply_shard_0_2() -> None:
    items = ["a", "b", "c", "d"]
    assert main._apply_shard(items, (0, 2)) == ["a", "c"]


def test_apply_shard_1_2() -> None:
    items = ["a", "b", "c", "d"]
    assert main._apply_shard(items, (1, 2)) == ["b", "d"]


def test_apply_shard_0_4() -> None:
    items = [f"p{i}" for i in range(12)]
    assert main._apply_shard(items, (0, 4)) == ["p0", "p4", "p8"]


def test_apply_shard_3_4() -> None:
    items = [f"p{i}" for i in range(12)]
    assert main._apply_shard(items, (3, 4)) == ["p3", "p7", "p11"]


def test_apply_shard_empty_list() -> None:
    assert main._apply_shard([], (0, 4)) == []
