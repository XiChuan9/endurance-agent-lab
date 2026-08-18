## Purpose

Describe the problem and why this is the smallest useful change.

## Change type

- [ ] Framework/runtime
- [ ] Benchmark case or rubric
- [ ] Skill or reference material
- [ ] Documentation
- [ ] Maintenance

## Evidence

- [ ] `eal validate`
- [ ] `pytest --cov=endurance_agent_lab --cov-report=term-missing`
- [ ] `ruff format --check .`
- [ ] `ruff check .`
- [ ] `mypy src/endurance_agent_lab`
- [ ] `eal demo --clean`

## Benchmark and privacy review

- [ ] No real athlete identity, raw activity export, credential, or private longitudinal record is included.
- [ ] New/changed claims have stable codes and evidence expectations.
- [ ] Hard-fail changes are justified in the PR description.
- [ ] Synthetic or de-identified case provenance is documented.

## Compatibility

State any schema, CLI, benchmark-version, or provider behavior change.
