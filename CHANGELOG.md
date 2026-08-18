# Changelog

All notable changes follow Keep a Changelog. The project uses Semantic Versioning.

## [0.1.0] - 2026-08-18

### Added

- Provider-neutral training-plan audit protocol with strict Pydantic contracts.
- OpenAI Responses API adapter using Structured Outputs.
- Deterministic rule-based provider for zero-cost installation and regression checks.
- Replay provider for scoring externally generated model outputs.
- EnduranceBench v0.1 with 30 expert-rubric cases across six categories.
- Six-dimension, 20-point claim/evidence/safety grading and hard-fail handling.
- Reproducible run manifests, per-case artifacts, Markdown reports, and standalone HTML reports.
- Private longitudinal athlete workspace with immutable, hashed snapshots.
- Codex/ChatGPT-compatible `training-plan-auditor` Skill and supporting references/scripts.
- Standalone wheel packaging that includes the benchmark, Skill, schemas, and default configuration.
- CLI commands for doctoring, validation, single audits, eval runs, report regeneration, schema export, and longitudinal tracks.
- Apache-2.0 licensing, governance, privacy, security, contribution, benchmark, and reproducibility documentation.
- GitHub Actions quality matrix for Python 3.11–3.13, wheel smoke testing, Dependabot, issue templates, and contribution gates.
- Twelve automated tests with an 80% minimum coverage gate.
