from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def load_data(path: str | Path) -> Any:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")
    text = source.read_text(encoding="utf-8")
    suffix = source.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported file format: {source.suffix}")


def load_model(path: str | Path, model_type: type[T]) -> T:
    return model_type.model_validate(load_data(path))


def dump_data(data: Any, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json", exclude_none=True)
    suffix = destination.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    elif suffix == ".json":
        rendered = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=False)
    else:
        raise ValueError(f"Unsupported file format: {destination.suffix}")
    atomic_write_text(destination, rendered.rstrip() + "\n")
    return destination


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
