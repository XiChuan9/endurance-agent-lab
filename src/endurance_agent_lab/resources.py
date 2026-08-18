from __future__ import annotations

import sysconfig
from pathlib import Path

from .constants import PACKAGE_NAME


def installed_share_root() -> Path:
    """Return the platform data directory used by setuptools data-files."""
    return Path(sysconfig.get_path("data")) / "share" / PACKAGE_NAME


def resolve_resource_path(path: str | Path) -> Path:
    """Prefer a repository-relative resource, then the installed wheel copy.

    User-supplied absolute paths are never rewritten. Nonexistent custom relative
    paths are returned unchanged so callers can surface a precise validation error.
    """
    candidate = Path(path).expanduser()
    if candidate.is_absolute() or candidate.exists():
        return candidate
    installed = installed_share_root() / candidate
    return installed if installed.exists() else candidate
