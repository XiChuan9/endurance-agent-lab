# Structured output contract

The framework supplies a Pydantic/JSON Schema named `AuditOutput`. The response must validate without field deletion or coercion.

The `claims` array is canonical for grading. Each claim requires:

- stable code;
- category;
- stance;
- priority;
- concise statement;
- valid evidence references;
- calibrated confidence from 0 to 1.

Narrative sections may elaborate, but must not contradict the canonical claims.

Confidence is epistemic confidence in the conclusion given the supplied evidence. It is not the probability that an athlete will achieve the race goal.
