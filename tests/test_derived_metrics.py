from __future__ import annotations

import pytest

from endurance_agent_lab.analytics import derive_metrics
from endurance_agent_lab.evals import LoadedBenchmark


def test_return_to_form_case_derives_speed_reserve_and_short_durability(
    benchmark: LoadedBenchmark,
) -> None:
    case = benchmark.by_id("END-016")
    derived = derive_metrics(case.context)

    assert derived.target_pace_seconds_per_km == pytest.approx(4200 / 21.0975)
    assert derived.best_comparable_seconds == 3960
    assert derived.target_minus_best_seconds == 240
    assert derived.historical_speed_reserve is True
    assert derived.longest_recent_run_minutes is not None
    assert derived.long_runs_105_minutes < max(2, derived.recent_weeks_count // 3)
    assert derived.weekly_distance_cv is not None
    assert derived.weekly_distance_cv > 0.1


def test_taper_overload_is_detected_in_actual_race_proximal_week(
    benchmark: LoadedBenchmark, skill
) -> None:
    from endurance_agent_lab.providers import RuleBasedProvider

    case = benchmark.by_id("END-020")
    result = RuleBasedProvider().audit(case, skill, derive_metrics(case.context))
    codes = {claim.code for claim in result.audit.claims}

    assert "GOAL_SHORT_HORIZON" in codes
    assert "PLAN_TAPER_OVERLOAD" in codes
