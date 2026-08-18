# Expert Labeling Protocol

## Case authoring

Start from a real professional decision pattern, not a desired model failure. Remove identity and reconstruct a minimal synthetic context that preserves the trade-off.

## Independent passes

A reviewer should separately answer:

1. What data problem must be recognized first?
2. What is the primary limiter and why?
3. Which attractive but wrong diagnosis is most likely?
4. What plan architecture is unsafe or misaligned?
5. What cannot be inferred?
6. What behavior deserves hard failure?

Only then compare with the proposed rubric.

## Rubric standards

Required claims must be necessary for a competent answer. Optional claims must add value without enforcing one coaching style. Forbidden claims must represent a genuine error, not a different reasonable wording. Hard failures are reserved for invalidating safety, hallucination, or professional-judgment failures.

## Disagreement

Record expert disagreement rather than hiding it. If the primary diagnosis is genuinely ambiguous, either add evidence, reduce the required claim, split the case, or mark alternative acceptable claims. Do not force false consensus.

## Human score data

When collecting human grades, store reviewer role, rubric version, timestamp, confidence, rationale, and conflicts. Do not treat an unreviewed model judge as ground truth.
