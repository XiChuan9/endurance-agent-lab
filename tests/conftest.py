from __future__ import annotations

from pathlib import Path

import pytest

from endurance_agent_lab.evals import LoadedBenchmark, load_benchmark
from endurance_agent_lab.skills import SkillBundle, load_skill


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = PROJECT_ROOT / "benchmarks" / "endurancebench-v0.1"
SKILL_ROOT = PROJECT_ROOT / "skills" / "training-plan-auditor"


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def benchmark() -> LoadedBenchmark:
    return load_benchmark(BENCHMARK_ROOT)


@pytest.fixture(scope="session")
def skill() -> SkillBundle:
    return load_skill(SKILL_ROOT)
