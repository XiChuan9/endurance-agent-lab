from __future__ import annotations

from pydantic import Field

from .common import ScoreDimension, StrictModel
from .context import AthleteContext


class DimensionRubric(StrictModel):
    max_points: float = Field(gt=0)
    required_codes: list[str] = Field(default_factory=list)
    optional_codes: list[str] = Field(default_factory=list)
    forbidden_codes: list[str] = Field(default_factory=list)
    notes: str | None = None


class HardFailRule(StrictModel):
    code: str
    reason: str


class BenchmarkRubric(StrictModel):
    dimensions: dict[ScoreDimension, DimensionRubric]
    hard_fail_if: list[HardFailRule] = Field(default_factory=list)
    minimum_valid_evidence_ratio: float = Field(default=0.7, ge=0.0, le=1.0)
    expert_notes: str | None = None


class BenchmarkCase(StrictModel):
    schema_version: str = "1.0"
    case_id: str = Field(pattern=r"^END-[0-9]{3}$")
    title: str
    category: str
    difficulty: str = "medium"
    tags: list[str] = Field(default_factory=list)
    public_origin: str = "synthetic"
    context: AthleteContext
    rubric: BenchmarkRubric


class ManifestCase(StrictModel):
    case_id: str
    path: str
    category: str
    enabled: bool = True


class BenchmarkManifest(StrictModel):
    schema_version: str = "1.0"
    benchmark_id: str
    version: str
    title: str
    description: str
    license: str = "Apache-2.0"
    scoring_max: float = 20.0
    cases: list[ManifestCase]
