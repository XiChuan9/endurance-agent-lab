from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..io import load_model
from ..models.benchmark import BenchmarkCase, BenchmarkManifest


@dataclass(slots=True)
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cases_validated: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_benchmark(path: str | Path) -> ValidationReport:
    root = Path(path)
    report = ValidationReport()
    manifest_path = root / "manifest.yaml"
    try:
        manifest = load_model(manifest_path, BenchmarkManifest)
    except Exception as exc:
        report.errors.append(f"Manifest validation failed: {exc}")
        return report

    seen: set[str] = set()
    for item in manifest.cases:
        if item.case_id in seen:
            report.errors.append(f"Duplicate case ID in manifest: {item.case_id}")
            continue
        seen.add(item.case_id)
        case_path = root / item.path
        try:
            case = load_model(case_path, BenchmarkCase)
        except Exception as exc:
            report.errors.append(f"{item.case_id}: {exc}")
            continue
        report.cases_validated += 1
        if case.case_id != item.case_id:
            report.errors.append(
                f"{item.case_id}: case file declares mismatched ID {case.case_id}."
            )
        if case.category != item.category:
            report.errors.append(
                f"{item.case_id}: category mismatch ({case.category} != {item.category})."
            )
        total = sum(dimension.max_points for dimension in case.rubric.dimensions.values())
        if abs(total - manifest.scoring_max) > 1e-9:
            report.errors.append(
                f"{item.case_id}: rubric totals {total}, expected {manifest.scoring_max}."
            )
        required_dimensions = {
            "diagnosis",
            "plan_reasoning",
            "evidence_grounding",
            "uncertainty",
            "safety",
            "instruction_schema",
        }
        actual_dimensions = {dimension.value for dimension in case.rubric.dimensions}
        missing = required_dimensions - actual_dimensions
        if missing:
            report.errors.append(
                f"{item.case_id}: missing rubric dimensions: {', '.join(sorted(missing))}."
            )
    if len(seen) != 30:
        report.warnings.append(f"Benchmark contains {len(seen)} cases; v0.1 target is 30.")
    return report
