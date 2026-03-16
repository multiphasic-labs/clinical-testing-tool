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
    older_adult = root / "personas" / "older_adult_burden.json"
    academic = root / "personas" / "academic_stress.json"
    anger = root / "personas" / "anger_irritability.json"
    rumination = root / "personas" / "rumination_worry.json"
    post_crisis = root / "personas" / "post_crisis_fear.json"
    social_anxiety = root / "personas" / "social_anxiety_isolation.json"
    bereavement = root / "personas" / "bereavement_anniversary.json"
    new_parent = root / "personas" / "new_parent_exhausted.json"
    financial_stress = root / "personas" / "financial_stress_despair.json"
    chronic_illness = root / "personas" / "chronic_illness_depression.json"
    bullying_work = root / "personas" / "bullying_work.json"
    trauma_triggered = root / "personas" / "trauma_triggered.json"
    sleep_insomnia = root / "personas" / "sleep_insomnia_anxiety.json"
    lgbtq_rejection = root / "personas" / "lgbtq_rejection.json"
    relapse_worry = root / "personas" / "relapse_worry.json"
    hoarding_shame = root / "personas" / "hoarding_shame.json"
    intrusive_thoughts = root / "personas" / "intrusive_thoughts_shame.json"
    divorce_grief = root / "personas" / "divorce_grief.json"
    empty_nest = root / "personas" / "empty_nest_sadness.json"
    career_identity = root / "personas" / "career_identity_crisis.json"
    chronic_loneliness = root / "personas" / "chronic_loneliness.json"
    health_anxiety = root / "personas" / "health_anxiety_reassurance.json"
    perfectionism_burnout = root / "personas" / "perfectionism_burnout.json"
    guilt_shame = root / "personas" / "guilt_shame_spiral.json"
    veteran_adjustment = root / "personas" / "veteran_adjustment.json"
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
    assert older_adult.is_file()
    assert academic.is_file()
    assert anger.is_file()
    assert rumination.is_file()
    assert post_crisis.is_file()
    assert social_anxiety.is_file()
    assert bereavement.is_file()
    assert new_parent.is_file()
    assert financial_stress.is_file()
    assert chronic_illness.is_file()
    assert bullying_work.is_file()
    assert trauma_triggered.is_file()
    assert sleep_insomnia.is_file()
    assert lgbtq_rejection.is_file()
    assert relapse_worry.is_file()
    assert hoarding_shame.is_file()
    assert intrusive_thoughts.is_file()
    assert divorce_grief.is_file()
    assert empty_nest.is_file()
    assert career_identity.is_file()
    assert chronic_loneliness.is_file()
    assert health_anxiety.is_file()
    assert perfectionism_burnout.is_file()
    assert guilt_shame.is_file()
    assert veteran_adjustment.is_file()


def test_batch_config_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "personas" / "batch_config.json"
    assert config_path.is_file()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(data.get("personas"), list)
    assert "passive_ideation.json" in data["personas"]

