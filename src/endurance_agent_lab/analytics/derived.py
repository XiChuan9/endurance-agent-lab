from __future__ import annotations

import math
import statistics
from datetime import date
from typing import Iterable

from pydantic import Field

from ..constants import QUALITY_INTENSITIES, RACE_DISTANCE_KM
from ..models.common import StrictModel
from ..models.context import AthleteContext, TrainingSession, TrainingWeek


class DerivedIssue(StrictModel):
    code: str
    description: str
    evidence_references: list[str] = Field(default_factory=list)


class DerivedMetrics(StrictModel):
    target_distance_km: float | None = None
    target_pace_seconds_per_km: float | None = None
    days_to_race: int | None = None
    best_comparable_seconds: int | None = None
    best_comparable_marker_id: str | None = None
    target_minus_best_seconds: int | None = None
    historical_speed_reserve: bool = False

    recent_weeks_count: int = 0
    weekly_distance_km: list[float] = Field(default_factory=list)
    average_weekly_distance_km: float | None = None
    recent_four_week_average_km: float | None = None
    weekly_distance_cv: float | None = None
    max_week_over_week_increase_ratio: float | None = None
    zero_or_missing_weeks: int = 0

    run_sessions_count: int = 0
    missing_hr_ratio: float | None = None
    long_runs_90_minutes: int = 0
    long_runs_105_minutes: int = 0
    long_runs_120_minutes: int = 0
    longest_recent_run_minutes: float | None = None
    quality_sessions_recent: int = 0

    planned_weeks_count: int = 0
    planned_quality_sessions: int = 0
    planned_max_quality_sessions_per_week: int = 0
    minimum_planned_quality_gap_days: int | None = None
    planned_max_week_over_week_increase_ratio: float | None = None

    issues: list[DerivedIssue] = Field(default_factory=list)


def _race_distance(context: AthleteContext) -> float | None:
    if context.goal.distance_km:
        return context.goal.distance_km
    return RACE_DISTANCE_KM.get(context.goal.race_type.value)


def _sorted_weeks(weeks: Iterable[TrainingWeek]) -> list[TrainingWeek]:
    items = list(weeks)

    def key(week: TrainingWeek) -> tuple[int, object]:
        if week.start_date is not None:
            return (0, week.start_date)
        if week.relative_week is not None:
            return (1, week.relative_week)
        return (2, week.week_id)

    return sorted(items, key=key)


def _coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = statistics.fmean(values)
    if mean <= 0:
        return None
    return statistics.pstdev(values) / mean


def _max_increase_ratio(values: list[float]) -> float | None:
    increases: list[float] = []
    for previous, current in zip(values, values[1:], strict=False):
        if previous > 0 and current > previous:
            increases.append((current - previous) / previous)
    return max(increases) if increases else 0.0 if len(values) >= 2 else None


def is_quality_session(session: TrainingSession) -> bool:
    return session.is_quality or session.intensity.value in QUALITY_INTENSITIES


def _session_duration(session: TrainingSession) -> float | None:
    return session.duration_minutes


def _minimum_quality_gap_days(weeks: list[TrainingWeek]) -> int | None:
    dated = sorted(
        session.session_date
        for week in weeks
        for session in week.sessions
        if is_quality_session(session) and session.session_date is not None
    )
    if len(dated) < 2:
        return None
    return min((later - earlier).days for earlier, later in zip(dated, dated[1:], strict=False))


def _detect_duplicate_sessions(context: AthleteContext) -> list[DerivedIssue]:
    seen: dict[tuple[object, ...], str] = {}
    issues: list[DerivedIssue] = []
    for week in context.recent_training.weeks:
        for session in week.sessions:
            signature = (
                session.session_date,
                session.sport.value,
                round(session.distance_km or -1, 3),
                round(session.duration_minutes or -1, 2),
                session.title.lower(),
            )
            if signature in seen:
                issues.append(
                    DerivedIssue(
                        code="DATA_DUPLICATE_ACTIVITY",
                        description=(
                            f"Sessions {seen[signature]} and {session.session_id} have identical core fields."
                        ),
                        evidence_references=[
                            f"session:{seen[signature]}",
                            f"session:{session.session_id}",
                        ],
                    )
                )
            else:
                seen[signature] = session.session_id
    return issues


def _detect_session_anomalies(context: AthleteContext) -> list[DerivedIssue]:
    issues: list[DerivedIssue] = []
    for week in context.recent_training.weeks:
        for session in week.sessions:
            if session.sport.value == "run" and session.pace_seconds_per_km is not None:
                if session.pace_seconds_per_km < 120:
                    issues.append(
                        DerivedIssue(
                            code="DATA_GPS_PACE_OUTLIER",
                            description=(
                                f"Run {session.session_id} has an implausibly fast average pace "
                                f"of {session.pace_seconds_per_km:.1f} s/km."
                            ),
                            evidence_references=[f"session:{session.session_id}"],
                        )
                    )
                if session.pace_seconds_per_km > 1_200 and (session.distance_km or 0) > 2:
                    issues.append(
                        DerivedIssue(
                            code="DATA_PACE_OUTLIER",
                            description=(
                                f"Run {session.session_id} has an implausibly slow average pace "
                                f"for the recorded distance."
                            ),
                            evidence_references=[f"session:{session.session_id}"],
                        )
                    )
            if session.avg_hr is not None and not 25 <= session.avg_hr <= 240:
                issues.append(
                    DerivedIssue(
                        code="DATA_HR_OUTLIER",
                        description=f"Session {session.session_id} contains an implausible average HR.",
                        evidence_references=[f"session:{session.session_id}"],
                    )
                )
    return issues


def derive_metrics(context: AthleteContext, today: date | None = None) -> DerivedMetrics:
    target_distance = _race_distance(context)
    target_pace = None
    if target_distance and context.goal.target_seconds:
        target_pace = context.goal.target_seconds / target_distance

    comparable = [
        marker
        for marker in context.performance_markers
        if marker.time_seconds
        and marker.distance_km
        and target_distance
        and math.isclose(marker.distance_km, target_distance, rel_tol=0.03)
    ]
    best = min(comparable, key=lambda marker: marker.time_seconds or 10**9) if comparable else None
    delta = None
    historical_speed_reserve = False
    if best and best.time_seconds and context.goal.target_seconds:
        delta = context.goal.target_seconds - best.time_seconds
        historical_speed_reserve = delta > 30

    current_date = today or context.as_of_date or date.today()
    days_to_race = (context.goal.race_date - current_date).days if context.goal.race_date else None

    weeks = _sorted_weeks(context.recent_training.weeks)
    volumes = [float(week.distance_km or 0) for week in weeks]
    nonzero_volumes = [value for value in volumes if value > 0]
    sessions = [session for week in weeks for session in week.sessions]
    run_sessions = [session for session in sessions if session.sport.value == "run"]
    hr_eligible = [session for session in run_sessions if (session.duration_minutes or 0) > 0]
    missing_hr = [session for session in hr_eligible if session.avg_hr is None]
    missing_hr_ratio = len(missing_hr) / len(hr_eligible) if hr_eligible else None

    durations = [
        duration
        for session in run_sessions
        if (duration := _session_duration(session)) is not None
    ]
    quality_recent = sum(1 for session in sessions if is_quality_session(session))

    plan_weeks = _sorted_weeks(context.proposed_plan.weeks) if context.proposed_plan else []
    plan_volumes = [float(week.distance_km or 0) for week in plan_weeks]
    plan_quality_by_week = [sum(1 for s in week.sessions if is_quality_session(s)) for week in plan_weeks]

    issues = _detect_duplicate_sessions(context) + _detect_session_anomalies(context)
    if missing_hr_ratio is not None and missing_hr_ratio >= 0.5:
        issues.append(
            DerivedIssue(
                code="DATA_MISSING_HR",
                description=f"Heart-rate data are missing for {missing_hr_ratio:.0%} of eligible runs.",
                evidence_references=["derived:missing_hr_ratio"],
            )
        )

    return DerivedMetrics(
        target_distance_km=target_distance,
        target_pace_seconds_per_km=target_pace,
        days_to_race=days_to_race,
        best_comparable_seconds=best.time_seconds if best else None,
        best_comparable_marker_id=best.marker_id if best else None,
        target_minus_best_seconds=delta,
        historical_speed_reserve=historical_speed_reserve,
        recent_weeks_count=len(weeks),
        weekly_distance_km=volumes,
        average_weekly_distance_km=statistics.fmean(nonzero_volumes) if nonzero_volumes else None,
        recent_four_week_average_km=(
            statistics.fmean(volumes[-4:]) if len(volumes) >= 1 else None
        ),
        weekly_distance_cv=_coefficient_of_variation(volumes),
        max_week_over_week_increase_ratio=_max_increase_ratio(volumes),
        zero_or_missing_weeks=sum(1 for value in volumes if value <= 0),
        run_sessions_count=len(run_sessions),
        missing_hr_ratio=missing_hr_ratio,
        long_runs_90_minutes=sum(1 for duration in durations if duration >= 90),
        long_runs_105_minutes=sum(1 for duration in durations if duration >= 105),
        long_runs_120_minutes=sum(1 for duration in durations if duration >= 120),
        longest_recent_run_minutes=max(durations) if durations else None,
        quality_sessions_recent=quality_recent,
        planned_weeks_count=len(plan_weeks),
        planned_quality_sessions=sum(plan_quality_by_week),
        planned_max_quality_sessions_per_week=max(plan_quality_by_week, default=0),
        minimum_planned_quality_gap_days=_minimum_quality_gap_days(plan_weeks),
        planned_max_week_over_week_increase_ratio=_max_increase_ratio(plan_volumes),
        issues=issues,
    )


def valid_evidence_references(
    context: AthleteContext, derived: DerivedMetrics | None = None
) -> set[str]:
    references = {"athlete:profile", "goal:race", "request:user"}
    references.update(f"performance:{item.marker_id}" for item in context.performance_markers)
    references.update(f"week:{week.week_id}" for week in context.recent_training.weeks)
    references.update(
        f"session:{session.session_id}"
        for week in context.recent_training.weeks
        for session in week.sessions
    )
    references.update(f"signal:{signal.signal_id}" for signal in context.signals)
    references.update(f"source:{note.source_id}" for note in context.source_notes)
    if context.proposed_plan:
        references.update(f"plan-week:{week.week_id}" for week in context.proposed_plan.weeks)
        references.update(
            f"plan-session:{session.session_id}"
            for week in context.proposed_plan.weeks
            for session in week.sessions
        )
    if derived is not None:
        references.update(f"derived:{name}" for name in DerivedMetrics.model_fields)
    return references
