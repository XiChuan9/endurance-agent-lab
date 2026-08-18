from __future__ import annotations

import time
from pathlib import Path

from ..analytics.derived import DerivedMetrics
from ..io import load_model
from ..models.audit import AuditOutput
from ..models.benchmark import BenchmarkCase
from ..models.run import ProviderResult
from ..skills.loader import SkillBundle
from .base import AuditProvider, ProviderError


class ReplayProvider(AuditProvider):
    name = "replay"

    def __init__(self, outputs_dir: str | Path, model: str = "imported-output") -> None:
        self.outputs_dir = Path(outputs_dir)
        self.model = model

    def audit(
        self,
        case: BenchmarkCase,
        skill: SkillBundle,
        derived: DerivedMetrics,
    ) -> ProviderResult:
        del skill, derived
        started = time.perf_counter()
        candidates = [
            self.outputs_dir / f"{case.case_id}.json",
            self.outputs_dir / case.case_id / "audit.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                audit = load_model(candidate, AuditOutput)
                audit.case_id = case.case_id
                return ProviderResult(
                    provider=self.name,
                    model=self.model,
                    audit=audit,
                    latency_seconds=time.perf_counter() - started,
                )
        raise ProviderError(f"No replay output found for {case.case_id} in {self.outputs_dir}.")
