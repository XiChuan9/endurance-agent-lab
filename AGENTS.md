# Endurance Agent Lab

## Mission

Build reliable, reproducible, privacy-preserving AI endurance-coaching agents from expert-labeled cases, reusable skills, deterministic tools, longitudinal scenarios, and provider-neutral evaluations.

## Non-negotiable rules

- Never commit private athlete data. `private/` and `runs/` are local artifacts.
- Do not turn missing physiological or recovery data into invented values.
- Deterministic calculations belong in `analytics/`; model interpretation belongs in providers/skills.
- Public benchmark cases must be synthetic, consented, or irreversibly de-identified.
- A benchmark semantic change requires a benchmark version change.
- A claim code's meaning is stable after release. Add a new code rather than silently redefining an old one.
- Every code change must preserve `eal validate`, tests, and the zero-cost `eal demo` path.
- OpenAI integration is first-class but the core benchmark and grader remain provider-neutral.

## Development workflow

1. Read the nearest relevant module and tests.
2. Make the smallest coherent change.
3. Add or update tests.
4. Run `eal validate`.
5. Run `pytest`.
6. Run `ruff check .` and `mypy src/endurance_agent_lab` when development dependencies are installed.
7. Run `eal demo --clean` for changes touching schemas, providers, graders, reports, or benchmark cases.
8. Explain any benchmark score movement in the PR.

## Repository boundaries

- `src/endurance_agent_lab/`: framework implementation.
- `skills/`: reusable Agent Skills.
- `benchmarks/`: public versioned cases and expert rubrics.
- `examples/`: synthetic examples only.
- `private/`: real athlete workspaces; never commit.
- `runs/`: reproducible generated artifacts; normally not committed except curated release reports.
- `schemas/`: exported public contracts.

## Benchmark contribution quality bar

A new case needs a distinct failure mode, realistic context, valid evidence references, all six scoring dimensions totaling 20 points, forbidden/hard-fail behavior where applicable, and an expert note explaining why the case matters.
