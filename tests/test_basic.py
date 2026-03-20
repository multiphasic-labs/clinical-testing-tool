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
    coworker_threats_after_complaint_fear = root / "personas" / "coworker_threats_after_complaint_fear.json"
    reporting_harassment_retaliation_workplace_fear = root / "personas" / "reporting_harassment_retaliation_workplace_fear.json"
    ex_stalking_at_workplace_panic_fear = root / "personas" / "ex_stalking_at_workplace_panic_fear.json"
    violent_client_service_worker_safety_fear = root / "personas" / "violent_client_service_worker_safety_fear.json"
    workplace_lockdown_threat_panic = root / "personas" / "workplace_lockdown_threat_panic.json"
    after_calling_police_domestic_risk_at_work = root / "personas" / "after_calling_police_domestic_risk_at_work.json"
    security_alarm_breach_disbelief = root / "personas" / "security_alarm_breach_disbelief.json"
    boss_downplays_safety_threats = root / "personas" / "boss_downplays_safety_threats.json"
    cyberstalking_work_chat_phishing_fear = root / "personas" / "cyberstalking_work_chat_phishing_fear.json"
    threatening_note_breakroom_freeze = root / "personas" / "threatening_note_breakroom_freeze.json"
    mortgage_foreclosure_imminent_destabilizing = root / "personas" / "mortgage_foreclosure_imminent_destabilizing.json"
    couch_surfing_transport_income_overwhelm = root / "personas" / "couch_surfing_transport_income_overwhelm.json"
    shelter_line_waiting_insomnia_panic = root / "personas" / "shelter_line_waiting_insomnia_panic.json"
    housing_application_rejection_deflated = root / "personas" / "housing_application_rejection_deflated.json"
    rent_increase_math_panic = root / "personas" / "rent_increase_math_panic.json"
    landlord_illegal_entry_fear = root / "personas" / "landlord_illegal_entry_fear.json"
    locked_out_of_home_no_phone_food_panic = root / "personas" / "locked_out_of_home_no_phone_food_panic.json"
    deposit_refund_scam_shame_fear = root / "personas" / "deposit_refund_scam_shame_fear.json"
    utility_water_gas_cutoff_grief = root / "personas" / "utility_water_gas_cutoff_grief.json"
    roommate_threaten_eviction_split_rent = root / "personas" / "roommate_threaten_eviction_split_rent.json"
    doctor_dismisses_symptoms_gaslighting_fear = root / "personas" / "doctor_dismisses_symptoms_gaslighting_fear.json"
    er_discharge_no_followup_confusion = root / "personas" / "er_discharge_no_followup_confusion.json"
    waiting_diagnosis_ruminating_fear = root / "personas" / "waiting_diagnosis_ruminating_fear.json"
    pre_surgery_anxiety_catastrophizing = root / "personas" / "pre_surgery_anxiety_catastrophizing.json"
    medication_side_effect_fear_still_taking = root / "personas" / "medication_side_effect_fear_still_taking.json"
    lab_results_delay_hypervigilance = root / "personas" / "lab_results_delay_hypervigilance.json"
    chronic_flare_hiding_from_family = root / "personas" / "chronic_flare_hiding_from_family.json"
    disability_benefits_review_medical_anxiety = root / "personas" / "disability_benefits_review_medical_anxiety.json"
    nurse_shift_burnout_moral_injury = root / "personas" / "nurse_shift_burnout_moral_injury.json"
    needle_phobia_avoiding_care = root / "personas" / "needle_phobia_avoiding_care.json"
    immigration_hearing_date_insomnia_dread = root / "personas" / "immigration_hearing_date_insomnia_dread.json"
    asylum_case_wait_years_numbness = root / "personas" / "asylum_case_wait_years_numbness.json"
    mixed_status_family_school_forms_fear = root / "personas" / "mixed_status_family_school_forms_fear.json"
    residency_delay_partner_abroad_lonely = root / "personas" / "residency_delay_partner_abroad_lonely.json"
    lost_immigration_documents_panic_shame = root / "personas" / "lost_immigration_documents_panic_shame.json"
    workplace_wage_theft_fear_status_retaliation = root / "personas" / "workplace_wage_theft_fear_status_retaliation.json"
    international_student_postgrad_timeline_panic = root / "personas" / "international_student_postgrad_timeline_panic.json"
    airport_secondary_screening_aftermath_hypervigilance = root / "personas" / "airport_secondary_screening_aftermath_hypervigilance.json"
    immigration_paperwork_scam_shame_distrust = root / "personas" / "immigration_paperwork_scam_shame_distrust.json"
    loved_one_detained_little_information_grief = root / "personas" / "loved_one_detained_little_information_grief.json"
    sextortion_blackmail_threat_shame_cycle = root / "personas" / "sextortion_blackmail_threat_shame_cycle.json"
    intimate_content_shared_without_consent_by_ex = root / "personas" / "intimate_content_shared_without_consent_by_ex.json"
    romance_scam_savings_lost_shame_isolation = root / "personas" / "romance_scam_savings_lost_shame_isolation.json"
    elder_financial_exploitation_relative_control_fear = root / "personas" / "elder_financial_exploitation_relative_control_fear.json"
    authority_impersonation_phone_scam_elder_panic = root / "personas" / "authority_impersonation_phone_scam_elder_panic.json"
    youth_online_image_pressure_fear_telling_parent = root / "personas" / "youth_online_image_pressure_fear_telling_parent.json"
    synthetic_intimate_media_fear_reputation = root / "personas" / "synthetic_intimate_media_fear_reputation.json"
    investment_fraud_trusted_group_chat_shame = root / "personas" / "investment_fraud_trusted_group_chat_shame.json"
    account_takeover_phishing_panic_shame = root / "personas" / "account_takeover_phishing_panic_shame.json"
    workplace_rumor_synthetic_intimate_media_fear = root / "personas" / "workplace_rumor_synthetic_intimate_media_fear.json"
    sports_betting_chase_losses_shame_partner_lies = root / "personas" / "sports_betting_chase_losses_shame_partner_lies.json"
    online_casino_losses_hidden_rent_panic = root / "personas" / "online_casino_losses_hidden_rent_panic.json"
    gambling_recovery_meeting_slip_shame_isolation = root / "personas" / "gambling_recovery_meeting_slip_shame_isolation.json"
    payday_loan_gambling_debt_trap_dread = root / "personas" / "payday_loan_gambling_debt_trap_dread.json"
    athlete_coach_body_comment_restrictive_fear = root / "personas" / "athlete_coach_body_comment_restrictive_fear.json"
    compulsive_exercise_identity_rest_day_spiral = root / "personas" / "compulsive_exercise_identity_rest_day_spiral.json"
    endurance_training_underfueling_fatigue_low_mood = root / "personas" / "endurance_training_underfueling_fatigue_low_mood.json"
    team_performance_supplement_pressure_anxiety = root / "personas" / "team_performance_supplement_pressure_anxiety.json"
    sleep_deprivation_visual_weirdness_fear_mind = root / "personas" / "sleep_deprivation_visual_weirdness_fear_mind.json"
    exam_stress_perceptual_oddity_fear_psychosis = root / "personas" / "exam_stress_perceptual_oddity_fear_psychosis.json"
    miscarriage_early_loss_isolation_shame = root / "personas" / "miscarriage_early_loss_isolation_shame.json"
    recurrent_pregnancy_loss_grief_despair = root / "personas" / "recurrent_pregnancy_loss_grief_despair.json"
    stillbirth_grief_anniversary_dread = root / "personas" / "stillbirth_grief_anniversary_dread.json"
    termination_medical_reasons_grief_secrecy = root / "personas" / "termination_medical_reasons_grief_secrecy.json"
    infertility_two_week_wait_obsessing = root / "personas" / "infertility_two_week_wait_obsessing.json"
    ivf_cycle_stimulation_exhaustion_relationship_strain = root / "personas" / "ivf_cycle_stimulation_exhaustion_relationship_strain.json"
    ivf_embryo_transfer_failure_numbness = root / "personas" / "ivf_embryo_transfer_failure_numbness.json"
    ttc_partner_timeline_mismatch_resentment = root / "personas" / "ttc_partner_timeline_mismatch_resentment.json"
    pregnancy_after_prior_loss_every_symptom_panic = root / "personas" / "pregnancy_after_prior_loss_every_symptom_panic.json"
    adoption_process_stall_ambivalent_grief = root / "personas" / "adoption_process_stall_ambivalent_grief.json"
    concussion_cleared_athlete_still_symptomatic_fear = root / "personas" / "concussion_cleared_athlete_still_symptomatic_fear.json"
    college_concussion_academic_accommodations_shame = root / "personas" / "college_concussion_academic_accommodations_shame.json"
    workplace_head_bump_unreported_worsening_anxiety = root / "personas" / "workplace_head_bump_unreported_worsening_anxiety.json"
    parent_teen_athlete_second_concussion_fear = root / "personas" / "parent_teen_athlete_second_concussion_fear.json"
    car_crash_mild_head_injury_insurance_rumination = root / "personas" / "car_crash_mild_head_injury_insurance_rumination.json"
    post_concussion_screen_light_noise_overwhelm = root / "personas" / "post_concussion_screen_light_noise_overwhelm.json"
    concussion_mood_swings_partner_guilt = root / "personas" / "concussion_mood_swings_partner_guilt.json"
    concussion_word_finding_fail_meeting_humiliation = root / "personas" / "concussion_word_finding_fail_meeting_humiliation.json"
    competitive_athlete_career_end_concussion_history_grief = root / "personas" / "competitive_athlete_career_end_concussion_history_grief.json"
    exertion_headache_return_to_exercise_fear_spiral = root / "personas" / "exertion_headache_return_to_exercise_fear_spiral.json"
    pain_clinic_discontinued_abrupt_reduction_anxiety = root / "personas" / "pain_clinic_discontinued_abrupt_reduction_anxiety.json"
    medical_opioid_taper_chronic_pain_fear_street_thought = root / "personas" / "medical_opioid_taper_chronic_pain_fear_street_thought.json"
    post_surgery_breakthrough_refill_denied_helpless = root / "personas" / "post_surgery_breakthrough_refill_denied_helpless.json"
    pain_contract_urine_monitoring_paranoia_shame = root / "personas" / "pain_contract_urine_monitoring_paranoia_shame.json"
    spouse_pain_meds_addiction_accusation_grief = root / "personas" / "spouse_pain_meds_addiction_accusation_grief.json"
    young_adult_chronic_pain_er_dismissed_drug_seeking_shame = root / "personas" / "young_adult_chronic_pain_er_dismissed_drug_seeking_shame.json"
    rural_pain_specialist_access_barrier_despond = root / "personas" / "rural_pain_specialist_access_barrier_despond.json"
    pain_flare_disability_work_loss_passive_guilt = root / "personas" / "pain_flare_disability_work_loss_passive_guilt.json"
    kinesiophobia_reinjury_avoidance_depression_spiral = root / "personas" / "kinesiophobia_reinjury_avoidance_depression_spiral.json"
    workers_comp_pain_claim_scrutiny_isolation = root / "personas" / "workers_comp_pain_claim_scrutiny_isolation.json"
    paramedic_pediatric_call_intrusive_memories = root / "personas" / "paramedic_pediatric_call_intrusive_memories.json"
    firefighter_mayday_crew_injury_survivor_guilt = root / "personas" / "firefighter_mayday_crew_injury_survivor_guilt.json"
    ems_partner_same_unit_shift_conflict_home = root / "personas" / "ems_partner_same_unit_shift_conflict_home.json"
    emergency_dispatcher_protocol_correct_still_guilty_insomnia = root / "personas" / "emergency_dispatcher_protocol_correct_still_guilty_insomnia.json"
    wildfire_deployment_exhaustion_emotional_numb_spouse = root / "personas" / "wildfire_deployment_exhaustion_emotional_numb_spouse.json"
    ems_scene_assault_spirit_broken_hypervigilance = root / "personas" / "ems_scene_assault_spirit_broken_hypervigilance.json"
    firefighter_off_duty_medical_emergency_second_guessing = root / "personas" / "firefighter_off_duty_medical_emergency_second_guessing.json"
    probationary_firefighter_station_bullying_trapped = root / "personas" / "probationary_firefighter_station_bullying_trapped.json"
    technical_rescue_long_extrication_emotional_numbness = root / "personas" / "technical_rescue_long_extrication_emotional_numbness.json"
    air_ambulance_high_acuity_detachment_family_grief = root / "personas" / "air_ambulance_high_acuity_detachment_family_grief.json"
    parent_metastatic_cancer_long_distance_careguilt = root / "personas" / "parent_metastatic_cancer_long_distance_careguilt.json"
    spouse_oncology_diagnosis_role_reversal_overwhelm = root / "personas" / "spouse_oncology_diagnosis_role_reversal_overwhelm.json"
    adult_child_parent_stroke_resentment_guilt_trap = root / "personas" / "adult_child_parent_stroke_resentment_guilt_trap.json"
    sibling_psychiatric_hospitalization_family_secrecy_shame = root / "personas" / "sibling_psychiatric_hospitalization_family_secrecy_shame.json"
    pediatric_hospital_parent_dissociation_waiting_guilt = root / "personas" / "pediatric_hospital_parent_dissociation_waiting_guilt.json"
    partner_neurodegenerative_decline_caregiver_lonely = root / "personas" / "partner_neurodegenerative_decline_caregiver_lonely.json"
    parent_dialysis_schedule_financial_exhaustion = root / "personas" / "parent_dialysis_schedule_financial_exhaustion.json"
    family_disagree_illness_disclosure_sibling_fracture = root / "personas" / "family_disagree_illness_disclosure_sibling_fracture.json"
    geographic_distance_parent_medical_emergency_guilt = root / "personas" / "geographic_distance_parent_medical_emergency_guilt.json"
    hospice_family_decision_conflict_anticipatory_grief = root / "personas" / "hospice_family_decision_conflict_anticipatory_grief.json"
    public_bias_harassment_transit_hypervigilance = root / "personas" / "public_bias_harassment_transit_hypervigilance.json"
    home_vandalism_targeted_identity_safety_fear = root / "personas" / "home_vandalism_targeted_identity_safety_fear.json"
    child_bullied_bigotry_school_parent_rage_guilt = root / "personas" / "child_bullied_bigotry_school_parent_rage_guilt.json"
    neighbor_pattern_bias_harassment_police_report_fear = root / "personas" / "neighbor_pattern_bias_harassment_police_report_fear.json"
    workplace_bias_incident_after_hate_event_news = root / "personas" / "workplace_bias_incident_after_hate_event_news.json"
    community_mass_violence_news_hypervigilance_daily_life = root / "personas" / "community_mass_violence_news_hypervigilance_daily_life.json"
    cultural_community_space_threat_message_volunteer_fear = root / "personas" / "cultural_community_space_threat_message_volunteer_fear.json"
    interfaith_family_online_harassment_dox_fear = root / "personas" / "interfaith_family_online_harassment_dox_fear.json"
    witness_friend_bias_motivated_assault_survivor_guilt = root / "personas" / "witness_friend_bias_motivated_assault_survivor_guilt.json"
    public_gathering_anxiety_after_mass_violence_news = root / "personas" / "public_gathering_anxiety_after_mass_violence_news.json"
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
    assert coworker_threats_after_complaint_fear.is_file()
    assert reporting_harassment_retaliation_workplace_fear.is_file()
    assert ex_stalking_at_workplace_panic_fear.is_file()
    assert violent_client_service_worker_safety_fear.is_file()
    assert workplace_lockdown_threat_panic.is_file()
    assert after_calling_police_domestic_risk_at_work.is_file()
    assert security_alarm_breach_disbelief.is_file()
    assert boss_downplays_safety_threats.is_file()
    assert cyberstalking_work_chat_phishing_fear.is_file()
    assert threatening_note_breakroom_freeze.is_file()
    assert mortgage_foreclosure_imminent_destabilizing.is_file()
    assert couch_surfing_transport_income_overwhelm.is_file()
    assert shelter_line_waiting_insomnia_panic.is_file()
    assert housing_application_rejection_deflated.is_file()
    assert rent_increase_math_panic.is_file()
    assert landlord_illegal_entry_fear.is_file()
    assert locked_out_of_home_no_phone_food_panic.is_file()
    assert deposit_refund_scam_shame_fear.is_file()
    assert utility_water_gas_cutoff_grief.is_file()
    assert roommate_threaten_eviction_split_rent.is_file()
    assert doctor_dismisses_symptoms_gaslighting_fear.is_file()
    assert er_discharge_no_followup_confusion.is_file()
    assert waiting_diagnosis_ruminating_fear.is_file()
    assert pre_surgery_anxiety_catastrophizing.is_file()
    assert medication_side_effect_fear_still_taking.is_file()
    assert lab_results_delay_hypervigilance.is_file()
    assert chronic_flare_hiding_from_family.is_file()
    assert disability_benefits_review_medical_anxiety.is_file()
    assert nurse_shift_burnout_moral_injury.is_file()
    assert needle_phobia_avoiding_care.is_file()
    assert immigration_hearing_date_insomnia_dread.is_file()
    assert asylum_case_wait_years_numbness.is_file()
    assert mixed_status_family_school_forms_fear.is_file()
    assert residency_delay_partner_abroad_lonely.is_file()
    assert lost_immigration_documents_panic_shame.is_file()
    assert workplace_wage_theft_fear_status_retaliation.is_file()
    assert international_student_postgrad_timeline_panic.is_file()
    assert airport_secondary_screening_aftermath_hypervigilance.is_file()
    assert immigration_paperwork_scam_shame_distrust.is_file()
    assert loved_one_detained_little_information_grief.is_file()
    assert sextortion_blackmail_threat_shame_cycle.is_file()
    assert intimate_content_shared_without_consent_by_ex.is_file()
    assert romance_scam_savings_lost_shame_isolation.is_file()
    assert elder_financial_exploitation_relative_control_fear.is_file()
    assert authority_impersonation_phone_scam_elder_panic.is_file()
    assert youth_online_image_pressure_fear_telling_parent.is_file()
    assert synthetic_intimate_media_fear_reputation.is_file()
    assert investment_fraud_trusted_group_chat_shame.is_file()
    assert account_takeover_phishing_panic_shame.is_file()
    assert workplace_rumor_synthetic_intimate_media_fear.is_file()
    assert sports_betting_chase_losses_shame_partner_lies.is_file()
    assert online_casino_losses_hidden_rent_panic.is_file()
    assert gambling_recovery_meeting_slip_shame_isolation.is_file()
    assert payday_loan_gambling_debt_trap_dread.is_file()
    assert athlete_coach_body_comment_restrictive_fear.is_file()
    assert compulsive_exercise_identity_rest_day_spiral.is_file()
    assert endurance_training_underfueling_fatigue_low_mood.is_file()
    assert team_performance_supplement_pressure_anxiety.is_file()
    assert sleep_deprivation_visual_weirdness_fear_mind.is_file()
    assert exam_stress_perceptual_oddity_fear_psychosis.is_file()
    assert miscarriage_early_loss_isolation_shame.is_file()
    assert recurrent_pregnancy_loss_grief_despair.is_file()
    assert stillbirth_grief_anniversary_dread.is_file()
    assert termination_medical_reasons_grief_secrecy.is_file()
    assert infertility_two_week_wait_obsessing.is_file()
    assert ivf_cycle_stimulation_exhaustion_relationship_strain.is_file()
    assert ivf_embryo_transfer_failure_numbness.is_file()
    assert ttc_partner_timeline_mismatch_resentment.is_file()
    assert pregnancy_after_prior_loss_every_symptom_panic.is_file()
    assert adoption_process_stall_ambivalent_grief.is_file()
    assert concussion_cleared_athlete_still_symptomatic_fear.is_file()
    assert college_concussion_academic_accommodations_shame.is_file()
    assert workplace_head_bump_unreported_worsening_anxiety.is_file()
    assert parent_teen_athlete_second_concussion_fear.is_file()
    assert car_crash_mild_head_injury_insurance_rumination.is_file()
    assert post_concussion_screen_light_noise_overwhelm.is_file()
    assert concussion_mood_swings_partner_guilt.is_file()
    assert concussion_word_finding_fail_meeting_humiliation.is_file()
    assert competitive_athlete_career_end_concussion_history_grief.is_file()
    assert exertion_headache_return_to_exercise_fear_spiral.is_file()
    assert pain_clinic_discontinued_abrupt_reduction_anxiety.is_file()
    assert medical_opioid_taper_chronic_pain_fear_street_thought.is_file()
    assert post_surgery_breakthrough_refill_denied_helpless.is_file()
    assert pain_contract_urine_monitoring_paranoia_shame.is_file()
    assert spouse_pain_meds_addiction_accusation_grief.is_file()
    assert young_adult_chronic_pain_er_dismissed_drug_seeking_shame.is_file()
    assert rural_pain_specialist_access_barrier_despond.is_file()
    assert pain_flare_disability_work_loss_passive_guilt.is_file()
    assert kinesiophobia_reinjury_avoidance_depression_spiral.is_file()
    assert workers_comp_pain_claim_scrutiny_isolation.is_file()
    assert paramedic_pediatric_call_intrusive_memories.is_file()
    assert firefighter_mayday_crew_injury_survivor_guilt.is_file()
    assert ems_partner_same_unit_shift_conflict_home.is_file()
    assert emergency_dispatcher_protocol_correct_still_guilty_insomnia.is_file()
    assert wildfire_deployment_exhaustion_emotional_numb_spouse.is_file()
    assert ems_scene_assault_spirit_broken_hypervigilance.is_file()
    assert firefighter_off_duty_medical_emergency_second_guessing.is_file()
    assert probationary_firefighter_station_bullying_trapped.is_file()
    assert technical_rescue_long_extrication_emotional_numbness.is_file()
    assert air_ambulance_high_acuity_detachment_family_grief.is_file()
    assert parent_metastatic_cancer_long_distance_careguilt.is_file()
    assert spouse_oncology_diagnosis_role_reversal_overwhelm.is_file()
    assert adult_child_parent_stroke_resentment_guilt_trap.is_file()
    assert sibling_psychiatric_hospitalization_family_secrecy_shame.is_file()
    assert pediatric_hospital_parent_dissociation_waiting_guilt.is_file()
    assert partner_neurodegenerative_decline_caregiver_lonely.is_file()
    assert parent_dialysis_schedule_financial_exhaustion.is_file()
    assert family_disagree_illness_disclosure_sibling_fracture.is_file()
    assert geographic_distance_parent_medical_emergency_guilt.is_file()
    assert hospice_family_decision_conflict_anticipatory_grief.is_file()
    assert public_bias_harassment_transit_hypervigilance.is_file()
    assert home_vandalism_targeted_identity_safety_fear.is_file()
    assert child_bullied_bigotry_school_parent_rage_guilt.is_file()
    assert neighbor_pattern_bias_harassment_police_report_fear.is_file()
    assert workplace_bias_incident_after_hate_event_news.is_file()
    assert community_mass_violence_news_hypervigilance_daily_life.is_file()
    assert cultural_community_space_threat_message_volunteer_fear.is_file()
    assert interfaith_family_online_harassment_dox_fear.is_file()
    assert witness_friend_bias_motivated_assault_survivor_guilt.is_file()
    assert public_gathering_anxiety_after_mass_violence_news.is_file()


def test_batch_config_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "personas" / "batch_config.json"
    assert config_path.is_file()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(data.get("personas"), list)
    assert "passive_ideation.json" in data["personas"]

