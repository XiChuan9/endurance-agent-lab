from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from .common import StrictModel


class TrackSnapshotRecord(StrictModel):
    snapshot_id: str
    effective_date: date
    context_path: str
    context_hash: str
    audit_path: str | None = None
    outcome_path: str | None = None
    created_at: datetime
    notes: str | None = None


class TrackManifest(StrictModel):
    schema_version: str = "1.0"
    athlete_id: str
    created_at: datetime
    privacy: str = "private-do-not-commit"
    snapshots: list[TrackSnapshotRecord] = Field(default_factory=list)
