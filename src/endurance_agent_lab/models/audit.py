from __future__ import annotations

from pydantic import Field

from .common import (
    CapabilityStatus,
    ClaimCategory,
    ClaimStance,
    Feasibility,
    OverallVerdict,
    Priority,
    RecommendationAction,
    RiskLevel,
    Severity,
    StrictModel,
)


class AuditClaim(StrictModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,79}$")
    category: ClaimCategory
    stance: ClaimStance = ClaimStance.SUPPORTS
    priority: Priority = Priority.SUPPORTING
    statement: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class DataQualityIssue(StrictModel):
    claim_code: str
    severity: Severity
    description: str
    evidence_references: list[str] = Field(default_factory=list)
    remediation: str | None = None


class DataQualityAssessment(StrictModel):
    completeness: float = Field(ge=0.0, le=1.0)
    issues: list[DataQualityIssue] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    cannot_infer: list[str] = Field(default_factory=list)


class CapabilityAssessment(StrictModel):
    capability: str
    status: CapabilityStatus
    evidence_references: list[str] = Field(default_factory=list)
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


class GoalAnalysis(StrictModel):
    target_pace_seconds_per_km: float | None = Field(default=None, gt=0)
    relation_to_history: str
    feasibility: Feasibility
    rationale: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class LimiterAssessment(StrictModel):
    limiter: str
    priority: Priority
    status: CapabilityStatus
    rationale: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class PlanFinding(StrictModel):
    claim_code: str
    category: str
    severity: Severity
    finding: str
    evidence_references: list[str] = Field(default_factory=list)
    consequence: str
    recommendation: str


class RecommendedChange(StrictModel):
    action: RecommendationAction
    target: str
    rationale: str
    evidence_references: list[str] = Field(default_factory=list)
    priority: Priority = Priority.SUPPORTING


class UncertaintyAssessment(StrictModel):
    missing_information: list[str] = Field(default_factory=list)
    conclusions_affected: list[str] = Field(default_factory=list)
    should_not_infer: list[str] = Field(default_factory=list)
    follow_up_data: list[str] = Field(default_factory=list)


class OverallAssessment(StrictModel):
    verdict: OverallVerdict
    risk_level: RiskLevel
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    hard_stop_recommended: bool = False


class AuditOutput(StrictModel):
    schema_version: str = "1.0"
    case_id: str | None = None
    data_quality: DataQualityAssessment
    athlete_state: list[CapabilityAssessment] = Field(default_factory=list)
    goal_analysis: GoalAnalysis
    limiters: list[LimiterAssessment] = Field(default_factory=list)
    plan_findings: list[PlanFinding] = Field(default_factory=list)
    recommended_changes: list[RecommendedChange] = Field(default_factory=list)
    uncertainty: UncertaintyAssessment
    claims: list[AuditClaim] = Field(default_factory=list)
    overall_assessment: OverallAssessment
