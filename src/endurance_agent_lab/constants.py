from __future__ import annotations

PACKAGE_NAME = "endurance-agent-lab"
PACKAGE_VERSION = "0.1.1"
DEFAULT_BENCHMARK_PATH = "benchmarks/endurancebench-v0.1"
DEFAULT_SKILL_PATH = "skills/training-plan-auditor"
DEFAULT_RUNS_DIR = "runs"
DEFAULT_PRIVATE_DIR = "private"

RACE_DISTANCE_KM: dict[str, float] = {
    "5k": 5.0,
    "10k": 10.0,
    "half_marathon": 21.0975,
    "marathon": 42.195,
}

QUALITY_INTENSITIES = {"threshold", "race_pace", "vo2max", "sprint", "mixed"}

STANDARD_SCORE_MAX = 20.0
