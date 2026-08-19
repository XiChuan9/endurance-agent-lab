from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from openai.types.shared_params import Reasoning

from ..analytics.derived import DerivedMetrics
from ..models.audit import AuditOutput
from ..models.benchmark import BenchmarkCase
from ..models.run import ProviderResult, UsageRecord
from ..skills.loader import SkillBundle
from .base import AuditProvider, ProviderError


class OpenAIProvider(AuditProvider):
    name = "openai"

    def __init__(
        self,
        model: str,
        reasoning_effort: str = "medium",
        timeout_seconds: float = 180,
        max_retries: int = 3,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def audit(
        self,
        case: BenchmarkCase,
        skill: SkillBundle,
        derived: DerivedMetrics,
    ) -> ProviderResult:
        if not os.getenv("OPENAI_API_KEY"):
            raise ProviderError("OPENAI_API_KEY is not set.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError('The OpenAI provider requires: pip install -e ".[openai]"') from exc

        client = OpenAI(
            timeout=self.timeout_seconds,
            max_retries=self.max_retries,
        )
        system_prompt = (
            skill.render_for_model()
            + "\n\n# Execution contract\n"
            + "Return only the structured audit represented by the supplied schema. "
            + "Use evidence references that exist in the input. Do not invent physiological "
            + "thresholds, diagnoses, activities, or recovery data. The claims array is the "
            + "canonical machine-readable registry of your conclusions."
        )
        payload = {
            "case_id": case.case_id,
            "context": case.context.model_dump(mode="json", exclude_none=True),
            "derived_metrics": derived.model_dump(mode="json", exclude_none=True),
        }
        started = time.perf_counter()
        try:
            reasoning = cast("Reasoning", {"effort": self.reasoning_effort})
            response = client.responses.parse(
                model=self.model,
                reasoning=reasoning,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False, indent=2),
                    },
                ],
                text_format=AuditOutput,
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        latency = time.perf_counter() - started

        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise ProviderError("OpenAI response did not contain output_parsed.")
        audit = parsed if isinstance(parsed, AuditOutput) else AuditOutput.model_validate(parsed)
        audit.case_id = case.case_id

        usage_object = getattr(response, "usage", None)
        usage = UsageRecord(
            input_tokens=_read_usage(usage_object, "input_tokens"),
            output_tokens=_read_usage(usage_object, "output_tokens"),
            total_tokens=_read_usage(usage_object, "total_tokens"),
        )
        raw: dict[str, Any]
        if hasattr(response, "model_dump"):
            raw = response.model_dump(mode="json")
        else:
            raw = {"id": getattr(response, "id", None)}
        return ProviderResult(
            provider=self.name,
            model=self.model,
            audit=audit,
            raw_response=raw,
            usage=usage,
            latency_seconds=latency,
            request_id=getattr(response, "id", None),
        )


def _read_usage(usage: object, name: str) -> int | None:
    if usage is None:
        return None
    value = getattr(usage, name, None)
    if value is None and isinstance(usage, dict):
        value = usage.get(name)
    return int(value) if value is not None else None
