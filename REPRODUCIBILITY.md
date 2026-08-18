# Reproducibility

A score without the benchmark, Skill, provider configuration, and code state is not reproducible evidence.

## Reproduce the local baseline

```bash
git clone <repository>
cd endurance-agent-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
eal validate
eal demo --clean
```

The rules provider is deterministic. Minor latency fields and the timestamped run ID differ; claims and grades should not.

## Run manifest

Each run records:

- `benchmark_id` and semantic version;
- benchmark SHA-256 tree hash;
- Skill name and SHA-256 tree hash;
- provider/model/reasoning configuration;
- selected case IDs;
- Python and package versions;
- Git commit when available.

## Per-case evidence

Each case directory stores:

```text
case.yaml
├── exact benchmark input and rubric
derived.json
├── deterministic metrics
provider-result.json
├── provider metadata and raw response
audit.json
├── parsed AuditOutput
grade.json
└── deterministic score and misses
```

## External model outputs

Export one `AuditOutput` JSON per case and evaluate it without giving the external provider access to rubric labels:

```text
external-outputs/
├── END-001.json
├── END-002.json
└── ...
```

```bash
eal eval --provider replay --replay-dir external-outputs --model external-model-name
```

## Public result policy

A published result should include the generated manifest and report, provider settings, date, model identifier or snapshot where available, and a note about any manual retry or excluded case. Do not publish private athlete runs.
