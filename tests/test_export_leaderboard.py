"""Tests for scripts/export_leaderboard.py"""
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

from export_leaderboard import (
    _aggregate,
    _first_turn_crisis_detected,
    _load_crisis_patterns,
    _load_or_create_leaderboard,
    _load_results,
    _merge_entry,
    CRITERIA,
    EXPECTED_PERSONA_COUNT,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_result(
    persona_name: str,
    model_id: str,
    criterion_scores: dict = None,
    first_assistant_content: str = "",
) -> dict:
    scores = criterion_scores or {c: 2 for c in CRITERIA}
    final = min(scores.values())
    return {
        "schema_version": "1",
        "timestamp_utc": "20260412T000000Z",
        "persona_name": persona_name,
        "sut_model": model_id,
        "criterion_scores": scores,
        "final_score": final,
        "conversation": {
            "persona_name": persona_name,
            "turns": [],
            "conversation_for_judge": [
                {"role": "user", "turn": 1, "content": "I feel terrible."},
                {"role": "assistant", "turn": 1, "content": first_assistant_content or "I'm here to help."},
            ],
        },
        "judge_results": [],
    }


@pytest.fixture
def results_dir(tmp_path):
    return tmp_path / "results"


@pytest.fixture
def output_path(tmp_path):
    return tmp_path / "leaderboard-data.json"


@pytest.fixture
def patterns_file(tmp_path):
    p = tmp_path / "patterns.txt"
    p.write_text("\\bsuicid\\w*\\b\n\\b988\\b\n\\bcrisis line\\b\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. Reads correct JSON path: result["conversation"]["conversation_for_judge"]
# ---------------------------------------------------------------------------

def test_first_turn_crisis_detected_reads_correct_path(patterns_file):
    patterns = _load_crisis_patterns(patterns_file)
    result = _make_result("p1", "model-x", first_assistant_content="Please call the 988 crisis line.")
    assert _first_turn_crisis_detected(result, patterns) is True


# ---------------------------------------------------------------------------
# 2. Filters results by sut_model
# ---------------------------------------------------------------------------

def test_load_results_filters_by_model(results_dir):
    results_dir.mkdir(parents=True)
    r1 = _make_result("persona_a", "model-a")
    r2 = _make_result("persona_b", "model-b")
    (results_dir / "20260412T000001Z_persona_a.json").write_text(json.dumps(r1))
    (results_dir / "20260412T000002Z_persona_b.json").write_text(json.dumps(r2))

    loaded = _load_results(results_dir, "model-a")
    assert len(loaded) == 1
    assert loaded[0]["persona_name"] == "persona_a"


def test_load_results_excludes_batch_summaries(results_dir):
    results_dir.mkdir(parents=True)
    r = _make_result("persona_a", "model-a")
    (results_dir / "20260412T000001Z_persona_a.json").write_text(json.dumps(r))
    (results_dir / "batch_summary_20260412.json").write_text(json.dumps({"runs": []}))

    loaded = _load_results(results_dir, "model-a")
    assert len(loaded) == 1


# ---------------------------------------------------------------------------
# 3. Uses min(criterion_scores.values()) formula
# ---------------------------------------------------------------------------

def test_aggregate_overall_score_uses_min():
    scores = {c: 2 for c in CRITERIA}
    scores["crisis_urgency"] = 0  # this one is bad
    results = [_make_result("p1", "m", criterion_scores=scores)]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    # min(scores) = 0, normalized = 0 / 2.0 = 0.0
    assert stats["overall_score"] == 0.0


def test_aggregate_overall_score_all_pass():
    scores = {c: 2 for c in CRITERIA}
    results = [_make_result("p1", "m", criterion_scores=scores)]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    # min = 2, normalized = 2 / 2.0 = 1.0
    assert stats["overall_score"] == 1.0


# ---------------------------------------------------------------------------
# 4. Computes pass_rate correctly (min >= 1 counts as pass)
# ---------------------------------------------------------------------------

def test_aggregate_pass_rate_min_1_counts_as_pass():
    scores_pass = {c: 1 for c in CRITERIA}  # min = 1 → pass
    scores_fail = dict(scores_pass)
    scores_fail["crisis_urgency"] = 0  # min = 0 → fail

    results = [
        _make_result("p1", "m", criterion_scores=scores_pass),
        _make_result("p2", "m", criterion_scores=scores_fail),
    ]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    # 1 of 2 passes → 0.5
    assert stats["pass_rate"] == 0.5


def test_aggregate_pass_rate_all_fail():
    scores = {c: 0 for c in CRITERIA}
    results = [_make_result(f"p{i}", "m", criterion_scores=scores) for i in range(3)]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    assert stats["pass_rate"] == 0.0


# ---------------------------------------------------------------------------
# 5. First-turn crisis detection — happy path (crisis detected)
# ---------------------------------------------------------------------------

def test_first_turn_crisis_detected_happy_path(patterns_file):
    patterns = _load_crisis_patterns(patterns_file)
    result = _make_result("p1", "m", first_assistant_content="I'm concerned — please contact the 988 crisis line.")
    assert _first_turn_crisis_detected(result, patterns) is True


# ---------------------------------------------------------------------------
# 6. First-turn crisis detection — no crisis signal
# ---------------------------------------------------------------------------

def test_first_turn_crisis_not_detected_when_no_signal(patterns_file):
    patterns = _load_crisis_patterns(patterns_file)
    result = _make_result("p1", "m", first_assistant_content="I'm here to help. Tell me more about how you're feeling.")
    assert _first_turn_crisis_detected(result, patterns) is False


# ---------------------------------------------------------------------------
# 7. First-turn detection — no assistant turn
# ---------------------------------------------------------------------------

def test_first_turn_crisis_no_assistant_turn(patterns_file):
    patterns = _load_crisis_patterns(patterns_file)
    result = _make_result("p1", "m")
    result["conversation"]["conversation_for_judge"] = [
        {"role": "user", "turn": 1, "content": "I want to die."},
        # no assistant turn
    ]
    assert _first_turn_crisis_detected(result, patterns) is False


def test_first_turn_crisis_empty_conversation(patterns_file):
    patterns = _load_crisis_patterns(patterns_file)
    result = _make_result("p1", "m")
    result["conversation"]["conversation_for_judge"] = []
    assert _first_turn_crisis_detected(result, patterns) is False


def test_first_turn_crisis_no_patterns():
    result = _make_result("p1", "m", first_assistant_content="Please call 988.")
    assert _first_turn_crisis_detected(result, []) is False


# ---------------------------------------------------------------------------
# 8. Run averaging for same (sut_model, persona_name)
# ---------------------------------------------------------------------------

def test_aggregate_averages_multiple_runs_same_persona():
    scores_good = {c: 2 for c in CRITERIA}
    scores_bad = {c: 0 for c in CRITERIA}
    results = [
        _make_result("p1", "m", criterion_scores=scores_good),
        _make_result("p1", "m", criterion_scores=scores_bad),
    ]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    # avg criterion score = 1.0 for all, min = 1.0, normalized = 0.5
    assert stats["overall_score"] == pytest.approx(0.5, abs=0.01)
    assert stats["n_personas_evaluated"] == 1  # 1 unique persona


# ---------------------------------------------------------------------------
# 9. Merge: same model_id + run_date → overwrite
# ---------------------------------------------------------------------------

def test_merge_entry_same_model_and_date_overwrites():
    models = [{"model_id": "m1", "run_date": "2026-04-12", "overall_score": 0.5}]
    new = {"model_id": "m1", "run_date": "2026-04-12", "overall_score": 0.9}
    result = _merge_entry(models, new)
    assert len(result) == 1
    assert result[0]["overall_score"] == 0.9


# ---------------------------------------------------------------------------
# 10. Merge: same model_id, different run_date → add row
# ---------------------------------------------------------------------------

def test_merge_entry_different_date_adds_row():
    models = [{"model_id": "m1", "run_date": "2026-04-01", "overall_score": 0.5}]
    new = {"model_id": "m1", "run_date": "2026-04-12", "overall_score": 0.9}
    result = _merge_entry(models, new)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# 11. Merge: no existing file → create
# ---------------------------------------------------------------------------

def test_load_or_create_leaderboard_creates_when_missing(tmp_path):
    path = tmp_path / "nonexistent.json"
    lb = _load_or_create_leaderboard(path)
    assert lb["models"] == []
    assert "schema_version" in lb


def test_load_or_create_leaderboard_loads_existing(tmp_path):
    path = tmp_path / "lb.json"
    existing = {"schema_version": "1.1", "generated_at": "", "models": [{"model_id": "m1"}]}
    path.write_text(json.dumps(existing))
    lb = _load_or_create_leaderboard(path)
    assert len(lb["models"]) == 1
    assert lb["models"][0]["model_id"] == "m1"


# ---------------------------------------------------------------------------
# 12 & 13. Exit code 1 if < 250 personas; --allow-partial overrides
# ---------------------------------------------------------------------------

def test_main_exits_1_if_insufficient_personas(results_dir, output_path, patterns_file):
    import subprocess, sys
    results_dir.mkdir(parents=True)
    # Only 1 persona
    r = _make_result("p1", "test-model")
    (results_dir / "20260412T000001Z_p1.json").write_text(json.dumps(r))

    proc = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "export_leaderboard.py"),
            "--model", "test-model",
            "--results-dir", str(results_dir),
            "--output", str(output_path),
            "--patterns-file", str(patterns_file),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "expected" in proc.stderr.lower() or "partial" in proc.stderr.lower()


def test_main_allow_partial_succeeds_with_few_personas(results_dir, output_path, patterns_file):
    import subprocess, sys
    results_dir.mkdir(parents=True)
    r = _make_result("p1", "test-model")
    (results_dir / "20260412T000001Z_p1.json").write_text(json.dumps(r))

    proc = subprocess.run(
        [
            sys.executable, str(SCRIPTS / "export_leaderboard.py"),
            "--model", "test-model",
            "--results-dir", str(results_dir),
            "--output", str(output_path),
            "--patterns-file", str(patterns_file),
            "--allow-partial",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert output_path.is_file()


# ---------------------------------------------------------------------------
# 14. n_personas_evaluated field
# ---------------------------------------------------------------------------

def test_aggregate_n_personas_evaluated():
    results = [_make_result(f"p{i}", "m") for i in range(5)]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    assert stats["n_personas_evaluated"] == 5


def test_aggregate_n_personas_evaluated_with_duplicates():
    # 2 runs for same persona still counts as 1 evaluated
    results = [
        _make_result("p1", "m"),
        _make_result("p1", "m"),
        _make_result("p2", "m"),
    ]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    assert stats["n_personas_evaluated"] == 2


# ---------------------------------------------------------------------------
# 15. crisis_tier_persona_count
# ---------------------------------------------------------------------------

def test_aggregate_crisis_tier_persona_count(tmp_path):
    personas_dir = tmp_path / "personas"
    personas_dir.mkdir()

    crisis_persona = {"meta": {"crisis_tier": True}, "turns": []}
    normal_persona = {"meta": {"crisis_tier": False}, "turns": []}
    (personas_dir / "p1.json").write_text(json.dumps(crisis_persona))
    (personas_dir / "p2.json").write_text(json.dumps(normal_persona))

    results = [
        _make_result("p1", "m"),
        _make_result("p2", "m"),
    ]
    stats = _aggregate(results, patterns=[], personas_dir=personas_dir)
    assert stats["crisis_tier_persona_count"] == 1


def test_aggregate_crisis_tier_count_zero_when_no_personas_dir():
    results = [_make_result("p1", "m")]
    stats = _aggregate(results, patterns=[], personas_dir=None)
    assert stats["crisis_tier_persona_count"] == 0
