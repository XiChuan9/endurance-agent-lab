from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field

from .constants import (
    DEFAULT_BENCHMARK_PATH,
    DEFAULT_PRIVATE_DIR,
    DEFAULT_RUNS_DIR,
    DEFAULT_SKILL_PATH,
)
from .io import load_data
from .models.common import StrictModel
from .resources import resolve_resource_path


class OpenAISettings(StrictModel):
    model: str = "gpt-5.6-luna"
    reasoning_effort: str = "medium"
    timeout_seconds: float = Field(default=180, gt=0)
    max_retries: int = Field(default=3, ge=0, le=10)


class GradingSettings(StrictModel):
    hard_fail_caps_score: bool = True
    hard_fail_score_cap: float = Field(default=0, ge=0)
    invalid_evidence_penalty: float = Field(default=0.5, ge=0)
    unexpected_claim_penalty: float = Field(default=0, ge=0)


class Settings(StrictModel):
    schema_version: str = "1.0"
    provider: str = "rules"
    benchmark_path: Path = Path(DEFAULT_BENCHMARK_PATH)
    skill_path: Path = Path(DEFAULT_SKILL_PATH)
    runs_dir: Path = Path(DEFAULT_RUNS_DIR)
    private_dir: Path = Path(DEFAULT_PRIVATE_DIR)
    workers: int = Field(default=1, ge=1, le=64)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    grading: GradingSettings = Field(default_factory=GradingSettings)


def load_dotenv(path: str | Path = ".env") -> None:
    source = Path(path)
    if not source.exists():
        return
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_settings(config_path: str | Path | None = None) -> Settings:
    load_dotenv()
    if config_path is None:
        default = resolve_resource_path("config/default.yaml")
        data = load_data(default) if default.exists() else {}
    else:
        data = load_data(config_path)

    data = dict(data or {})
    data["provider"] = os.getenv("EAL_PROVIDER", data.get("provider", "rules"))
    data["benchmark_path"] = os.getenv(
        "EAL_BENCHMARK", data.get("benchmark_path", DEFAULT_BENCHMARK_PATH)
    )
    data["skill_path"] = os.getenv("EAL_SKILL", data.get("skill_path", DEFAULT_SKILL_PATH))
    data["runs_dir"] = os.getenv("EAL_RUNS_DIR", data.get("runs_dir", DEFAULT_RUNS_DIR))
    data["private_dir"] = os.getenv("EAL_PRIVATE_DIR", data.get("private_dir", DEFAULT_PRIVATE_DIR))
    data["benchmark_path"] = resolve_resource_path(data["benchmark_path"])
    data["skill_path"] = resolve_resource_path(data["skill_path"])

    openai_data = dict(data.get("openai", {}))
    openai_data["model"] = os.getenv(
        "EAL_OPENAI_MODEL", openai_data.get("model", "gpt-5.6-luna")
    )
    openai_data["reasoning_effort"] = os.getenv(
        "EAL_OPENAI_REASONING_EFFORT", openai_data.get("reasoning_effort", "medium")
    )
    openai_data["timeout_seconds"] = float(
        os.getenv(
            "EAL_OPENAI_TIMEOUT_SECONDS",
            str(openai_data.get("timeout_seconds", 180)),
        )
    )
    data["openai"] = openai_data
    return Settings.model_validate(data)
