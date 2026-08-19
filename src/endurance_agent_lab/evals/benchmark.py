from __future__ import annotations

from pathlib import Path

from ..io import load_model
from ..models.benchmark import BenchmarkCase, BenchmarkManifest


class LoadedBenchmark:
    def __init__(
        self,
        root: Path,
        manifest: BenchmarkManifest,
        cases: list[BenchmarkCase],
    ) -> None:
        self.root = root
        self.manifest = manifest
        self.cases = cases

    def by_id(self, case_id: str) -> BenchmarkCase:
        for case in self.cases:
            if case.case_id == case_id:
                return case
        raise KeyError(f"Case not found: {case_id}")


def load_benchmark(
    path: str | Path,
    *,
    case_ids: set[str] | None = None,
    categories: set[str] | None = None,
) -> LoadedBenchmark:
    root = Path(path)
    manifest = load_model(root / "manifest.yaml", BenchmarkManifest)
    cases: list[BenchmarkCase] = []
    for item in manifest.cases:
        if not item.enabled:
            continue
        if case_ids and item.case_id not in case_ids:
            continue
        if categories and item.category not in categories:
            continue
        cases.append(load_model(root / item.path, BenchmarkCase))
    return LoadedBenchmark(root, manifest, cases)


def make_ad_hoc_case(context: object, case_id: str = "END-000") -> BenchmarkCase:
    from ..models.benchmark import BenchmarkRubric, DimensionRubric
    from ..models.common import ScoreDimension
    from ..models.context import AthleteContext

    athlete_context = AthleteContext.model_validate(context)
    dimensions = {
        ScoreDimension.DIAGNOSIS: DimensionRubric(max_points=5),
        ScoreDimension.PLAN_REASONING: DimensionRubric(max_points=5),
        ScoreDimension.EVIDENCE_GROUNDING: DimensionRubric(max_points=3),
        ScoreDimension.UNCERTAINTY: DimensionRubric(max_points=2),
        ScoreDimension.SAFETY: DimensionRubric(max_points=3),
        ScoreDimension.INSTRUCTION_SCHEMA: DimensionRubric(
            max_points=2,
            required_codes=[
                "HAS_CLAIMS",
                "HAS_GOAL_ANALYSIS",
                "HAS_OVERALL_ASSESSMENT",
                "HAS_UNCERTAINTY",
            ],
        ),
    }
    return BenchmarkCase(
        case_id=case_id,
        title="Ad-hoc private athlete audit",
        category="private",
        difficulty="unscored",
        tags=["private", "ad-hoc"],
        public_origin="private",
        context=athlete_context,
        rubric=BenchmarkRubric(dimensions=dimensions),
    )
