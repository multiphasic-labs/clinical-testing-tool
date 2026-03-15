import json
from pathlib import Path


def test_persona_files_exist() -> None:
    root = Path(__file__).resolve().parents[1]
    passive = root / "personas" / "passive_ideation.json"
    active = root / "personas" / "active_ideation.json"
    mild = root / "personas" / "mild_anxiety.json"
    bad_day = root / "personas" / "bad_day_vent.json"
    diagnosis_seeking = root / "personas" / "diagnosis_seeking.json"
    lonely = root / "personas" / "lonely_venting.json"
    overwhelmed = root / "personas" / "overwhelmed_unsure.json"
    substance = root / "personas" / "substance_cope.json"
    self_harm = root / "personas" / "self_harm_venting.json"
    grief = root / "personas" / "recent_loss_grief.json"
    panic = root / "personas" / "panic_acute.json"
    meds = root / "personas" / "medication_question.json"
    caretaker = root / "personas" / "caretaker_burnout.json"
    teen = root / "personas" / "teen_stress.json"
    eating = root / "personas" / "eating_distress.json"
    relationship = root / "personas" / "relationship_abuse.json"
    vague_physical = root / "personas" / "vague_physical_anxiety.json"
    teen_crisis = root / "personas" / "teen_crisis.json"
    workplace_burnout = root / "personas" / "workplace_burnout.json"
    perinatal = root / "personas" / "perinatal_worry.json"
    identity_stress = root / "personas" / "identity_stress.json"
    sleep_low_mood = root / "personas" / "sleep_low_mood.json"
    youth_substance = root / "personas" / "youth_substance.json"
    chronic_pain_mood = root / "personas" / "chronic_pain_mood.json"
    disengage = root / "personas" / "disengage_not_helping.json"
    assert passive.is_file()
    assert active.is_file()
    assert mild.is_file()
    assert bad_day.is_file()
    assert diagnosis_seeking.is_file()
    assert lonely.is_file()
    assert overwhelmed.is_file()
    assert substance.is_file()
    assert self_harm.is_file()
    assert grief.is_file()
    assert panic.is_file()
    assert meds.is_file()
    assert caretaker.is_file()
    assert teen.is_file()
    assert eating.is_file()
    assert relationship.is_file()
    assert vague_physical.is_file()
    assert teen_crisis.is_file()
    assert workplace_burnout.is_file()
    assert perinatal.is_file()
    assert identity_stress.is_file()
    assert sleep_low_mood.is_file()
    assert youth_substance.is_file()
    assert chronic_pain_mood.is_file()
    assert disengage.is_file()


def test_batch_config_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "personas" / "batch_config.json"
    assert config_path.is_file()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(data.get("personas"), list)
    assert "passive_ideation.json" in data["personas"]

