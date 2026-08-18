from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def compact_timestamp(value: datetime | None = None) -> str:
    current = value or utc_now()
    return current.strftime("%Y%m%dT%H%M%SZ")
