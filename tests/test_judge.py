"""Tests for judge module (parsing, no API calls)."""
import json

import pytest

from judge import _format_conversation_text, _parse_judge_response


def test_format_conversation_text() -> None:
    conversation = [
        {"role": "user", "turn": 1, "content": "Hi"},
        {"role": "assistant", "turn": 1, "content": "Hello"},
    ]
    text = _format_conversation_text(conversation)
    assert "Turn 1 - user: Hi" in text
    assert "Turn 1 - assistant: Hello" in text


def test_parse_judge_response_valid() -> None:
    raw = '{"score": 2, "rationale": "Good.", "critical_failures": [], "positive_behaviors": ["X"]}'
    parsed = _parse_judge_response(raw, "Some criterion")
    assert parsed["score"] == 2
    assert parsed["rationale"] == "Good."
    assert parsed["critical_failures"] == []
    assert parsed["positive_behaviors"] == ["X"]


def test_parse_judge_response_with_markdown_wrapper() -> None:
    raw = "```json\n{\"score\": 1, \"rationale\": \"OK\", \"critical_failures\": [], \"positive_behaviors\": []}\n```"
    parsed = _parse_judge_response(raw, "Criterion")
    assert parsed["score"] == 1


def test_parse_judge_response_missing_score() -> None:
    raw = '{"rationale": "No score."}'
    with pytest.raises(RuntimeError, match="missing .score."):
        _parse_judge_response(raw, "Criterion")


def test_parse_judge_response_invalid_json() -> None:
    raw = "not json at all"
    with pytest.raises(RuntimeError, match="Failed to parse judge JSON"):
        _parse_judge_response(raw, "Criterion")
