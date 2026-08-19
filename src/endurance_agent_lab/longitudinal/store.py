from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from ..io import dump_data, load_model
from ..models.context import AthleteContext
from ..models.track import TrackManifest, TrackSnapshotRecord
from ..utils import compact_timestamp, sha256_file, utc_now


def initialize_track(root: str | Path, athlete_id: str) -> Path:
    track_dir = Path(root) / "athletes" / athlete_id
    if (track_dir / "track.yaml").exists():
        raise FileExistsError(f"Track already exists: {track_dir}")
    (track_dir / "snapshots").mkdir(parents=True, exist_ok=True)
    (track_dir / "audits").mkdir(parents=True, exist_ok=True)
    (track_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    manifest = TrackManifest(athlete_id=athlete_id, created_at=utc_now())
    dump_data(manifest, track_dir / "track.yaml")
    (Path(root) / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
    return track_dir


def add_snapshot(
    track_dir: str | Path,
    context_path: str | Path,
    effective_date: date,
    notes: str | None = None,
) -> TrackSnapshotRecord:
    root = Path(track_dir)
    manifest_path = root / "track.yaml"
    manifest = load_model(manifest_path, TrackManifest)
    context = load_model(context_path, AthleteContext)
    snapshot_id = f"{effective_date.isoformat()}-{compact_timestamp()}"
    destination = root / "snapshots" / f"{snapshot_id}.yaml"
    dump_data(context, destination)
    record = TrackSnapshotRecord(
        snapshot_id=snapshot_id,
        effective_date=effective_date,
        context_path=destination.relative_to(root).as_posix(),
        context_hash=sha256_file(destination),
        created_at=utc_now(),
        notes=notes,
    )
    manifest.snapshots.append(record)
    manifest.snapshots.sort(key=lambda item: (item.effective_date, item.created_at))
    dump_data(manifest, manifest_path)
    return record


def latest_snapshot(
    track_dir: str | Path,
) -> tuple[TrackManifest, TrackSnapshotRecord, AthleteContext]:
    root = Path(track_dir)
    manifest = load_model(root / "track.yaml", TrackManifest)
    if not manifest.snapshots:
        raise ValueError("The track has no snapshots.")
    record = manifest.snapshots[-1]
    context = load_model(root / record.context_path, AthleteContext)
    return manifest, record, context


def attach_audit(track_dir: str | Path, snapshot_id: str, audit_path: str | Path) -> Path:
    root = Path(track_dir)
    manifest_path = root / "track.yaml"
    manifest = load_model(manifest_path, TrackManifest)
    record = next((item for item in manifest.snapshots if item.snapshot_id == snapshot_id), None)
    if record is None:
        raise KeyError(f"Unknown snapshot: {snapshot_id}")
    source = Path(audit_path)
    destination = root / "audits" / f"{snapshot_id}-audit.json"
    shutil.copy2(source, destination)
    record.audit_path = destination.relative_to(root).as_posix()
    dump_data(manifest, manifest_path)
    return destination
