from __future__ import annotations

from endurance_agent_lab.analytics import derive_metrics
from endurance_agent_lab.providers import RuleBasedProvider
from endurance_agent_lab.rendering import render_audit_markdown


def test_markdown_renders_athlete_state_and_limiters_together(benchmark, skill) -> None:
    case = benchmark.by_id("END-016")
    audit = RuleBasedProvider().audit(case, skill, derive_metrics(case.context)).audit

    markdown = render_audit_markdown(audit)

    assert audit.athlete_state
    assert audit.limiters
    assert "## Current athlete state" in markdown
    assert audit.athlete_state[0].capability in markdown
    assert "## Limiters" in markdown
    assert audit.limiters[0].limiter in markdown
