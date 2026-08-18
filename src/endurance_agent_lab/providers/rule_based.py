from __future__ import annotations

import time
from collections import defaultdict
from datetime import timedelta
from typing import Iterable

from ..analytics.derived import DerivedMetrics, is_quality_session
from ..models.audit import (
    AuditClaim,
    AuditOutput,
    CapabilityAssessment,
    DataQualityAssessment,
    DataQualityIssue,
    GoalAnalysis,
    LimiterAssessment,
    OverallAssessment,
    PlanFinding,
    RecommendedChange,
    UncertaintyAssessment,
)
from ..models.benchmark import BenchmarkCase
from ..models.common import (
    CapabilityStatus,
    ClaimCategory,
    ClaimStance,
    Feasibility,
    OverallVerdict,
    Priority,
    RecommendationAction,
    RiskLevel,
    Severity,
)
from ..models.context import ContextSignal, TrainingSession
from ..models.run import ProviderResult
from ..skills.loader import SkillBundle
from .base import AuditProvider


class _AuditBuilder:
    def __init__(self) -> None:
        self.claims: dict[str, AuditClaim] = {}
        self.data_issues: list[DataQualityIssue] = []
        self.capabilities: list[CapabilityAssessment] = []
        self.limiters: list[LimiterAssessment] = []
        self.findings: list[PlanFinding] = []
        self.changes: list[RecommendedChange] = []
        self.missing_information: list[str] = []
        self.conclusions_affected: list[str] = []
        self.should_not_infer: list[str] = []
        self.follow_up_data: list[str] = []

    def claim(
        self,
        code: str,
        category: ClaimCategory,
        statement: str,
        evidence: Iterable[str] = (),
        confidence: float = 0.8,
        priority: Priority = Priority.SUPPORTING,
        stance: ClaimStance = ClaimStance.SUPPORTS,
    ) -> None:
        evidence_list = list(dict.fromkeys(evidence))
        existing = self.claims.get(code)
        if existing:
            existing.evidence_references = list(
                dict.fromkeys([*existing.evidence_references, *evidence_list])
            )
            existing.confidence = max(existing.confidence, confidence)
            return
        self.claims[code] = AuditClaim(
            code=code,
            category=category,
            stance=stance,
            priority=priority,
            statement=statement,
            evidence_references=evidence_list,
            confidence=confidence,
        )

    def data_issue(
        self,
        code: str,
        description: str,
        evidence: Iterable[str],
        severity: Severity = Severity.MEDIUM,
        remediation: str | None = None,
    ) -> None:
        self.data_issues.append(
            DataQualityIssue(
                claim_code=code,
                severity=severity,
                description=description,
                evidence_references=list(evidence),
                remediation=remediation,
            )
        )
        self.claim(code, ClaimCategory.DATA_QUALITY, description, evidence, 0.95)

    def capability(
        self,
        name: str,
        status: CapabilityStatus,
        rationale: str,
        evidence: Iterable[str],
        confidence: float,
    ) -> None:
        self.capabilities.append(
            CapabilityAssessment(
                capability=name,
                status=status,
                evidence_references=list(evidence),
                rationale=rationale,
                confidence=confidence,
            )
        )

    def limiter(
        self,
        code: str,
        name: str,
        priority: Priority,
        status: CapabilityStatus,
        rationale: str,
        evidence: Iterable[str],
        confidence: float,
    ) -> None:
        evidence_list = list(evidence)
        self.limiters.append(
            LimiterAssessment(
                limiter=name,
                priority=priority,
                status=status,
                rationale=rationale,
                evidence_references=evidence_list,
                confidence=confidence,
            )
        )
        self.claim(
            code,
            ClaimCategory.LIMITER,
            rationale,
            evidence_list,
            confidence,
            priority,
        )

    def finding(
        self,
        code: str,
        category: str,
        severity: Severity,
        finding: str,
        evidence: Iterable[str],
        consequence: str,
        recommendation: str,
        confidence: float = 0.9,
    ) -> None:
        evidence_list = list(evidence)
        self.findings.append(
            PlanFinding(
                claim_code=code,
                category=category,
                severity=severity,
                finding=finding,
                evidence_references=evidence_list,
                consequence=consequence,
                recommendation=recommendation,
            )
        )
        self.claim(
            code,
            ClaimCategory.PLAN,
            finding,
            evidence_list,
            confidence,
            Priority.PRIMARY if severity in {Severity.HIGH, Severity.CRITICAL} else Priority.SECONDARY,
        )

    def change(
        self,
        action: RecommendationAction,
        target: str,
        rationale: str,
        evidence: Iterable[str],
        priority: Priority = Priority.SUPPORTING,
    ) -> None:
        self.changes.append(
            RecommendedChange(
                action=action,
                target=target,
                rationale=rationale,
                evidence_references=list(evidence),
                priority=priority,
            )
        )


class RuleBasedProvider(AuditProvider):
    """Transparent zero-cost baseline. It is intentionally not presented as a coach replacement."""

    name = "rules"
    model = "transparent-baseline-v0.1"

    def audit(
        self,
        case: BenchmarkCase,
        skill: SkillBundle,
        derived: DerivedMetrics,
    ) -> ProviderResult:
        del skill
        started = time.perf_counter()
        context = case.context
        builder = _AuditBuilder()
        signals = _SignalIndex(context.signals)

        self._audit_data(builder, case, derived, signals)
        goal_analysis = self._audit_goal(builder, case, derived)
        self._audit_state(builder, case, derived, signals)
        self._audit_plan(builder, case, derived, signals)
        hard_stop, risk_level = self._audit_safety(builder, case, derived, signals)
        self._audit_uncertainty(builder, case, derived, signals)

        completeness = self._completeness(case, derived)
        verdict = self._verdict(builder, derived, hard_stop)
        summary = self._summary(builder, verdict, hard_stop)
        audit = AuditOutput(
            case_id=case.case_id,
            data_quality=DataQualityAssessment(
                completeness=completeness,
                issues=builder.data_issues,
                missing_information=builder.missing_information,
                cannot_infer=builder.should_not_infer,
            ),
            athlete_state=builder.capabilities,
            goal_analysis=goal_analysis,
            limiters=builder.limiters,
            plan_findings=builder.findings,
            recommended_changes=builder.changes,
            uncertainty=UncertaintyAssessment(
                missing_information=builder.missing_information,
                conclusions_affected=builder.conclusions_affected,
                should_not_infer=builder.should_not_infer,
                follow_up_data=builder.follow_up_data,
            ),
            claims=list(builder.claims.values()),
            overall_assessment=OverallAssessment(
                verdict=verdict,
                risk_level=risk_level,
                summary=summary,
                confidence=0.78 if completeness >= 0.7 else 0.58,
                hard_stop_recommended=hard_stop,
            ),
        )
        return ProviderResult(
            provider=self.name,
            model=self.model,
            audit=audit,
            raw_response={"engine": self.model, "deterministic": True},
            latency_seconds=time.perf_counter() - started,
        )

    def _audit_data(
        self,
        builder: _AuditBuilder,
        case: BenchmarkCase,
        derived: DerivedMetrics,
        signals: "_SignalIndex",
    ) -> None:
        for issue in derived.issues:
            severity = Severity.HIGH if "OUTLIER" in issue.code else Severity.MEDIUM
            builder.data_issue(
                issue.code,
                issue.description,
                issue.evidence_references,
                severity,
                "Exclude or correct the affected record before deriving fitness or load conclusions.",
            )

        explicit = {
            "unit_mismatch": (
                "DATA_UNIT_MISMATCH",
                "The supplied activity data contain a unit mismatch.",
            ),
            "activity_mislabeled": (
                "DATA_ACTIVITY_MISLABEL",
                "At least one activity is mislabeled and should not be interpreted at face value.",
            ),
            "duplicate_export": (
                "DATA_DUPLICATE_ACTIVITY",
                "The export contains a duplicate activity that inflates training load.",
            ),
            "volume_outlier": (
                "DATA_OUTLIER_VOLUME",
                "An extreme weekly-volume value is likely a data artifact rather than real training.",
            ),
        }
        for key, (code, statement) in explicit.items():
            for signal in signals.match(key):
                builder.data_issue(
                    code,
                    statement,
                    [f"signal:{signal.signal_id}"],
                    Severity.HIGH,
                    "Resolve the source record before evaluating progression.",
                )

        if derived.recent_weeks_count < 4 or signals.match("short_history"):
            evidence = ["derived:recent_weeks_count"]
            evidence.extend(f"signal:{item.signal_id}" for item in signals.match("short_history"))
            builder.data_issue(
                "DATA_INSUFFICIENT_HISTORY",
                "The available training history is too short for confident longitudinal diagnosis.",
                evidence,
                Severity.HIGH,
                "Collect at least 6-8 representative weeks where possible.",
            )

        if signals.match("weather_heat") or signals.match("heat_index"):
            evidence = [
                f"signal:{signal.signal_id}"
                for signal in [*signals.match("weather_heat"), *signals.match("heat_index")]
            ]
            builder.data_issue(
                "DATA_WEATHER_CONFOUNDER",
                "Heat or humidity materially confounds pace-based fitness interpretation.",
                evidence,
                Severity.MEDIUM,
                "Use effort, heart rate, environmental correction, and comparable-condition sessions.",
            )

        if signals.match("conflicting_hr_rpe"):
            evidence = [f"signal:{s.signal_id}" for s in signals.match("conflicting_hr_rpe")]
            builder.data_issue(
                "DATA_CONFLICTING_SIGNALS",
                "Heart-rate and perceived-exertion signals conflict and require cautious interpretation.",
                evidence,
                Severity.MEDIUM,
                "Review device quality, conditions, sleep, and repeated observations.",
            )

        if not case.context.signals or signals.match("missing_recovery_data"):
            evidence = ["athlete:profile"]
            evidence.extend(
                f"signal:{signal.signal_id}" for signal in signals.match("missing_recovery_data")
            )
            builder.data_issue(
                "DATA_INCOMPLETE_RECOVERY",
                "Recovery, pain, sleep, or readiness information is incomplete.",
                evidence,
                Severity.LOW,
                "Add recent recovery and injury-status observations before high-stakes adjustment.",
            )

    def _audit_goal(
        self,
        builder: _AuditBuilder,
        case: BenchmarkCase,
        derived: DerivedMetrics,
    ) -> GoalAnalysis:
        evidence = ["goal:race"]
        relation = "No directly comparable performance marker is available."
        feasibility = Feasibility.UNKNOWN
        confidence = 0.5

        if derived.best_comparable_marker_id:
            evidence.append(f"performance:{derived.best_comparable_marker_id}")
            if derived.target_minus_best_seconds is not None and derived.target_minus_best_seconds > 30:
                relation = (
                    "The target is slower than the athlete's historical best and is best framed as "
                    "returning to previously demonstrated capacity."
                )
                feasibility = Feasibility.RETURN_TO_FORM
                confidence = 0.92
                builder.claim(
                    "GOAL_RETURN_TO_FORM",
                    ClaimCategory.GOAL,
                    relation,
                    evidence,
                    confidence,
                    Priority.PRIMARY,
                )
                builder.claim(
                    "NOT_LIMITER_SPEED",
                    ClaimCategory.LIMITER,
                    "Historical race performance indicates that raw speed is not the primary limiter.",
                    evidence,
                    0.9,
                    Priority.NOT_PRIORITY,
                )
            elif derived.target_minus_best_seconds is not None and derived.target_minus_best_seconds < 0:
                improvement = abs(derived.target_minus_best_seconds) / max(
                    derived.best_comparable_seconds or 1, 1
                )
                if improvement >= 0.1 and (derived.days_to_race is None or derived.days_to_race <= 90):
                    relation = (
                        "The target requires a large improvement over the best comparable performance "
                        "inside a limited preparation window."
                    )
                    feasibility = Feasibility.UNREALISTIC
                    confidence = 0.9
                    builder.claim(
                        "GOAL_UNREALISTIC",
                        ClaimCategory.GOAL,
                        relation,
                        evidence,
                        confidence,
                        Priority.PRIMARY,
                    )
                else:
                    relation = "The target is faster than the best comparable performance."
                    feasibility = Feasibility.STRETCH
                    confidence = 0.75
            else:
                relation = "The target is close to the best comparable performance."
                feasibility = Feasibility.REALISTIC
                confidence = 0.8
                builder.claim(
                    "GOAL_REALISTIC",
                    ClaimCategory.GOAL,
                    relation,
                    evidence,
                    confidence,
                    Priority.SECONDARY,
                )

        if derived.days_to_race is not None and derived.days_to_race <= 21:
            builder.claim(
                "GOAL_SHORT_HORIZON",
                ClaimCategory.GOAL,
                "The remaining time is too short for rebuilding every fitness component; prioritize readiness and risk control.",
                ["goal:race", "derived:days_to_race"],
                0.95,
                Priority.PRIMARY,
            )

        return GoalAnalysis(
            target_pace_seconds_per_km=derived.target_pace_seconds_per_km,
            relation_to_history=relation,
            feasibility=feasibility,
            rationale=relation,
            evidence_references=evidence,
            confidence=confidence,
        )

    def _audit_state(
        self,
        builder: _AuditBuilder,
        case: BenchmarkCase,
        derived: DerivedMetrics,
        signals: "_SignalIndex",
    ) -> None:
        race = case.context.goal.race_type.value
        durability_relevant = race in {"half_marathon", "marathon", "ultra"}
        expected_exposures = max(2, derived.recent_weeks_count // 3)
        if durability_relevant and (
            derived.long_runs_90_minutes < expected_exposures
            or (derived.longest_recent_run_minutes or 0) < 100
            or signals.match("late_race_fade")
        ):
            evidence = ["derived:long_runs_90_minutes", "derived:longest_recent_run_minutes"]
            evidence.extend(f"signal:{s.signal_id}" for s in signals.match("late_race_fade"))
            builder.capability(
                "durability",
                CapabilityStatus.WEAK,
                "Long-duration exposure is insufficient or late-race fade is evident.",
                evidence,
                0.88,
            )
            builder.limiter(
                "LIMITER_DURABILITY",
                "durability",
                Priority.PRIMARY,
                CapabilityStatus.WEAK,
                "The main limiter is the ability to preserve performance over race-relevant duration.",
                evidence,
                0.9,
            )
            builder.claim(
                "STATE_LATE_RACE_FADE",
                ClaimCategory.ATHLETE_STATE,
                "Available evidence is consistent with performance decay over longer duration.",
                evidence,
                0.82,
                Priority.PRIMARY,
            )

        volatile = (
            (derived.weekly_distance_cv or 0) >= 0.25
            or (derived.max_week_over_week_increase_ratio or 0) >= 0.3
            or derived.zero_or_missing_weeks > 0
            or bool(signals.match("volatile_load"))
        )
        if volatile:
            evidence = [
                "derived:weekly_distance_cv",
                "derived:max_week_over_week_increase_ratio",
                "derived:zero_or_missing_weeks",
            ]
            evidence.extend(f"signal:{s.signal_id}" for s in signals.match("volatile_load"))
            builder.capability(
                "volume continuity",
                CapabilityStatus.WEAK,
                "Weekly load is too volatile to treat average volume as stable fitness exposure.",
                evidence,
                0.9,
            )
            builder.limiter(
                "LIMITER_VOLUME_CONTINUITY",
                "volume continuity",
                Priority.PRIMARY,
                CapabilityStatus.WEAK,
                "Training continuity is a primary limiter because exposure varies excessively between weeks.",
                evidence,
                0.9,
            )
            builder.claim(
                "STATE_VOLATILE_LOAD",
                ClaimCategory.ATHLETE_STATE,
                "The athlete's load pattern is volatile rather than consistently high.",
                evidence,
                0.9,
                Priority.PRIMARY,
            )

        if signals.match("short_run_bias"):
            evidence = [f"signal:{s.signal_id}" for s in signals.match("short_run_bias")]
            builder.claim(
                "STATE_SHORT_RUN_BIAS",
                ClaimCategory.ATHLETE_STATE,
                "Training volume is accumulated mainly through short runs, limiting long-duration aerobic exposure.",
                evidence,
                0.9,
                Priority.PRIMARY,
            )
            if not any(limiter.limiter == "durability" for limiter in builder.limiters):
                builder.limiter(
                    "LIMITER_DURABILITY",
                    "durability",
                    Priority.PRIMARY,
                    CapabilityStatus.WEAK,
                    "Short-run-biased volume does not adequately develop long-duration durability.",
                    evidence,
                    0.87,
                )

        if signals.match("threshold_weak"):
            evidence = [f"signal:{s.signal_id}" for s in signals.match("threshold_weak")]
            builder.capability(
                "threshold capacity",
                CapabilityStatus.WEAK,
                "Available performance evidence indicates weak sustained threshold capacity.",
                evidence,
                0.86,
            )
            builder.limiter(
                "LIMITER_THRESHOLD",
                "threshold capacity",
                Priority.PRIMARY,
                CapabilityStatus.WEAK,
                "Threshold capacity is the main performance limiter despite adequate volume.",
                evidence,
                0.86,
            )

        if signals.match("hm_specific_weak") or signals.match("five_k_strong_hm_weak"):
            evidence = [
                f"signal:{s.signal_id}"
                for s in [*signals.match("hm_specific_weak"), *signals.match("five_k_strong_hm_weak")]
            ]
            builder.limiter(
                "LIMITER_HM_SPECIFIC_ENDURANCE",
                "half-marathon-specific endurance",
                Priority.PRIMARY,
                CapabilityStatus.WEAK,
                "Short-distance performance is not converting to half-marathon performance.",
                evidence,
                0.9,
            )

        if signals.match("five_k_weak_hm_strong"):
            evidence = [f"signal:{s.signal_id}" for s in signals.match("five_k_weak_hm_strong")]
            builder.limiter(
                "LIMITER_SPEED_RESERVE",
                "speed reserve",
                Priority.PRIMARY,
                CapabilityStatus.WEAK,
                "Longer-distance performance is relatively strong, while 5K performance indicates limited speed reserve for the stated goal.",
                evidence,
                0.84,
            )

        if derived.historical_speed_reserve:
            evidence = ["goal:race"]
            if derived.best_comparable_marker_id:
                evidence.append(f"performance:{derived.best_comparable_marker_id}")
            builder.capability(
                "speed reserve",
                CapabilityStatus.STRONG,
                "Historical performance exceeds the speed requirement of the current goal.",
                evidence,
                0.9,
            )

        if signals.match("return_from_injury") or signals.match("tissue_tolerance_rebuilding"):
            evidence = [
                f"signal:{s.signal_id}"
                for s in [
                    *signals.match("return_from_injury"),
                    *signals.match("tissue_tolerance_rebuilding"),
                ]
            ]
            builder.limiter(
                "LIMITER_MUSCULOSKELETAL_TOLERANCE",
                "musculoskeletal tolerance",
                Priority.SECONDARY,
                CapabilityStatus.REBUILDING,
                "Mechanical loading tolerance is still rebuilding and constrains progression speed.",
                evidence,
                0.88,
            )

        if derived.average_weekly_distance_km and derived.average_weekly_distance_km >= 90:
            builder.claim(
                "STATE_HIGH_VOLUME",
                ClaimCategory.ATHLETE_STATE,
                "Recent training volume is high in absolute terms.",
                ["derived:average_weekly_distance_km"],
                0.9,
                Priority.SUPPORTING,
            )

    def _audit_plan(
        self,
        builder: _AuditBuilder,
        case: BenchmarkCase,
        derived: DerivedMetrics,
        signals: "_SignalIndex",
    ) -> None:
        plan = case.context.proposed_plan
        if plan is None or not plan.weeks:
            builder.finding(
                "PLAN_MISSING",
                "completeness",
                Severity.HIGH,
                "No proposed training plan was supplied for audit.",
                ["request:user"],
                "A plan-specific audit cannot be completed.",
                "Provide at least one planned week with session intent and load.",
            )
            return

        quality_sessions = [
            session for week in plan.weeks for session in week.sessions if is_quality_session(session)
        ]
        vo2_sessions = [session for session in quality_sessions if session.intensity.value == "vo2max"]
        race_pace_sessions = [
            session for session in quality_sessions if session.intensity.value == "race_pace"
        ]

        if derived.planned_max_quality_sessions_per_week >= 3:
            refs = [
                f"plan-week:{week.week_id}"
                for week in plan.weeks
                if sum(1 for session in week.sessions if is_quality_session(session)) >= 3
            ]
            builder.finding(
                "PLAN_TOO_MANY_PRIORITIES",
                "distribution",
                Severity.HIGH,
                "The plan places too many quality priorities into the same week.",
                refs,
                "Locally reasonable sessions combine into an unrecoverable global load.",
                "Choose one or two primary quality stimuli and protect recovery around them.",
            )
            builder.finding(
                "PLAN_TOO_MUCH_INTENSITY",
                "intensity",
                Severity.HIGH,
                "The weekly quality-session count exceeds a conservative recoverable dose.",
                refs,
                "Adaptation quality and consistency may deteriorate as fatigue accumulates.",
                "Reduce the number of hard sessions before changing their individual design.",
            )

        if derived.minimum_planned_quality_gap_days is not None and derived.minimum_planned_quality_gap_days <= 1:
            refs = [f"plan-session:{session.session_id}" for session in quality_sessions]
            builder.finding(
                "PLAN_INTENSITY_CLUSTER",
                "recovery",
                Severity.HIGH,
                "Quality sessions are separated by no more than one day.",
                refs,
                "Residual fatigue may turn planned quality into low-quality overload.",
                "Insert at least one genuinely easy or rest day, and usually two, between key sessions.",
            )
            builder.finding(
                "PLAN_INSUFFICIENT_RECOVERY",
                "recovery",
                Severity.HIGH,
                "Recovery spacing is insufficient for the planned intensity pattern.",
                refs,
                "The athlete may fail to absorb the intended stimulus.",
                "Redistribute quality across the week before adding load.",
            )

        if (derived.planned_max_week_over_week_increase_ratio or 0) >= 0.25:
            builder.finding(
                "PLAN_VOLUME_SPIKE",
                "progression",
                Severity.HIGH,
                "Planned weekly volume rises abruptly relative to the preceding planned week.",
                ["derived:planned_max_week_over_week_increase_ratio"],
                "Mechanical and recovery cost may increase faster than aerobic adaptation.",
                "Use a smaller step, hold, or cutback before progressing again.",
            )

        if signals.match("recovery_week"):
            first_week = plan.weeks[0]
            recent_avg = derived.recent_four_week_average_km or 0
            if (first_week.distance_km or 0) >= recent_avg or signals.match("recovery_week_overload"):
                evidence = [f"signal:{s.signal_id}" for s in signals.match("recovery_week")]
                evidence.append(f"plan-week:{first_week.week_id}")
                builder.finding(
                    "PLAN_RECOVERY_WEEK_OVERLOAD",
                    "recovery",
                    Severity.HIGH,
                    "The declared recovery week does not reduce total load.",
                    evidence,
                    "The athlete receives the label of recovery without the physiological reduction.",
                    "Reduce volume and/or quality density enough to create a real unloading week.",
                )

        if derived.days_to_race is not None and derived.days_to_race <= 21:
            race_date = case.context.goal.race_date
            recent_avg = derived.recent_four_week_average_km or 0
            overloaded_taper_weeks: list[str] = []
            for week in plan.weeks:
                # Judge the actual race-proximal weeks, not merely the first displayed week.
                # This avoids missing overload when a multi-week plan begins before the taper window.
                days_from_week_start = (
                    (race_date - week.start_date).days
                    if race_date is not None and week.start_date is not None
                    else None
                )
                inside_taper_window = days_from_week_start is None or 0 <= days_from_week_start <= 14
                if not inside_taper_window:
                    continue
                quality_count = sum(
                    1 for session in week.sessions if is_quality_session(session)
                )
                retains_volume = recent_avg > 0 and (week.distance_km or 0) >= recent_avg * 0.9
                if retains_volume or quality_count >= 3:
                    overloaded_taper_weeks.append(f"plan-week:{week.week_id}")
            if overloaded_taper_weeks:
                builder.finding(
                    "PLAN_TAPER_OVERLOAD",
                    "taper",
                    Severity.HIGH,
                    "The taper retains excessive volume or quality density close to race day.",
                    ["goal:race", *overloaded_taper_weeks, "derived:days_to_race"],
                    "Fitness cannot be meaningfully rebuilt now, but fatigue can still be added.",
                    "Reduce load while preserving small doses of race-relevant intensity.",
                )

        if signals.match("base_phase") and len(race_pace_sessions) >= 2:
            builder.finding(
                "PLAN_PREMATURE_SPECIFICITY",
                "specificity",
                Severity.MEDIUM,
                "Race-pace work is overrepresented during a base-oriented phase.",
                [
                    *[f"signal:{s.signal_id}" for s in signals.match("base_phase")],
                    *[f"plan-session:{s.session_id}" for s in race_pace_sessions],
                ],
                "Specific fatigue displaces aerobic continuity before the base is stable.",
                "Use lower-cost aerobic and controlled threshold work first.",
            )

        primary_durability = any(
            limiter.limiter == "durability" and limiter.priority == Priority.PRIMARY
            for limiter in builder.limiters
        )
        speed_not_limiter = "NOT_LIMITER_SPEED" in builder.claims
        if (primary_durability or speed_not_limiter) and len(vo2_sessions) >= 2:
            refs = [f"plan-session:{session.session_id}" for session in vo2_sessions]
            builder.finding(
                "PLAN_WRONG_LIMITER",
                "limiter_alignment",
                Severity.HIGH,
                "The plan spends disproportionate recovery resources on VO2max despite a different primary limiter.",
                refs,
                "The athlete may become sharper without solving race-duration failure.",
                "Reallocate one VO2max session toward durability, continuity, or controlled threshold work.",
            )
            builder.finding(
                "PLAN_EXCESS_VO2",
                "intensity",
                Severity.HIGH,
                "VO2max frequency is excessive for the diagnosed need.",
                refs,
                "High recovery cost crowds out the adaptations that matter most.",
                "Retain only a small maintenance dose if speed support is needed.",
            )

        self._detect_strength_conflict(builder, plan.weeks)

        if primary_durability:
            builder.change(
                RecommendationAction.ADD,
                "progressive 90-120 minute durability exposure",
                "Increase long-duration exposure gradually while keeping most of the work controlled.",
                ["derived:long_runs_90_minutes", "derived:longest_recent_run_minutes"],
                Priority.PRIMARY,
            )
            builder.claim(
                "PLAN_ADD_DURABILITY",
                ClaimCategory.PLAN,
                "The plan should add progressive long-duration aerobic exposure.",
                ["derived:long_runs_90_minutes"],
                0.9,
                Priority.PRIMARY,
            )

        if any(limiter.limiter == "threshold capacity" for limiter in builder.limiters):
            builder.change(
                RecommendationAction.ADD,
                "controlled threshold development",
                "Use repeatable threshold work rather than adding more total intensity categories.",
                [claim_ref(builder, "LIMITER_THRESHOLD")],
                Priority.PRIMARY,
            )
            builder.claim(
                "PLAN_ADD_THRESHOLD",
                ClaimCategory.PLAN,
                "The plan should prioritize controlled threshold development.",
                [claim_ref(builder, "LIMITER_THRESHOLD")],
                0.88,
                Priority.PRIMARY,
            )

        if derived.longest_recent_run_minutes and derived.longest_recent_run_minutes >= 100:
            long_plan = [
                session
                for week in plan.weeks
                for session in week.sessions
                if (session.duration_minutes or 0) >= 90
            ]
            if long_plan:
                builder.change(
                    RecommendationAction.KEEP,
                    long_plan[0].title,
                    "A controlled long run supports race-relevant durability.",
                    [f"plan-session:{long_plan[0].session_id}"],
                    Priority.SECONDARY,
                )
                builder.claim(
                    "PLAN_KEEP_LONG_RUN",
                    ClaimCategory.PLAN,
                    "A controlled long run should be retained.",
                    [f"plan-session:{long_plan[0].session_id}"],
                    0.8,
                    Priority.SECONDARY,
                )

        if builder.findings:
            builder.change(
                RecommendationAction.MODIFY,
                "weekly session architecture",
                "Fix global load distribution before optimizing individual workout details.",
                [finding_ref(builder.findings[0])],
                Priority.PRIMARY,
            )
            builder.claim(
                "PLAN_MODIFY_KEY_SESSION",
                ClaimCategory.PLAN,
                "At least one key session or its placement should be modified.",
                builder.findings[0].evidence_references,
                0.85,
                Priority.PRIMARY,
            )

    def _detect_strength_conflict(
        self, builder: _AuditBuilder, weeks: Iterable[object]
    ) -> None:
        sessions: list[TrainingSession] = []
        for week in weeks:
            sessions.extend(getattr(week, "sessions", []))
        dated = [session for session in sessions if session.session_date is not None]
        for strength in dated:
            if strength.sport.value != "strength":
                continue
            for quality in dated:
                if not is_quality_session(quality) or quality.session_date is None:
                    continue
                if quality.session_date - strength.session_date == timedelta(days=1):
                    refs = [
                        f"plan-session:{strength.session_id}",
                        f"plan-session:{quality.session_id}",
                    ]
                    builder.finding(
                        "PLAN_STRENGTH_BEFORE_KEY",
                        "recovery",
                        Severity.MEDIUM,
                        "Heavy strength work is placed immediately before a key running session.",
                        refs,
                        "Neuromuscular fatigue may reduce running quality and increase mechanical strain.",
                        "Move heavy strength away from the 24-36 hours before key endurance work.",
                    )
                    return

    def _audit_safety(
        self,
        builder: _AuditBuilder,
        case: BenchmarkCase,
        derived: DerivedMetrics,
        signals: "_SignalIndex",
    ) -> tuple[bool, RiskLevel]:
        del derived
        hard_stop = False
        risk = RiskLevel.LOW
        pain_signals = [
            signal
            for signal in case.context.signals
            if signal.signal_type.value in {"injury", "medical"}
            and any(term in signal.key.lower() for term in ("pain", "injury", "symptom"))
            and _truthy(signal.value)
        ]
        worsening = [
            signal
            for signal in pain_signals
            if (signal.severity or "").lower() in {"high", "critical"}
            or "worsen" in (signal.notes or "").lower()
            or "加重" in (signal.notes or "")
        ]
        if worsening:
            refs = [f"signal:{signal.signal_id}" for signal in worsening]
            builder.claim(
                "SAFETY_PAIN_RED_FLAG",
                ClaimCategory.SAFETY,
                "Worsening pain is a red flag that overrides the planned intensity progression.",
                refs,
                0.98,
                Priority.PRIMARY,
            )
            builder.claim(
                "SAFETY_NO_INTENSIFICATION",
                ClaimCategory.SAFETY,
                "Do not intensify training while the red-flag symptom is unresolved.",
                refs,
                0.98,
                Priority.PRIMARY,
            )
            builder.claim(
                "SAFETY_MEDICAL_ESCALATION",
                ClaimCategory.SAFETY,
                "Persistent or worsening symptoms warrant qualified medical assessment rather than remote training diagnosis.",
                refs,
                0.95,
                Priority.PRIMARY,
            )
            builder.change(
                RecommendationAction.HOLD,
                "high-intensity and high-impact training",
                "Pause escalation until the symptom is assessed and ordinary activity is tolerable.",
                refs,
                Priority.PRIMARY,
            )
            hard_stop = True
            risk = RiskLevel.CRITICAL

        rhr_signals = signals.match("resting_hr_delta_bpm")
        for signal in rhr_signals:
            try:
                delta = float(signal.value)
            except (TypeError, ValueError):
                continue
            if delta >= 5:
                refs = [f"signal:{signal.signal_id}"]
                builder.claim(
                    "SAFETY_RHR_RED_FLAG",
                    ClaimCategory.SAFETY,
                    "Resting heart rate is materially elevated from baseline and argues against a hard session today.",
                    refs,
                    0.94,
                    Priority.PRIMARY,
                )
                builder.claim(
                    "SAFETY_NO_INTENSIFICATION",
                    ClaimCategory.SAFETY,
                    "Do not intensify training while recovery markers are abnormal.",
                    refs,
                    0.94,
                    Priority.PRIMARY,
                )
                risk = max_risk(risk, RiskLevel.HIGH)

        request = case.context.user_request.lower()
        override_terms = (
            "do not question",
            "don't question",
            "ignore recovery",
            "as hard as possible",
            "不要质疑",
            "不用管恢复",
            "越狠越好",
        )
        if any(term in request for term in override_terms):
            builder.claim(
                "SAFETY_USER_OVERRIDE_REJECTED",
                ClaimCategory.SAFETY,
                "A user instruction cannot override material safety or feasibility evidence.",
                ["request:user"],
                0.99,
                Priority.PRIMARY,
            )
            risk = max_risk(risk, RiskLevel.MODERATE)

        if signals.match("weather_heat") or signals.match("heat_index"):
            refs = [
                f"signal:{signal.signal_id}"
                for signal in [*signals.match("weather_heat"), *signals.match("heat_index")]
            ]
            builder.claim(
                "SAFETY_HEAT_ADJUSTMENT",
                ClaimCategory.SAFETY,
                "Training intensity and interpretation should be adjusted for heat stress.",
                refs,
                0.92,
                Priority.SECONDARY,
            )
            risk = max_risk(risk, RiskLevel.MODERATE)

        high_plan = any(
            finding.severity in {Severity.HIGH, Severity.CRITICAL} for finding in builder.findings
        )
        if high_plan:
            risk = max_risk(risk, RiskLevel.HIGH)
        return hard_stop, risk

    def _audit_uncertainty(
        self,
        builder: _AuditBuilder,
        case: BenchmarkCase,
        derived: DerivedMetrics,
        signals: "_SignalIndex",
    ) -> None:
        threshold_marker = any(
            marker.marker_type.lower() in {"lt1", "lt2", "threshold", "lactate_test"}
            for marker in case.context.performance_markers
        )
        request = case.context.user_request.lower()
        if not threshold_marker:
            builder.missing_information.append("No measured or validated LT1/LT2 marker was supplied.")
            builder.should_not_infer.extend(["exact LT1", "exact LT2"])
            builder.conclusions_affected.append("precise threshold prescription")
            builder.follow_up_data.append(
                "Provide a recent controlled test, validated field estimate, or laboratory threshold assessment."
            )
            builder.claim(
                "UNCERTAINTY_LT1_LT2",
                ClaimCategory.UNCERTAINTY,
                "Exact LT1 and LT2 cannot be inferred from the supplied data.",
                ["athlete:profile"],
                0.98,
                Priority.PRIMARY,
                ClaimStance.UNCERTAIN,
            )
            if "zone" in request or "区间" in request or "精确" in request:
                builder.claim(
                    "UNCERTAINTY_EXACT_ZONES",
                    ClaimCategory.UNCERTAINTY,
                    "Exact heart-rate or pace zones should not be fabricated without valid anchors.",
                    ["request:user"],
                    0.99,
                    Priority.PRIMARY,
                    ClaimStance.UNCERTAIN,
                )

        if derived.recent_weeks_count < 4:
            builder.missing_information.append("Fewer than four representative training weeks are available.")
            builder.conclusions_affected.append("long-term load and progression diagnosis")
            builder.claim(
                "UNCERTAINTY_SHORT_HISTORY",
                ClaimCategory.UNCERTAINTY,
                "The short history limits confidence in longitudinal conclusions.",
                ["derived:recent_weeks_count"],
                0.97,
                Priority.PRIMARY,
                ClaimStance.UNCERTAIN,
            )

        if signals.match("conflicting_hr_rpe"):
            refs = [f"signal:{s.signal_id}" for s in signals.match("conflicting_hr_rpe")]
            builder.claim(
                "UNCERTAINTY_CONFLICTING_SIGNALS",
                ClaimCategory.UNCERTAINTY,
                "Conflicting physiological and subjective signals require conditional interpretation.",
                refs,
                0.95,
                Priority.PRIMARY,
                ClaimStance.UNCERTAIN,
            )

        has_recovery = any(
            signal.signal_type.value in {"recovery", "injury", "medical"}
            for signal in case.context.signals
        )
        if not has_recovery or signals.match("missing_recovery_data"):
            builder.missing_information.append("Recent recovery and injury status are incomplete.")
            builder.conclusions_affected.append("readiness for high-intensity progression")
            builder.claim(
                "UNCERTAINTY_RECOVERY_STATUS",
                ClaimCategory.UNCERTAINTY,
                "Readiness cannot be fully assessed without recovery and injury-status data.",
                ["athlete:profile"],
                0.88,
                Priority.SECONDARY,
                ClaimStance.UNCERTAIN,
            )

        builder.should_not_infer.append("medical or injury diagnosis from training data alone")
        builder.claim(
            "UNCERTAINTY_INJURY_DIAGNOSIS",
            ClaimCategory.UNCERTAINTY,
            "Training data do not support a medical diagnosis.",
            ["athlete:profile"],
            0.99,
            Priority.SUPPORTING,
            ClaimStance.UNCERTAIN,
        )
        builder.missing_information = list(dict.fromkeys(builder.missing_information))
        builder.conclusions_affected = list(dict.fromkeys(builder.conclusions_affected))
        builder.should_not_infer = list(dict.fromkeys(builder.should_not_infer))
        builder.follow_up_data = list(dict.fromkeys(builder.follow_up_data))

    def _completeness(self, case: BenchmarkCase, derived: DerivedMetrics) -> float:
        score = 0.15
        score += min(derived.recent_weeks_count / 8, 1) * 0.35
        score += 0.15 if case.context.performance_markers else 0
        score += 0.2 if case.context.proposed_plan and case.context.proposed_plan.weeks else 0
        score += 0.1 if case.context.signals else 0
        if derived.missing_hr_ratio is None:
            score += 0.02
        else:
            score += max(0, 1 - derived.missing_hr_ratio) * 0.05
        return min(round(score, 3), 1.0)

    def _verdict(
        self, builder: _AuditBuilder, derived: DerivedMetrics, hard_stop: bool
    ) -> OverallVerdict:
        if hard_stop:
            return OverallVerdict.HOLD
        if derived.recent_weeks_count < 3:
            return OverallVerdict.INSUFFICIENT_DATA
        if any(finding.severity in {Severity.HIGH, Severity.CRITICAL} for finding in builder.findings):
            return OverallVerdict.REVISE
        if builder.findings:
            return OverallVerdict.APPROVE_WITH_CHANGES
        return OverallVerdict.APPROVE

    def _summary(
        self, builder: _AuditBuilder, verdict: OverallVerdict, hard_stop: bool
    ) -> str:
        primary = [
            limiter.limiter for limiter in builder.limiters if limiter.priority == Priority.PRIMARY
        ]
        if hard_stop:
            return "Hold progression because a safety red flag outweighs the planned training objective."
        if primary:
            joined = ", ".join(primary[:2])
            return (
                f"Verdict: {verdict.value}. The plan should be revised around the primary limiter(s): "
                f"{joined}, while preserving only the lowest-cost useful stimuli."
            )
        return f"Verdict: {verdict.value}. No single high-confidence primary limiter was established."


class _SignalIndex:
    def __init__(self, signals: list[ContextSignal]) -> None:
        self._signals = signals
        self._by_key: dict[str, list[ContextSignal]] = defaultdict(list)
        for signal in signals:
            self._by_key[signal.key.lower()].append(signal)

    def match(self, fragment: str) -> list[ContextSignal]:
        fragment = fragment.lower()
        matches: list[ContextSignal] = []
        for key, signals in self._by_key.items():
            if fragment in key:
                matches.extend(signals)
        return matches


def _truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "no", "none", "0", "否"}
    return bool(value)


def max_risk(left: RiskLevel, right: RiskLevel) -> RiskLevel:
    order = {
        RiskLevel.LOW: 0,
        RiskLevel.MODERATE: 1,
        RiskLevel.HIGH: 2,
        RiskLevel.CRITICAL: 3,
    }
    return left if order[left] >= order[right] else right


def finding_ref(finding: PlanFinding) -> str:
    return finding.evidence_references[0] if finding.evidence_references else "request:user"


def claim_ref(builder: _AuditBuilder, code: str) -> str:
    claim = builder.claims.get(code)
    if claim and claim.evidence_references:
        return claim.evidence_references[0]
    return "athlete:profile"
