# Contributing

Contributions are welcome in code, benchmark methodology, documentation, provider adapters, and expert case review.

## Start here

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
eal validate
pytest
ruff check .
mypy src/endurance_agent_lab
eal demo --clean
```

## Pull-request requirements

- Explain the user or research problem.
- Keep public/private data boundaries intact.
- Add tests for behavior changes.
- Record benchmark score movement for changes affecting prompts, claims, graders, analytics, or providers.
- Avoid unrelated formatting or dependency changes.

## Benchmark cases

A proposed case must add a distinct failure mode and include all six rubric dimensions totaling 20 points. Do not submit real athlete records. Use a synthetic reconstruction or obtain documented consent and complete de-identification review.

## Claim codes

Use an existing code when its documented meaning matches exactly. New concepts need a new code and taxonomy documentation. Do not rename or redefine released codes without a migration and version discussion.

## Human expert review

A model-generated rubric is not expert ground truth. At least one qualified endurance practitioner must review the decision structure, required claims, forbidden claims, safety boundary, and ambiguity before inclusion.
