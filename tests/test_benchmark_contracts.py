from __future__ import annotations

from endurance_agent_lab.analytics import validate_benchmark
from endurance_agent_lab.evals import LoadedBenchmark


def test_v01_benchmark_has_30_valid_cases(project_root) -> None:
    report = validate_benchmark(project_root / "benchmarks" / "endurancebench-v0.1")
    assert report.ok, report.errors
    assert report.cases_validated == 30


def test_case_ids_and_rubrics_are_unique_and_total_20(benchmark: LoadedBenchmark) -> None:
    case_ids = [case.case_id for case in benchmark.cases]
    assert len(case_ids) == len(set(case_ids)) == 30
    for case in benchmark.cases:
        assert sum(item.max_points for item in case.rubric.dimensions.values()) == 20
