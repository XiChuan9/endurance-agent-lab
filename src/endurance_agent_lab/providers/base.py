from __future__ import annotations

from abc import ABC, abstractmethod

from ..analytics.derived import DerivedMetrics
from ..models.benchmark import BenchmarkCase
from ..models.run import ProviderResult
from ..skills.loader import SkillBundle


class ProviderError(RuntimeError):
    pass


class AuditProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def audit(
        self,
        case: BenchmarkCase,
        skill: SkillBundle,
        derived: DerivedMetrics,
    ) -> ProviderResult:
        """Produce one structured audit result for a benchmark case."""
