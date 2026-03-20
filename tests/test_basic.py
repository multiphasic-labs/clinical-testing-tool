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
    sibling_grief = root / "personas" / "sibling_grief.json"
    newly_diagnosed = root / "personas" / "newly_diagnosed_overwhelm.json"
    workplace_discrimination = root / "personas" / "workplace_discrimination.json"
    parent_child_conflict = root / "personas" / "parent_child_conflict.json"
    social_media_distress = root / "personas" / "social_media_distress.json"
    retirement_identity = root / "personas" / "retirement_identity.json"
    underemployment_frustration = root / "personas" / "underemployment_frustration.json"
    first_job_anxiety = root / "personas" / "first_job_anxiety.json"
    promotion_imposter_syndrome = root / "personas" / "promotion_imposter_syndrome.json"
    toxic_boss_nonabusive = root / "personas" / "toxic_boss_nonabusive.json"
    gig_worker_instability = root / "personas" / "gig_worker_instability.json"
    paycut_inflation_stress = root / "personas" / "paycut_inflation_stress.json"
    performance_plan_fear = root / "personas" / "performance_plan_fear.json"
    overachiever_cant_slow_down = root / "personas" / "overachiever_cant_slow_down.json"
    layoff_single_parent = root / "personas" / "layoff_single_parent.json"
    debt_collection_panic = root / "personas" / "debt_collection_panic.json"
    small_business_closure_grief = root / "personas" / "small_business_closure_grief.json"
    workplace_microaggressions = root / "personas" / "workplace_microaggressions.json"
    visa_job_uncertainty = root / "personas" / "visa_job_uncertainty.json"
    remote_work_isolation = root / "personas" / "remote_work_isolation.json"
    housing_insecure_worker = root / "personas" / "housing_insecure_worker.json"
    exam_stress_freeze = root / "personas" / "exam_stress_freeze.json"
    failing_out_hiding = root / "personas" / "failing_out_hiding.json"
    scholarship_pressure_dread = root / "personas" / "scholarship_pressure_dread.json"
    internship_competition_rumination = root / "personas" / "internship_competition_rumination.json"
    switching_majors_panic = root / "personas" / "switching_majors_panic.json"
    bullying_school_withdrawal = root / "personas" / "bullying_school_withdrawal.json"
    grade_disclosure_fear = root / "personas" / "grade_disclosure_fear.json"
    academic_burnout_overwhelm = root / "personas" / "academic_burnout_overwhelm.json"
    late_assignment_shame_avoidance = root / "personas" / "late_assignment_shame_avoidance.json"
    graduation_purpose_loss = root / "personas" / "graduation_purpose_loss.json"
    sandwich_generation_breakdown = root / "personas" / "sandwich_generation_breakdown.json"
    co_parenting_custody_stress = root / "personas" / "co_parenting_custody_stress.json"
    step_parent_insecurity = root / "personas" / "step_parent_insecurity.json"
    estranged_adult_child_guilt_shame = root / "personas" / "estranged_adult_child_guilt_shame.json"
    parent_child_no_contact_panic = root / "personas" / "parent_child_no_contact_panic.json"
    teen_running_away_fear = root / "personas" / "teen_running_away_fear.json"
    child_secret_depression_parent_fear = root / "personas" / "child_secret_depression_parent_fear.json"
    respite_care_unreachable_breakpoint = root / "personas" / "respite_care_unreachable_breakpoint.json"
    elder_fall_watching_doomsday = root / "personas" / "elder_fall_watching_doomsday.json"
    divorce_coparenting_anger_spiral = root / "personas" / "divorce_coparenting_anger_spiral.json"
    adoption_identity_grief = root / "personas" / "adoption_identity_grief.json"
    birth_family_contact_conflict = root / "personas" / "birth_family_contact_conflict.json"
    grandparent_guardianship_pressure = root / "personas" / "grandparent_guardianship_pressure.json"
    newborn_partner_resentment_sleep_deprivation = root / "personas" / "newborn_partner_resentment_sleep_deprivation.json"
    family_betrayal_trust_break = root / "personas" / "family_betrayal_trust_break.json"
    domestic_violence_coercive_fear = root / "personas" / "domestic_violence_coercive_fear.json"
    eviction_notice_food_insecurity = root / "personas" / "eviction_notice_food_insecurity.json"
    dementia_spouse_caregiver_trap = root / "personas" / "dementia_spouse_caregiver_trap.json"
    pet_loss_grief_guilt = root / "personas" / "pet_loss_grief_guilt.json"
    disability_accommodations_denied_job_pressure = root / "personas" / "disability_accommodations_denied_job_pressure.json"
    neurodivergent_masking_overwhelm = root / "personas" / "neurodivergent_masking_overwhelm.json"
    sensory_overload_shutdown = root / "personas" / "sensory_overload_shutdown.json"
    racial_bias_job_interview_worry = root / "personas" / "racial_bias_job_interview_worry.json"
    immigrant_language_shame_isolation = root / "personas" / "immigrant_language_shame_isolation.json"
    religious_guilt_scrupulosity = root / "personas" / "religious_guilt_scrupulosity.json"
    refugee_arrival_hypervigilance = root / "personas" / "refugee_arrival_hypervigilance.json"
    interracial_relationship_judgment_loneliness = root / "personas" / "interracial_relationship_judgment_loneliness.json"
    sexual_harassment_unwanted_attention_fear = root / "personas" / "sexual_harassment_unwanted_attention_fear.json"
    rejection_sensitive_overwhelm_breakdown = root / "personas" / "rejection_sensitive_overwhelm_breakdown.json"
    breakup_abandonment_panic = root / "personas" / "breakup_abandonment_panic.json"
    dating_app_ghosting_rumination = root / "personas" / "dating_app_ghosting_rumination.json"
    rejection_after_public_confession = root / "personas" / "rejection_after_public_confession.json"
    stalking_post_breakup_monitoring = root / "personas" / "stalking_post_breakup_monitoring.json"
    cyberstalking_unwanted_messages = root / "personas" / "cyberstalking_unwanted_messages.json"
    partner_threats_texts_fear = root / "personas" / "partner_threats_texts_fear.json"
    partner_withdrawal_panic_communication_breakdown = root / "personas" / "partner_withdrawal_panic_communication_breakdown.json"
    mutual_friends_breakup_displacement_grief = root / "personas" / "mutual_friends_breakup_displacement_grief.json"
    emotional_withdrawal_self_blame_ruminating = root / "personas" / "emotional_withdrawal_self_blame_ruminating.json"
    relationship_boundary_conflict_in_laws_misunderstanding = root / "personas" / "relationship_boundary_conflict_in_laws_misunderstanding.json"
    suicide_loss_survivor_guilt_intrusive_memories = root / "personas" / "suicide_loss_survivor_guilt_intrusive_memories.json"
    could_i_have_prevented_it_regret = root / "personas" / "could_i_have_prevented_it_regret.json"
    surviving_sibling_guilt_suicide_loss = root / "personas" / "surviving_sibling_guilt_suicide_loss.json"
    community_suicide_news_fear_trigger = root / "personas" / "community_suicide_news_fear_trigger.json"
    anniversary_suicide_loss_passive_disappearance = root / "personas" / "anniversary_suicide_loss_passive_disappearance.json"
    coworker_suicide_shock_isolation = root / "personas" / "coworker_suicide_shock_isolation.json"
    parent_suicide_loss_child_grief = root / "personas" / "parent_suicide_loss_child_grief.json"
    avoid_talking_about_suicide_shame = root / "personas" / "avoid_talking_about_suicide_shame.json"
    postvention_support_group_fear_return = root / "personas" / "postvention_support_group_fear_return.json"
    birthday_holidays_after_suicide_passive_thoughts = root / "personas" / "birthday_holidays_after_suicide_passive_thoughts.json"
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
    assert sibling_grief.is_file()
    assert newly_diagnosed.is_file()
    assert workplace_discrimination.is_file()
    assert parent_child_conflict.is_file()
    assert social_media_distress.is_file()
    assert retirement_identity.is_file()
    assert underemployment_frustration.is_file()
    assert first_job_anxiety.is_file()
    assert promotion_imposter_syndrome.is_file()
    assert toxic_boss_nonabusive.is_file()
    assert gig_worker_instability.is_file()
    assert paycut_inflation_stress.is_file()
    assert performance_plan_fear.is_file()
    assert overachiever_cant_slow_down.is_file()
    assert layoff_single_parent.is_file()
    assert debt_collection_panic.is_file()
    assert small_business_closure_grief.is_file()
    assert workplace_microaggressions.is_file()
    assert visa_job_uncertainty.is_file()
    assert remote_work_isolation.is_file()
    assert housing_insecure_worker.is_file()
    assert exam_stress_freeze.is_file()
    assert failing_out_hiding.is_file()
    assert scholarship_pressure_dread.is_file()
    assert internship_competition_rumination.is_file()
    assert switching_majors_panic.is_file()
    assert bullying_school_withdrawal.is_file()
    assert grade_disclosure_fear.is_file()
    assert academic_burnout_overwhelm.is_file()
    assert late_assignment_shame_avoidance.is_file()
    assert graduation_purpose_loss.is_file()
    assert sandwich_generation_breakdown.is_file()
    assert co_parenting_custody_stress.is_file()
    assert step_parent_insecurity.is_file()
    assert estranged_adult_child_guilt_shame.is_file()
    assert parent_child_no_contact_panic.is_file()
    assert teen_running_away_fear.is_file()
    assert child_secret_depression_parent_fear.is_file()
    assert respite_care_unreachable_breakpoint.is_file()
    assert elder_fall_watching_doomsday.is_file()
    assert divorce_coparenting_anger_spiral.is_file()
    assert adoption_identity_grief.is_file()
    assert birth_family_contact_conflict.is_file()
    assert grandparent_guardianship_pressure.is_file()
    assert newborn_partner_resentment_sleep_deprivation.is_file()
    assert family_betrayal_trust_break.is_file()
    assert domestic_violence_coercive_fear.is_file()
    assert eviction_notice_food_insecurity.is_file()
    assert dementia_spouse_caregiver_trap.is_file()
    assert pet_loss_grief_guilt.is_file()
    assert disability_accommodations_denied_job_pressure.is_file()
    assert neurodivergent_masking_overwhelm.is_file()
    assert sensory_overload_shutdown.is_file()
    assert racial_bias_job_interview_worry.is_file()
    assert immigrant_language_shame_isolation.is_file()
    assert religious_guilt_scrupulosity.is_file()
    assert refugee_arrival_hypervigilance.is_file()
    assert interracial_relationship_judgment_loneliness.is_file()
    assert sexual_harassment_unwanted_attention_fear.is_file()
    assert rejection_sensitive_overwhelm_breakdown.is_file()
    assert breakup_abandonment_panic.is_file()
    assert dating_app_ghosting_rumination.is_file()
    assert rejection_after_public_confession.is_file()
    assert stalking_post_breakup_monitoring.is_file()
    assert cyberstalking_unwanted_messages.is_file()
    assert partner_threats_texts_fear.is_file()
    assert partner_withdrawal_panic_communication_breakdown.is_file()
    assert mutual_friends_breakup_displacement_grief.is_file()
    assert emotional_withdrawal_self_blame_ruminating.is_file()
    assert relationship_boundary_conflict_in_laws_misunderstanding.is_file()
    assert suicide_loss_survivor_guilt_intrusive_memories.is_file()
    assert could_i_have_prevented_it_regret.is_file()
    assert surviving_sibling_guilt_suicide_loss.is_file()
    assert community_suicide_news_fear_trigger.is_file()
    assert anniversary_suicide_loss_passive_disappearance.is_file()
    assert coworker_suicide_shock_isolation.is_file()
    assert parent_suicide_loss_child_grief.is_file()
    assert avoid_talking_about_suicide_shame.is_file()
    assert postvention_support_group_fear_return.is_file()
    assert birthday_holidays_after_suicide_passive_thoughts.is_file()


def test_batch_config_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "personas" / "batch_config.json"
    assert config_path.is_file()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(data.get("personas"), list)
    assert "passive_ideation.json" in data["personas"]

