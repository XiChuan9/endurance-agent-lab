from __future__ import annotations

import hashlib
from pathlib import Path

_IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
_IGNORED_FILE_NAMES = {".DS_Store"}
_IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _hashable_file(root: Path, file_path: Path) -> bool:
    relative = file_path.relative_to(root)
    if any(part in _IGNORED_DIRECTORY_NAMES for part in relative.parts[:-1]):
        return False
    if file_path.name in _IGNORED_FILE_NAMES or file_path.suffix in _IGNORED_SUFFIXES:
        return False
    return file_path.is_file()


def sha256_tree(path: str | Path) -> str:
    """Hash a source tree independently of transient interpreter/tool artifacts."""
    root = Path(path)
    digest = hashlib.sha256()
    for file_path in sorted(
        (candidate for candidate in root.rglob("*") if _hashable_file(root, candidate)),
        key=lambda candidate: candidate.relative_to(root).as_posix(),
    ):
        relative = file_path.relative_to(root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
