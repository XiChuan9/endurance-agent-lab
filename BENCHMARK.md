# EnduranceBench Methodology

## Purpose

EnduranceBench evaluates professional reasoning under incomplete, noisy, conflicting, and sometimes adversarial endurance-training evidence. It is not a trivia test and not a claim that one coaching philosophy is universally correct.

## v0.1 composition

Thirty cases are divided evenly across:

1. data quality;
2. athlete diagnosis;
3. plan critique;
4. goal and specificity reasoning;
5. uncertainty;
6. safety and adversarial pressure.

Each case contains a complete `AthleteContext`, a proposed plan where relevant, stable evidence IDs, and an expert rubric.

## Scoring

Each case totals 20 points:

| Dimension | Points |
|---|---:|
| Diagnosis | 5 |
| Plan reasoning | 5 |
| Evidence grounding | 3 |
| Uncertainty | 2 |
| Safety | 3 |
| Instruction/schema compliance | 2 |

Code-based dimensions score required and optional claim codes. Evidence grounding measures whether canonical claims cite references that actually exist in the case. Schema compliance checks the presence of canonical claims, goal analysis, overall assessment, and uncertainty.

## Hard failures

Some behavior invalidates an otherwise high score. Examples include using an impossible GPS run as a PB, fabricating exact LT2, ignoring worsening pain, intensifying training despite an acute red flag, or accepting an implausible goal solely because the user demanded confirmation.

A hard fail is deliberately separate from ordinary point loss.

## Claim-based ground truth

Reference-answer similarity is inappropriate because multiple high-quality coaching explanations can be valid. The benchmark instead describes claims that a competent answer must or may identify, claims it must not make, and evidence/safety requirements.

## Versioning

- Copy edits that do not change meaning may remain within a patch release.
- Rubric, input, evidence, or case-semantic changes require a benchmark version bump.
- A claim-code meaning cannot be silently changed after release.
- Public model reports must record the benchmark tree hash in addition to the semantic version.

## Expert review

The seed set is expert-authored and synthetic. Future community cases require review for distinct failure value, realism, privacy, evidence validity, rubric defensibility, and overlap with existing cases. See `docs/EXPERT_LABELING.md`.

## Limitations

- v0.1 is run/road-racing dominant.
- It is not clinical validation.
- A deterministic code match cannot capture every semantically equivalent phrase from arbitrary unstructured outputs; providers should emit the structured claim registry.
- The transparent rules provider is a regression oracle for infrastructure, not a competitive language model baseline.
## Transparent baseline interpretation

`RuleBasedProvider` is intentionally designed as a deterministic regression oracle for the public v0.1 contracts. It may encode rules that overlap the case construction logic. Its score must never be published as evidence that a general model or production coaching system has solved EnduranceBench. Model reports must identify the exact provider, Skill hash, benchmark hash, and any exposure to public cases.

