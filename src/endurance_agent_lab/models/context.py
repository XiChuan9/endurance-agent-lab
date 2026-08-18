from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import Field, model_validator

from .common import Intensity, RaceType, SignalType, Sport, StrictModel


Scalar = str | int | float | bool


class AthleteProfile(StrictModel):
    athlete_id: str = "anonymous"
    display_name: str | None = None
    age: int | None = Field(default=None, ge=10, le=100)
    sex: str | None = None
    sport_experience_years: float | None = Field(default=None, ge=0)
    coaching_context: str | None = None


class Goal(StrictModel):
    race_type: RaceType
    race_date: date | None = None
    target_seconds: int | None = Field(default=None, gt=0)
    distance_km: float | None = Field(default=None, gt=0)
    priority: str = "A"
    notes: str | None = None


class PerformanceMarker(StrictModel):
    marker_id: str
    marker_type: str = "race"
    sport: Sport = Sport.RUN
    distance_km: float | None = Field(default=None, gt=0)
    time_seconds: int | None = Field(default=None, gt=0)
    marker_date: date | None = None
    pace_seconds_per_km: float | None = Field(default=None, gt=0)
    label: str | None = None
    conditions: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def derive_pace(self) -> "PerformanceMarker":
        if self.pace_seconds_per_km is None and self.distance_km and self.time_seconds:
            self.pace_seconds_per_km = self.time_seconds / self.distance_km
        return self


class TrainingSession(StrictModel):
    session_id: str
    session_date: date | None = None
    sport: Sport = Sport.RUN
    title: str
    intensity: Intensity = Intensity.UNKNOWN
    is_quality: bool = False
    distance_km: float | None = Field(default=None, ge=0)
    duration_minutes: float | None = Field(default=None, ge=0)
    pace_seconds_per_km: float | None = Field(default=None, gt=0)
    avg_hr: float | None = Field(default=None, gt=0)
    max_hr: float | None = Field(default=None, gt=0)
    rpe: float | None = Field(default=None, ge=0, le=10)
    elevation_m: float | None = Field(default=None, ge=0)
    completed: bool | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def derive_session_pace(self) -> "TrainingSession":
        if (
            self.pace_seconds_per_km is None
            and self.distance_km
            and self.duration_minutes
            and self.distance_km > 0
        ):
            self.pace_seconds_per_km = self.duration_minutes * 60 / self.distance_km
        return self


class TrainingWeek(StrictModel):
    week_id: str
    relative_week: int | None = None
    start_date: date | None = None
    distance_km: float | None = Field(default=None, ge=0)
    duration_hours: float | None = Field(default=None, ge=0)
    sessions: list[TrainingSession] = Field(default_factory=list)
    notes: str | None = None

    @model_validator(mode="after")
    def derive_week_totals(self) -> "TrainingWeek":
        if self.distance_km is None and self.sessions:
            values = [s.distance_km for s in self.sessions if s.distance_km is not None]
            self.distance_km = round(sum(values), 3) if values else None
        if self.duration_hours is None and self.sessions:
            values = [s.duration_minutes for s in self.sessions if s.duration_minutes is not None]
            self.duration_hours = round(sum(values) / 60, 3) if values else None
        return self


class TrainingHistory(StrictModel):
    weeks: list[TrainingWeek] = Field(default_factory=list)
    source: str = "manual"
    completeness_note: str | None = None


class TrainingPlan(StrictModel):
    plan_id: str = "proposed-plan"
    title: str = "Proposed training plan"
    weeks: list[TrainingWeek] = Field(default_factory=list)
    philosophy: str | None = None
    notes: str | None = None


class ContextSignal(StrictModel):
    signal_id: str
    signal_type: SignalType
    key: str
    value: Scalar
    unit: str | None = None
    severity: str | None = None
    observed_date: date | None = None
    notes: str | None = None


class SourceNote(StrictModel):
    source_id: str
    text: str


class AthleteContext(StrictModel):
    schema_version: str = "1.0"
    as_of_date: date | None = None
    athlete: AthleteProfile
    goal: Goal
    performance_markers: list[PerformanceMarker] = Field(default_factory=list)
    recent_training: TrainingHistory = Field(default_factory=TrainingHistory)
    signals: list[ContextSignal] = Field(default_factory=list)
    proposed_plan: TrainingPlan | None = None
    source_notes: list[SourceNote] = Field(default_factory=list)
    user_request: str = "Audit the proposed training plan."
    language: Annotated[str, Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")] = "en"
