from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from .audit import AuditOutput
from .common import ScoreDimension, StrictModel


class UsageRecord(StrictModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class ProviderResult(StrictModel):
    provider: str
    model: str
    audit: AuditOutput
    raw_response: dict[str, Any] = Field(default_factory=dict)
    usage: UsageRecord = Field(default_factory=UsageRecord)
    latency_seconds: float = Field(ge=0)
    request_id: str | None = None


class DimensionGrade(StrictModel):
    dimension: ScoreDimension
    score: float = Field(ge=0)
    max_points: float = Field(gt=0)
    required_hits: list[str] = Field(default_factory=list)
    required_misses: list[str] = Field(default_factory=list)
    optional_hits: list[str] = Field(default_factory=list)
    forbidden_hits: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CaseGrade(StrictModel):
    case_id: str
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    passed: bool
    hard_fail: bool = False
    hard_fail_reasons: list[str] = Field(default_factory=list)
    dimensions: list[DimensionGrade] = Field(default_factory=list)
    valid_evidence_ratio: float = Field(ge=0.0, le=1.0)
    invalid_evidence_references: list[str] = Field(default_factory=list)
    claim_codes: list[str] = Field(default_factory=list)


class RunConfigRecord(StrictModel):
    provider: str
    model: str
    workers: int = Field(ge=1)
    reasoning_effort: str | None = None
    benchmark_path: str
    skill_path: str


class RunManifest(StrictModel):
    schema_version: str = "1.0"
    run_id: str
    created_at: datetime
    benchmark_id: str
    benchmark_version: str
    benchmark_hash: str
    skill_name: str
    skill_hash: str
    config: RunConfigRecord
    git_commit: str | None = None
    python_version: str
    package_version: str
    case_ids: list[str]


class CaseRunRecord(StrictModel):
    case_id: str
    status: str
    provider_result: ProviderResult | None = None
    grade: CaseGrade | None = None
    error: str | None = None


class CategoryScore(StrictModel):
    category: str
    score: float
    max_score: float
    percentage: float
    cases: int


class RunSummary(StrictModel):
    run_id: str
    provider: str
    model: str
    total_score: float
    max_score: float
    percentage: float
    cases_total: int
    cases_completed: int
    cases_failed: int
    hard_failures: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    category_scores: list[CategoryScore] = Field(default_factory=list)
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    failure_counts: dict[str, int] = Field(default_factory=dict)
