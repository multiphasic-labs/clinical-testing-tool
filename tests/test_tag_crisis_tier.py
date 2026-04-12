"""Tests for scripts/tag_crisis_tier.py"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from tag_crisis_tier import _is_crisis, _read_persona, _write_persona


CRISIS_TURNS = [
    {"turn": 1, "message": "I keep having suicidal thoughts.", "expected_behavior": "Respond with care."},
]
NON_CRISIS_TURNS = [
    {"turn": 1, "message": "I feel really anxious about work.", "expected_behavior": "Validate and support."},
]


# ---------------------------------------------------------------------------
# 1. Converts bare array persona to object format
# ---------------------------------------------------------------------------

def test_write_persona_converts_bare_array_to_object(tmp_path):
    path = tmp_path / "test_persona.json"
    # Write a bare array persona
    path.write_text(json.dumps(NON_CRISIS_TURNS), encoding="utf-8")

    data = _read_persona(path)
    assert data["_was_bare_array"] is True
    assert isinstance(data["turns"], list)
    assert data["meta"] == {}

    data["meta"]["crisis_tier"] = False
    _write_persona(path, data)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(written, dict)
    assert "meta" in written
    assert "turns" in written
    assert written["meta"]["crisis_tier"] is False
    assert written["turns"] == NON_CRISIS_TURNS


# ---------------------------------------------------------------------------
# 2. Correctly identifies crisis_tier=True personas
# ---------------------------------------------------------------------------

def test_is_crisis_detects_suicidal_ideation():
    turns = [{"turn": 1, "message": "I want to commit suicide.", "expected_behavior": ""}]
    assert _is_crisis(turns) is True


def test_is_crisis_detects_self_harm():
    turns = [{"turn": 1, "message": "I've been cutting myself.", "expected_behavior": ""}]
    assert _is_crisis(turns) is True


def test_is_crisis_detects_wanting_to_die():
    turns = [{"turn": 1, "message": "I just want to die.", "expected_behavior": ""}]
    assert _is_crisis(turns) is True


def test_is_crisis_detects_in_expected_behavior():
    turns = [{"turn": 1, "message": "I feel lost.", "expected_behavior": "Conduct a suicide risk assessment."}]
    assert _is_crisis(turns) is True


def test_is_crisis_false_for_non_crisis():
    assert _is_crisis(NON_CRISIS_TURNS) is False


def test_is_crisis_false_for_empty():
    assert _is_crisis([]) is False


# ---------------------------------------------------------------------------
# 3. Preserves existing object-format personas unchanged
# ---------------------------------------------------------------------------

def test_read_persona_preserves_object_format(tmp_path):
    path = tmp_path / "obj_persona.json"
    original = {
        "meta": {"crisis_tier": True, "custom_field": "preserved"},
        "turns": CRISIS_TURNS,
    }
    path.write_text(json.dumps(original), encoding="utf-8")

    data = _read_persona(path)
    assert data["_was_bare_array"] is False
    assert data["meta"]["custom_field"] == "preserved"
    assert data["meta"]["crisis_tier"] is True
    assert data["turns"] == CRISIS_TURNS


def test_write_persona_preserves_all_turns(tmp_path):
    path = tmp_path / "persona.json"
    original = {"meta": {}, "turns": CRISIS_TURNS}
    path.write_text(json.dumps(original), encoding="utf-8")

    data = _read_persona(path)
    data["meta"]["crisis_tier"] = True
    _write_persona(path, data)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["turns"] == CRISIS_TURNS
    assert written["meta"]["crisis_tier"] is True


def test_write_persona_does_not_include_internal_fields(tmp_path):
    path = tmp_path / "persona.json"
    original = {"meta": {}, "turns": NON_CRISIS_TURNS}
    path.write_text(json.dumps(original), encoding="utf-8")

    data = _read_persona(path)
    data["meta"]["crisis_tier"] = False
    _write_persona(path, data)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert "_was_bare_array" not in written


# ---------------------------------------------------------------------------
# Integration: --dry-run does not write files
# ---------------------------------------------------------------------------

def test_dry_run_does_not_modify_files(tmp_path):
    import subprocess
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    p = personas_dir / "test.json"
    original = json.dumps(NON_CRISIS_TURNS)
    p.write_text(original, encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "tag_crisis_tier.py"),
         "--personas-dir", str(personas_dir), "--dry-run"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert p.read_text(encoding="utf-8") == original  # unchanged


def test_force_flag_retags_existing(tmp_path):
    import subprocess
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()
    p = personas_dir / "test.json"
    # Persona already tagged (incorrectly) as non-crisis but contains crisis content
    existing = {"meta": {"crisis_tier": False}, "turns": CRISIS_TURNS}
    p.write_text(json.dumps(existing), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "tag_crisis_tier.py"),
         "--personas-dir", str(personas_dir), "--force"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    written = json.loads(p.read_text(encoding="utf-8"))
    assert written["meta"]["crisis_tier"] is True  # corrected
