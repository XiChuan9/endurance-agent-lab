from __future__ import annotations

import platform
import re
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from ..analytics.derived import derive_metrics
from ..constants import PACKAGE_VERSION
from ..graders import grade_case
from ..io import atomic_write_text, dump_data, load_model
from ..models.run import (
    CaseRunRecord,
    RunConfigRecord,
    RunManifest,
    RunSummary,
)
from ..providers.base import AuditProvider
from ..rendering import render_run_html, render_run_markdown
from ..skills.loader import SkillBundle
from ..utils import compact_timestamp, get_git_commit, sha256_tree, utc_now
from .aggregate import aggregate_run
from .benchmark import LoadedBenchmark


def run_benchmark(
    benchmark: LoadedBenchmark,
    provider: AuditProvider,
    skill: SkillBundle,
    *,
    runs_dir: str | Path,
    workers: int = 1,
    reasoning_effort: str | None = None,
    clean: bool = False,
) -> tuple[Path, RunManifest, RunSummary, list[CaseRunRecord]]:
    safe_model = re.sub(r"[^A-Za-z0-9_.-]+", "-", provider.model).strip("-")
    run_id = f"{compact_timestamp()}-{provider.name}-{safe_model}"
    run_dir = Path(runs_dir) / run_id
    if run_dir.exists() and clean:
        import shutil

        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest = RunManifest(
        run_id=run_id,
        created_at=utc_now(),
        benchmark_id=benchmark.manifest.benchmark_id,
        benchmark_version=benchmark.manifest.version,
        benchmark_hash=sha256_tree(benchmark.root),
        skill_name=skill.metadata.name,
        skill_hash=skill.sha256,
        config=RunConfigRecord(
            provider=provider.name,
            model=provider.model,
            workers=workers,
            reasoning_effort=reasoning_effort,
            benchmark_path=str(benchmark.root),
            skill_path=str(skill.root),
        ),
        git_commit=get_git_commit(),
        python_version=platform.python_version(),
        package_version=PACKAGE_VERSION,
        case_ids=[case.case_id for case in benchmark.cases],
    )
    dump_data(manifest, run_dir / "manifest.yaml")

    records_by_id: dict[str, CaseRunRecord] = {}
    if workers == 1:
        for case in benchmark.cases:
            record = _run_case(run_dir, case, provider, skill)
            records_by_id[case.case_id] = record
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map: dict[Future[CaseRunRecord], str] = {
                executor.submit(_run_case, run_dir, case, provider, skill): case.case_id
                for case in benchmark.cases
            }
            for future in as_completed(future_map):
                case_id = future_map[future]
                try:
                    records_by_id[case_id] = future.result()
                except Exception as exc:  # defensive boundary around worker execution
                    records_by_id[case_id] = CaseRunRecord(
                        case_id=case_id,
                        status="error",
                        error=str(exc),
                    )

    records = [records_by_id[case.case_id] for case in benchmark.cases]
    dump_data(
        [record.model_dump(mode="json", exclude_none=True) for record in records],
        run_dir / "records.json",
    )
    summary = aggregate_run(run_id, provider.name, provider.model, records, benchmark.cases)
    write_run_reports(run_dir, manifest, summary, records)
    return run_dir, manifest, summary, records


def _run_case(
    run_dir: Path,
    case: object,
    provider: AuditProvider,
    skill: SkillBundle,
) -> CaseRunRecord:
    from ..models.benchmark import BenchmarkCase

    benchmark_case = BenchmarkCase.model_validate(case)
    case_dir = run_dir / "cases" / benchmark_case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    dump_data(benchmark_case, case_dir / "case.yaml")
    derived = derive_metrics(benchmark_case.context)
    dump_data(derived, case_dir / "derived.json")
    try:
        result = provider.audit(benchmark_case, skill, derived)
        grade = grade_case(benchmark_case, result.audit, derived)
        dump_data(result.audit, case_dir / "audit.json")
        dump_data(result, case_dir / "provider-result.json")
        dump_data(grade, case_dir / "grade.json")
        return CaseRunRecord(
            case_id=benchmark_case.case_id,
            status="completed",
            provider_result=result,
            grade=grade,
        )
    except Exception as exc:
        atomic_write_text(case_dir / "error.txt", f"{type(exc).__name__}: {exc}\n")
        return CaseRunRecord(
            case_id=benchmark_case.case_id,
            status="error",
            error=f"{type(exc).__name__}: {exc}",
        )


def write_run_reports(
    run_dir: str | Path,
    manifest: RunManifest,
    summary: RunSummary,
    records: list[CaseRunRecord],
) -> None:
    root = Path(run_dir)
    dump_data(summary, root / "report.json")
    atomic_write_text(root / "report.md", render_run_markdown(manifest, summary, records))
    atomic_write_text(root / "report.html", render_run_html(manifest, summary, records))


def load_run(run_dir: str | Path) -> tuple[RunManifest, RunSummary, list[CaseRunRecord]]:
    root = Path(run_dir)
    manifest = load_model(root / "manifest.yaml", RunManifest)
    summary = load_model(root / "report.json", RunSummary)
    raw_records = __import__("json").loads((root / "records.json").read_text(encoding="utf-8"))
    records = [CaseRunRecord.model_validate(item) for item in raw_records]
    return manifest, summary, records
