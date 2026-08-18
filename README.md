# Endurance Agent Lab

**Endurance Agent Lab is an open-source evaluation and engineering framework for building reliable AI endurance-coaching agents from expert-labeled cases, reusable skills, deterministic tools, longitudinal athlete scenarios, and reproducible model evaluations.**

It is not another chat wrapper that asks a model to “act as a running coach.” The project separates five things that are often mixed together:

1. deterministic calculation;
2. professional interpretation;
3. structured claims and evidence;
4. benchmark grading;
5. private longitudinal coaching work.

The same core can therefore serve a coach today, support model research tomorrow, and remain suitable for a future commercial application without making private athlete data part of the open repository.

## What v0.1 includes

- A Codex/ChatGPT-compatible `training-plan-auditor` Skill.
- A strict `AthleteContext` input contract and `AuditOutput` output contract.
- Deterministic metrics for volume continuity, long-run exposure, quality-session density, target pace, historical speed reserve, missing HR, duplicates, and obvious outliers.
- `EnduranceBench v0.1`: 30 expert-rubric cases across data quality, diagnosis, plan critique, goal/specificity, uncertainty, and safety/adversarial behavior.
- Six-dimension scoring: diagnosis 5, plan reasoning 5, evidence grounding 3, uncertainty 2, safety 3, schema/instruction compliance 2.
- Claim-code grading, valid evidence-reference checks, forbidden claims, and hard-fail rules.
- A zero-cost transparent rules provider for installation tests and regression checks.
- An OpenAI Responses API provider using Pydantic Structured Outputs.
- A replay adapter for evaluating outputs produced by other models or systems.
- Reproducible run manifests, per-case artifacts, Markdown reports, and standalone HTML reports.
- A private longitudinal athlete track that is excluded from Git by default.

## Quick start

Requirements: Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

eal doctor
eal validate
eal demo --clean
```

The demo makes no network call and requires no API key. It runs all 30 cases through the transparent baseline and writes a complete run under `runs/`. The rules baseline is a **pipeline regression oracle intentionally aligned to v0.1 claim codes**; its expected 100% score proves wiring and contracts, not general coaching intelligence.

Open the generated `report.html` in a browser. A committed sample is available under `examples/reports/`.

## Audit the return-to-form half-marathon case

`END-016` represents an anonymized/synthetic decision structure in which an athlete with a historical half-marathon capacity around 66 minutes is rebuilding toward a 70-minute target. Recent continuity and durability are weak while raw speed is already demonstrated.

```bash
eal audit --case END-016 --provider rules
```

Generated artifacts:

```text
runs/audit-...-END-016/
├── context.yaml
├── derived.json
├── audit.json
├── audit.md
└── provider-result.json
```

## Use OpenAI

Install the optional provider and configure a key:

```bash
pip install -e ".[openai]"
cp .env.example .env
# Set OPENAI_API_KEY in .env

eal audit --case END-016 --provider openai --model gpt-5.6-luna
eal eval --provider openai --model gpt-5.6-luna --case END-016 --case END-026
```

The adapter uses the Responses API and parses directly into the versioned `AuditOutput` Pydantic model. Model names remain configuration, not benchmark semantics.

## Evaluate output from another model or system

Write one structured `AuditOutput` JSON file per case as either `<replay-dir>/END-016.json` or `<replay-dir>/END-016/audit.json`, then run the same deterministic graders:

```bash
eal audit --case END-016 --provider replay \
  --replay-dir examples/replay --model external-system

eal eval --provider replay --replay-dir examples/replay \
  --model external-system --case END-016
```

This keeps benchmark semantics independent of any model provider. `examples/replay/END-016.json` is a valid synthetic sample, not a claim about external-model performance.

## Use it for a real athlete

Real athlete work belongs under `private/`, which is Git-ignored.

```bash
eal track init athlete-001
cp examples/private-athlete-context.template.yaml private/athlete-001-context.yaml
# Edit the context with consented athlete data.

eal track add athlete-001 private/athlete-001-context.yaml \
  --effective-date 2026-08-18 \
  --notes "Initial post-recovery assessment"

eal track audit athlete-001 --provider rules
```

For weekly work:

1. preserve the previous snapshot;
2. add actual completed training and new recovery signals;
3. add a new snapshot;
4. rerun the audit;
5. compare changed claims and plan recommendations;
6. keep any public case extraction separate and irreversibly de-identified.

See [the Chinese operating guide](docs/MVP_OPERATING_GUIDE.zh-CN.md).

## Architecture

```text
raw/private athlete records
          │
          ▼
    AthleteContext
          │
          ├──────────────► deterministic analytics
          │                       │
          ▼                       ▼
training-plan-auditor Skill + derived metrics
          │
          ▼
 provider adapter (rules / OpenAI / replay / future local model)
          │
          ▼
      AuditOutput
          │
          ├──────────────► coach-facing Markdown report
          │
          └──────────────► claim/evidence graders
                                  │
                                  ▼
                          reproducible eval run
```

Public and private paths are deliberately separate:

```text
benchmarks/   public, versioned, reviewable
skills/       public workflow knowledge
src/          public framework
examples/     synthetic only
private/      real athlete data; never commit
runs/         generated local artifacts; not source data
```

## CLI

| Command | Purpose |
|---|---|
| `eal doctor` | Verify Python, Skill, benchmark, optional OpenAI readiness, and privacy defaults. |
| `eal validate` | Validate all 30 cases, manifest references, schema contracts, and rubric totals. |
| `eal demo` | Run a zero-cost end-to-end regression. |
| `eal audit` | Audit one public case or private `AthleteContext`. |
| `eal eval` | Run a reproducible multi-case evaluation. |
| `eal report` | Regenerate reports from recorded artifacts. |
| `eal schema export` | Export public JSON Schemas. |
| `eal track ...` | Manage a private longitudinal athlete record. |

## Why claims instead of answer similarity?

There is rarely one correct paragraph for an endurance decision. EnduranceBench scores stable professional claims, evidence use, uncertainty, and unsafe behavior rather than textual similarity to a reference essay.

A case can require:

```yaml
required_codes:
  - LIMITER_DURABILITY
  - NOT_LIMITER_SPEED
forbidden_codes:
  - WRONG_LIMITER_SPEED
hard_fail_if:
  - code: WRONG_LIMITER_SPEED
    reason: Raw speed was named as the main limiter despite demonstrated reserve.
```

This permits multiple valid coaching explanations while making core errors machine-testable.

## Reproducibility

Every run records:

- benchmark ID, version, and tree hash;
- Skill name and tree hash;
- provider and model configuration;
- Python and package versions;
- Git commit when available;
- selected case IDs;
- raw provider response;
- parsed audit;
- derived metrics;
- deterministic grade;
- aggregate reports.

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Safety and scope

This project is a training-decision aid and research framework. It is not a medical device, does not diagnose injury or disease, and does not guarantee race outcomes. Worsening pain, acute symptoms, or material recovery abnormalities must not be overridden by a training plan.

## Open-source and commercial boundary

The open core contains the benchmark, schemas, Skill, deterministic analytics, provider adapters, graders, CLI, and sample cases. A future commercial service can add consented data connectors, coach workflow, team management, private knowledge, preference data, report delivery, and operations without closing the public evaluation layer. See [docs/COMMERCIAL_BOUNDARY.md](docs/COMMERCIAL_BOUNDARY.md).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Benchmark methodology](BENCHMARK.md)
- [Expert labeling](docs/EXPERT_LABELING.md)
- [Failure taxonomy](docs/FAILURE_TAXONOMY.md)
- [Privacy](PRIVACY.md)
- [Reproducibility](REPRODUCIBILITY.md)
- [OpenAI ecosystem contribution](docs/OPENAI_CONTRIBUTION.md)
- [Roadmap](ROADMAP.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)

## License

Apache License 2.0. Athlete data remain governed by consent, privacy law, and the project's privacy policy regardless of code license.
