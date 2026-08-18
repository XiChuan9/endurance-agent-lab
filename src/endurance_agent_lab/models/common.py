from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Base model used for all persisted public contracts."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=False,
    )


class RaceType(StrEnum):
    FIVE_K = "5k"
    TEN_K = "10k"
    HALF_MARATHON = "half_marathon"
    MARATHON = "marathon"
    ULTRA = "ultra"
    OTHER = "other"


class Sport(StrEnum):
    RUN = "run"
    BIKE = "bike"
    SWIM = "swim"
    STRENGTH = "strength"
    CROSS_TRAIN = "cross_train"
    REST = "rest"
    OTHER = "other"


class Intensity(StrEnum):
    REST = "rest"
    RECOVERY = "recovery"
    EASY = "easy"
    STEADY = "steady"
    LT1 = "lt1"
    THRESHOLD = "threshold"
    RACE_PACE = "race_pace"
    VO2MAX = "vo2max"
    SPRINT = "sprint"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class SignalType(StrEnum):
    RECOVERY = "recovery"
    INJURY = "injury"
    WEATHER = "weather"
    DATA = "data"
    PERFORMANCE = "performance"
    CONSTRAINT = "constraint"
    USER_INSTRUCTION = "user_instruction"
    MEDICAL = "medical"
    OTHER = "other"


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimCategory(StrEnum):
    DATA_QUALITY = "data_quality"
    ATHLETE_STATE = "athlete_state"
    GOAL = "goal"
    LIMITER = "limiter"
    PLAN = "plan"
    SAFETY = "safety"
    UNCERTAINTY = "uncertainty"


class ClaimStance(StrEnum):
    SUPPORTS = "supports"
    REJECTS = "rejects"
    UNCERTAIN = "uncertain"


class Priority(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUPPORTING = "supporting"
    NOT_PRIORITY = "not_priority"
    UNKNOWN = "unknown"


class CapabilityStatus(StrEnum):
    STRONG = "strong"
    ADEQUATE = "adequate"
    DEVELOPING = "developing"
    WEAK = "weak"
    REBUILDING = "rebuilding"
    UNKNOWN = "unknown"


class RecommendationAction(StrEnum):
    KEEP = "keep"
    MODIFY = "modify"
    REMOVE = "remove"
    ADD = "add"
    HOLD = "hold"
    ESCALATE = "escalate"


class OverallVerdict(StrEnum):
    APPROVE = "approve"
    APPROVE_WITH_CHANGES = "approve_with_changes"
    REVISE = "revise"
    HOLD = "hold"
    INSUFFICIENT_DATA = "insufficient_data"


class Feasibility(StrEnum):
    CONSERVATIVE = "conservative"
    REALISTIC = "realistic"
    STRETCH = "stretch"
    UNREALISTIC = "unrealistic"
    RETURN_TO_FORM = "return_to_form"
    UNKNOWN = "unknown"


class ScoreDimension(StrEnum):
    DIAGNOSIS = "diagnosis"
    PLAN_REASONING = "plan_reasoning"
    EVIDENCE_GROUNDING = "evidence_grounding"
    UNCERTAINTY = "uncertainty"
    SAFETY = "safety"
    INSTRUCTION_SCHEMA = "instruction_schema"


class KeyValue(StrictModel):
    key: str
    value: Any


class ConfidenceMixin(StrictModel):
    confidence: float = Field(ge=0.0, le=1.0)
