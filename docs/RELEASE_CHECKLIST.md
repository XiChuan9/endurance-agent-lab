# Release checklist

Use this checklist before tagging a public release.

## Contracts and benchmark

- [ ] `eal validate` passes.
- [ ] Any schema change has an explicit compatibility decision and version update.
- [ ] Benchmark manifests reference only existing, valid cases.
- [ ] Rubric dimensions total 20 points for every case.
- [ ] New claim codes are documented in the taxonomy.
- [ ] Hard-fail additions are independently reviewed.

## Privacy and safety

- [ ] No file under `private/` or `runs/` is staged.
- [ ] Example and benchmark data are synthetic or irreversibly de-identified.
- [ ] No credential, precise identity, raw activity export, or medical record is present.
- [ ] Safety findings remain separate from ordinary quality scoring.

## Engineering quality

- [ ] `pytest --cov=endurance_agent_lab --cov-report=term-missing` passes the 80% gate.
- [ ] `ruff format --check .` passes.
- [ ] `ruff check .` passes.
- [ ] `mypy src/endurance_agent_lab` passes in strict mode.
- [ ] `eal demo --clean` completes all enabled cases.
- [ ] Wheel and source archive build successfully.
- [ ] The wheel works from a directory outside the source checkout.

## Reproducibility

- [ ] Release notes name benchmark, Skill, and schema versions.
- [ ] Sample reports are regenerated from the tagged source.
- [ ] Release artifacts have SHA-256 checksums.
- [ ] The Git tag points to the reviewed commit.
