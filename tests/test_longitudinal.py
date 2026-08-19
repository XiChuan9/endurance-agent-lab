from __future__ import annotations

from datetime import date

from endurance_agent_lab.io import dump_data
from endurance_agent_lab.longitudinal import (
    add_snapshot,
    attach_audit,
    initialize_track,
    latest_snapshot,
)
from endurance_agent_lab.models.audit import (
    AuditOutput,
    DataQualityAssessment,
    GoalAnalysis,
    OverallAssessment,
    UncertaintyAssessment,
)
from endurance_agent_lab.models.common import Feasibility, OverallVerdict, RiskLevel


def test_private_track_preserves_snapshot_and_attaches_audit(tmp_path, project_root) -> None:
    private_root = tmp_path / "private"
    track_dir = initialize_track(private_root, "athlete-001")
    context_path = project_root / "examples" / "private-athlete-context.template.yaml"
    record = add_snapshot(track_dir, context_path, date(2026, 8, 18), "initial")

    manifest, latest, context = latest_snapshot(track_dir)
    assert manifest.privacy == "private-do-not-commit"
    assert latest.snapshot_id == record.snapshot_id
    assert context.athlete.athlete_id == "replace-with-local-private-id"
    assert (private_root / ".gitignore").read_text(encoding="utf-8") == "*\n!.gitignore\n"

    audit = AuditOutput(
        data_quality=DataQualityAssessment(completeness=0.8),
        goal_analysis=GoalAnalysis(
            relation_to_history="test",
            feasibility=Feasibility.UNKNOWN,
            rationale="test",
            confidence=0.5,
        ),
        uncertainty=UncertaintyAssessment(should_not_infer=["exact thresholds"]),
        overall_assessment=OverallAssessment(
            verdict=OverallVerdict.REVISE,
            risk_level=RiskLevel.LOW,
            summary="test",
            confidence=0.5,
        ),
    )
    source = dump_data(audit, tmp_path / "audit.json")
    destination = attach_audit(track_dir, record.snapshot_id, source)
    assert destination.is_file()
    refreshed, _, _ = latest_snapshot(track_dir)
    assert refreshed.snapshots[0].audit_path is not None
