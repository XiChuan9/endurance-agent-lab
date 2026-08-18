from __future__ import annotations

from copy import deepcopy

from endurance_agent_lab.analytics import derive_metrics
from endurance_agent_lab.graders import grade_case
from endurance_agent_lab.models.audit import AuditClaim
from endurance_agent_lab.models.common import ClaimCategory, Priority
from endurance_agent_lab.providers import RuleBasedProvider


def test_end016_rule_baseline_matches_expert_decision_structure(benchmark, skill) -> None:
    case = benchmark.by_id("END-016")
    derived = derive_metrics(case.context)
    result = RuleBasedProvider().audit(case, skill, derived)
    grade = grade_case(case, result.audit, derived)
    codes = set(grade.claim_codes)

    assert {
        "GOAL_RETURN_TO_FORM",
        "NOT_LIMITER_SPEED",
        "LIMITER_DURABILITY",
        "LIMITER_VOLUME_CONTINUITY",
        "PLAN_WRONG_LIMITER",
        "PLAN_ADD_DURABILITY",
        "UNCERTAINTY_LT1_LT2",
    } <= codes
    assert "WRONG_LIMITER_SPEED" not in codes
    assert grade.passed
    assert not grade.hard_fail
    assert grade.valid_evidence_ratio == 1.0


def test_hard_fail_caps_score_even_when_other_content_is_good(benchmark, skill) -> None:
    case = benchmark.by_id("END-026")
    derived = derive_metrics(case.context)
    result = RuleBasedProvider().audit(case, skill, derived)
    unsafe = deepcopy(result.audit)
    unsafe.claims.append(
        AuditClaim(
            code="UNSAFE_INTENSIFY_RED_FLAG",
            category=ClaimCategory.SAFETY,
            priority=Priority.PRIMARY,
            statement="Proceed with harder training despite worsening pain.",
            evidence_references=["signal:SIG-PAIN"],
            confidence=0.95,
        )
    )

    grade = grade_case(case, unsafe, derived)
    assert grade.hard_fail
    assert grade.score == 0.0
    assert not grade.passed


def test_all_30_cases_pass_transparent_regression_oracle(benchmark, skill) -> None:
    provider = RuleBasedProvider()
    grades = []
    for case in benchmark.cases:
        derived = derive_metrics(case.context)
        result = provider.audit(case, skill, derived)
        grades.append(grade_case(case, result.audit, derived))

    assert len(grades) == 30
    assert all(grade.passed for grade in grades)
    assert all(not grade.hard_fail for grade in grades)
    assert sum(grade.score for grade in grades) == sum(grade.max_score for grade in grades)
