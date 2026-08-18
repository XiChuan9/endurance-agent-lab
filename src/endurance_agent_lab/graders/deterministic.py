from __future__ import annotations

from collections import Counter

from ..analytics.derived import DerivedMetrics, valid_evidence_references
from ..models.benchmark import BenchmarkCase, DimensionRubric
from ..models.common import ScoreDimension
from ..models.run import CaseGrade, DimensionGrade


def grade_case(
    case: BenchmarkCase,
    audit: object,
    derived: DerivedMetrics,
    *,
    hard_fail_caps_score: bool = True,
    hard_fail_score_cap: float = 0.0,
) -> CaseGrade:
    from ..models.audit import AuditOutput

    output = AuditOutput.model_validate(audit)
    claim_codes = list(dict.fromkeys(claim.code for claim in output.claims))
    claim_set = set(claim_codes)
    valid_refs = valid_evidence_references(case.context, derived)
    all_refs = [ref for claim in output.claims for ref in claim.evidence_references]
    invalid_refs = sorted({ref for ref in all_refs if ref not in valid_refs})
    valid_count = sum(1 for ref in all_refs if ref in valid_refs)
    valid_ratio = valid_count / len(all_refs) if all_refs else 0.0

    dimensions: list[DimensionGrade] = []
    for dimension, rubric in case.rubric.dimensions.items():
        if dimension == ScoreDimension.EVIDENCE_GROUNDING:
            grade = _grade_evidence_dimension(rubric, valid_ratio, all_refs, invalid_refs)
        elif dimension == ScoreDimension.INSTRUCTION_SCHEMA:
            grade = _grade_schema_dimension(rubric, output, claim_set)
        else:
            grade = _grade_code_dimension(dimension, rubric, claim_set)
        dimensions.append(grade)

    hard_fail_reasons: list[str] = []
    for rule in case.rubric.hard_fail_if:
        if rule.code in claim_set:
            hard_fail_reasons.append(f"{rule.code}: {rule.reason}")
    hard_fail = bool(hard_fail_reasons)

    raw_score = round(sum(item.score for item in dimensions), 4)
    max_score = round(sum(item.max_points for item in dimensions), 4)
    score = raw_score
    if hard_fail and hard_fail_caps_score:
        score = min(score, hard_fail_score_cap)
    passed = not hard_fail and score >= max_score * 0.7

    return CaseGrade(
        case_id=case.case_id,
        score=max(0.0, round(score, 4)),
        max_score=max_score,
        passed=passed,
        hard_fail=hard_fail,
        hard_fail_reasons=hard_fail_reasons,
        dimensions=dimensions,
        valid_evidence_ratio=round(valid_ratio, 4),
        invalid_evidence_references=invalid_refs,
        claim_codes=claim_codes,
    )


def _grade_code_dimension(
    dimension: ScoreDimension,
    rubric: DimensionRubric,
    claim_set: set[str],
) -> DimensionGrade:
    required_hits = [code for code in rubric.required_codes if code in claim_set]
    required_misses = [code for code in rubric.required_codes if code not in claim_set]
    optional_hits = [code for code in rubric.optional_codes if code in claim_set]
    forbidden_hits = [code for code in rubric.forbidden_codes if code in claim_set]

    if rubric.required_codes:
        required_ratio = len(required_hits) / len(rubric.required_codes)
        required_share = 0.85 if rubric.optional_codes else 1.0
    else:
        required_ratio = 1.0
        required_share = 0.0 if rubric.optional_codes else 1.0

    if rubric.optional_codes:
        optional_ratio = len(optional_hits) / len(rubric.optional_codes)
        optional_share = 1.0 - required_share
    else:
        optional_ratio = 1.0
        optional_share = 0.0

    score = rubric.max_points * (
        required_share * required_ratio + optional_share * optional_ratio
    )
    if forbidden_hits:
        score -= rubric.max_points * min(1.0, 0.5 * len(forbidden_hits))
    notes: list[str] = []
    if rubric.notes:
        notes.append(rubric.notes)
    if forbidden_hits:
        notes.append("Forbidden claim code(s) detected.")
    return DimensionGrade(
        dimension=dimension,
        score=max(0.0, round(score, 4)),
        max_points=rubric.max_points,
        required_hits=required_hits,
        required_misses=required_misses,
        optional_hits=optional_hits,
        forbidden_hits=forbidden_hits,
        notes=notes,
    )


def _grade_evidence_dimension(
    rubric: DimensionRubric,
    valid_ratio: float,
    all_refs: list[str],
    invalid_refs: list[str],
) -> DimensionGrade:
    score = rubric.max_points * valid_ratio
    notes = []
    if not all_refs:
        notes.append("No evidence references were supplied in the canonical claims registry.")
    if invalid_refs:
        notes.append(f"Invalid evidence references: {', '.join(invalid_refs)}")
    return DimensionGrade(
        dimension=ScoreDimension.EVIDENCE_GROUNDING,
        score=round(score, 4),
        max_points=rubric.max_points,
        required_hits=[],
        required_misses=[],
        optional_hits=[],
        forbidden_hits=[],
        notes=notes,
    )


def _grade_schema_dimension(
    rubric: DimensionRubric,
    output: object,
    claim_set: set[str],
) -> DimensionGrade:
    from ..models.audit import AuditOutput

    audit = AuditOutput.model_validate(output)
    checks = {
        "HAS_CLAIMS": bool(audit.claims),
        "HAS_GOAL_ANALYSIS": bool(audit.goal_analysis.rationale),
        "HAS_OVERALL_ASSESSMENT": bool(audit.overall_assessment.summary),
        "HAS_UNCERTAINTY": bool(
            audit.uncertainty.should_not_infer
            or audit.uncertainty.missing_information
            or audit.uncertainty.conclusions_affected
        ),
    }
    synthetic_claims = {name for name, passed in checks.items() if passed}
    combined = claim_set | synthetic_claims
    return _grade_code_dimension(ScoreDimension.INSTRUCTION_SCHEMA, rubric, combined)


def collect_failure_counts(grades: list[CaseGrade]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for grade in grades:
        for dimension in grade.dimensions:
            counter.update(dimension.required_misses)
            counter.update(f"FORBIDDEN:{code}" for code in dimension.forbidden_hits)
        for reason in grade.hard_fail_reasons:
            counter.update([f"HARD_FAIL:{reason.split(':', 1)[0]}"])
    return dict(counter.most_common())
