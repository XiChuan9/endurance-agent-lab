# Architecture

## Design principles

1. Provider-neutral core, OpenAI first-class integration.
2. Deterministic calculations before model interpretation.
3. Strict schemas at every persisted boundary.
4. Canonical claims with evidence IDs.
5. Public benchmark separate from private coaching data.
6. Reproducible run artifacts rather than leaderboard-only results.
7. Safety hard failures separate from ordinary quality scores.

## Modules

### Models

Pydantic models define athlete context, audit output, benchmark cases, grades, run manifests, and longitudinal tracks. `extra="forbid"` prevents unnoticed schema drift.

### Analytics

`derive_metrics` calculates target pace, historical target relation, load continuity, long-duration exposure, quality density, missing HR, duplicates, and basic outliers. These values are injected into the model task and recorded for grading.

### Skill

`skills/training-plan-auditor/` contains OpenAI-compatible `SKILL.md`, reference policies, scripts, and the exported output schema. The Skill describes process and professional boundaries; deterministic code remains in the package.

### Providers

Providers implement one interface and return `ProviderResult`. The rules provider proves the pipeline locally, the OpenAI provider uses Structured Outputs, and replay evaluates externally generated JSON.

### Graders

The deterministic grader reads canonical claim codes, validates evidence references, applies dimension rubrics, detects forbidden codes, and enforces hard failures.

### Runner

The runner binds benchmark, Skill, provider, grader, environment, and commit into a versioned run directory. It never needs to know provider-specific business logic.

### Longitudinal store

Private tracks preserve immutable context snapshots and attach audits. Future versions will add explicit belief/decision diffs and observed outcomes.

## Extension points

- new provider: implement `AuditProvider`;
- new domain Skill: add a separate skill bundle;
- new benchmark pack: add a versioned manifest and cases;
- new grader: preserve `CaseGrade` output or version the protocol;
- new deterministic metric: add to `DerivedMetrics` and its evidence registry;
- production application: consume `AthleteContext` and `AuditOutput` without importing benchmark labels.
