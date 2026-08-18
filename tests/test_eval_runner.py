from __future__ import annotations

from endurance_agent_lab.evals import load_benchmark, load_run, run_benchmark
from endurance_agent_lab.providers import RuleBasedProvider


def test_single_case_run_is_reproducible_and_reloadable(tmp_path, project_root, skill) -> None:
    benchmark = load_benchmark(
        project_root / "benchmarks" / "endurancebench-v0.1",
        case_ids={"END-016"},
    )
    run_dir, manifest, summary, records = run_benchmark(
        benchmark,
        RuleBasedProvider(),
        skill,
        runs_dir=tmp_path,
    )

    assert manifest.case_ids == ["END-016"]
    assert summary.cases_completed == 1
    assert summary.cases_failed == 0
    assert records[0].grade is not None and records[0].grade.passed
    for name in ["manifest.yaml", "records.json", "report.json", "report.md", "report.html"]:
        assert (run_dir / name).is_file()
    for name in ["case.yaml", "derived.json", "audit.json", "provider-result.json", "grade.json"]:
        assert (run_dir / "cases" / "END-016" / name).is_file()

    loaded_manifest, loaded_summary, loaded_records = load_run(run_dir)
    assert loaded_manifest.run_id == manifest.run_id
    assert loaded_summary.model == summary.model
    assert loaded_records[0].case_id == "END-016"
