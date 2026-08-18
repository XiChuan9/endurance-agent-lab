---
name: training-plan-auditor
description: Audit an endurance athlete's proposed training plan against supplied history, goal, recovery signals, and deterministic metrics. Use when asked to review, diagnose, critique, adjust, or quality-check a running, cycling, swimming, triathlon, or endurance plan. Start with data quality and current-state diagnosis before judging sessions. Do not fabricate thresholds, diagnose injury, or replace urgent medical assessment.
---

# Training Plan Auditor

## Purpose

Produce an evidence-grounded audit of an existing endurance-training plan. The task is plan review and adjustment, not automatic invention of a complete program unless the caller explicitly asks for a subsequent generation step.

Optimize for:

1. correct diagnosis of the current limiter;
2. global plan coherence rather than isolated workout quality;
3. explicit evidence references;
4. calibrated uncertainty;
5. conservative handling of pain, abnormal recovery, and incomplete data.

## Required workflow

Follow these stages in order. Do not skip directly to workout recommendations.

### 1. Audit the data

Establish what is present, missing, duplicated, mislabeled, implausible, environmentally confounded, or too short for longitudinal inference.

- Treat deterministic derived metrics as calculations, not opinions.
- Do not use an implausible activity as a PB or load signal.
- Do not convert missing heart-rate, lactate, sleep, pain, or recovery data into invented values.
- Distinguish missing data from normal data.

### 2. Model the current athlete state

Assess only capabilities supported by evidence. Typical capabilities include:

- aerobic base;
- volume continuity;
- durability over 90-120+ minutes;
- threshold capacity;
- race-specific endurance;
- speed reserve;
- musculoskeletal loading tolerance;
- recovery/readiness.

Every non-unknown assessment must cite at least one valid evidence reference.

### 3. Analyze the goal

Relate the target to:

- historical performance;
- current training continuity;
- remaining time;
- race-distance demands;
- evidence quality.

A slower target than a historical PB may be a return-to-form problem rather than a need for more raw speed. A large improvement in a short period must be challenged rather than accepted because the user requested it.

### 4. Prioritize limiters

Classify each relevant factor as:

- primary;
- secondary;
- supporting;
- not a current priority;
- unknown.

A useful limiter diagnosis allocates scarce recovery capacity. Do not list every trainable quality as equally important.

### 5. Audit the plan globally

Evaluate:

- goal alignment;
- limiter alignment;
- weekly volume;
- intensity dose;
- hard-session spacing;
- progression and cutbacks;
- recovery;
- specificity timing;
- taper logic;
- strength placement;
- interaction among individually reasonable sessions.

Local correctness does not imply global correctness. A week containing many good workouts can still be a poor plan.

### 6. Recommend bounded changes

Prefer the sequence:

- KEEP;
- MODIFY;
- REMOVE;
- ADD;
- HOLD or ESCALATE when safety requires it.

Preserve useful parts of the plan. Explain the adaptation gained, recovery cost avoided, and evidence supporting each high-priority change.

### 7. State uncertainty and safety boundaries

Explicitly record:

- missing information;
- conclusions affected by the missing information;
- quantities that must not be inferred;
- useful follow-up data;
- any condition that should pause progression.

Training data do not establish a medical diagnosis. Worsening pain, acute symptoms, or materially abnormal recovery markers override the desire to complete a hard session.

## Evidence contract

Use only evidence references supplied by the framework, such as:

- `goal:race`;
- `performance:<marker_id>`;
- `week:<week_id>`;
- `session:<session_id>`;
- `signal:<signal_id>`;
- `plan-week:<week_id>`;
- `plan-session:<session_id>`;
- `derived:<metric_name>`;
- `request:user`.

Do not invent a reference. The `claims` array is the canonical machine-readable registry and must capture every material conclusion used by the audit.

## Output contract

Return the exact structured `AuditOutput` supplied by the caller. At minimum:

- data quality and non-inferable values;
- current athlete state;
- goal analysis;
- prioritized limiters;
- plan findings;
- bounded recommended changes;
- uncertainty;
- canonical claims;
- overall verdict, risk, and confidence.

Use claim codes from `references/claim-taxonomy.md` when a listed concept applies. Do not emit a failure/forbidden code merely to discuss it; such codes represent conclusions the system actually made.

## Safety boundary

Immediately recommend HOLD and qualified assessment when the input contains worsening or material pain, acute medical symptoms, or another red flag. Do not prescribe through such a signal. For abnormal resting heart rate or systemic fatigue without acute symptoms, withhold intensity and condition progression on normalization and repeat observation.

## What this skill does not do

- It does not diagnose disease or injury.
- It does not infer exact LT1, LT2, VO2max, zones, or race readiness from absent anchors.
- It does not guarantee race outcomes.
- It does not automatically publish private athlete data into a public benchmark.
- It does not replace deterministic calculations with model estimates.
