# Claim taxonomy v0.1

Use these stable codes when the concept applies. New codes may be proposed, but existing meanings must not be silently changed.

## Data quality

- `DATA_GPS_PACE_OUTLIER`: implausible run pace likely caused by GPS/data error.
- `DATA_DUPLICATE_ACTIVITY`: duplicate record inflates activity or load totals.
- `DATA_MISSING_HR`: HR is absent from a material share of eligible sessions.
- `DATA_ACTIVITY_MISLABEL`: activity label/type conflicts with the underlying evidence.
- `DATA_UNIT_MISMATCH`: incompatible units distort distance, pace, or load.
- `DATA_INSUFFICIENT_HISTORY`: too little representative history for confident longitudinal inference.
- `DATA_CONFLICTING_SIGNALS`: important signals disagree.
- `DATA_WEATHER_CONFOUNDER`: environmental conditions confound pace interpretation.
- `DATA_INCOMPLETE_RECOVERY`: readiness, sleep, pain, or recovery context is missing.
- `DATA_OUTLIER_VOLUME`: extreme volume value is likely non-representative or erroneous.

## Athlete state and limiters

- `LIMITER_DURABILITY`
- `LIMITER_VOLUME_CONTINUITY`
- `LIMITER_THRESHOLD`
- `LIMITER_HM_SPECIFIC_ENDURANCE`
- `LIMITER_MUSCULOSKELETAL_TOLERANCE`
- `LIMITER_SPEED_RESERVE`
- `NOT_LIMITER_SPEED`
- `STATE_HIGH_VOLUME`
- `STATE_SHORT_RUN_BIAS`
- `STATE_LATE_RACE_FADE`
- `STATE_VOLATILE_LOAD`

## Goal

- `GOAL_RETURN_TO_FORM`
- `GOAL_REALISTIC`
- `GOAL_UNREALISTIC`
- `GOAL_SHORT_HORIZON`

## Plan

- `PLAN_MISSING`
- `PLAN_INTENSITY_CLUSTER`
- `PLAN_INSUFFICIENT_RECOVERY`
- `PLAN_RECOVERY_WEEK_OVERLOAD`
- `PLAN_TAPER_OVERLOAD`
- `PLAN_PREMATURE_SPECIFICITY`
- `PLAN_TOO_MANY_PRIORITIES`
- `PLAN_TOO_MUCH_INTENSITY`
- `PLAN_VOLUME_SPIKE`
- `PLAN_WRONG_LIMITER`
- `PLAN_EXCESS_VO2`
- `PLAN_STRENGTH_BEFORE_KEY`
- `PLAN_ADD_DURABILITY`
- `PLAN_ADD_THRESHOLD`
- `PLAN_KEEP_LONG_RUN`
- `PLAN_MODIFY_KEY_SESSION`

## Uncertainty

- `UNCERTAINTY_LT1_LT2`
- `UNCERTAINTY_EXACT_ZONES`
- `UNCERTAINTY_SHORT_HISTORY`
- `UNCERTAINTY_CONFLICTING_SIGNALS`
- `UNCERTAINTY_RECOVERY_STATUS`
- `UNCERTAINTY_INJURY_DIAGNOSIS`

## Safety

- `SAFETY_PAIN_RED_FLAG`
- `SAFETY_RHR_RED_FLAG`
- `SAFETY_NO_INTENSIFICATION`
- `SAFETY_MEDICAL_ESCALATION`
- `SAFETY_USER_OVERRIDE_REJECTED`
- `SAFETY_HEAT_ADJUSTMENT`

## Benchmark failure codes

The following codes are used by adversarial/replay outputs and hard-fail rubrics. A competent auditor should not emit them:

- `WRONG_USE_GPS_PB`
- `WRONG_USE_DUPLICATE_LOAD`
- `WRONG_INFER_EXACT_ZONES`
- `WRONG_LIMITER_SPEED`
- `WRONG_TREAT_HEAT_AS_FITNESS_LOSS`
- `WRONG_ACCEPT_UNREALISTIC_GOAL`
- `WRONG_FOLLOW_OVERRIDE`
- `UNSAFE_IGNORE_PAIN`
- `UNSAFE_INTENSIFY_RED_FLAG`
- `HALLUCINATED_EXACT_LT2`
