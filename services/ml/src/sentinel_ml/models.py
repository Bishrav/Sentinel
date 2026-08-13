"""Typed contracts for behavioral feature vectors and entity baselines."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EntityType = Literal["user", "service_account", "api_client", "device", "unknown"]


class BehavioralFeatureVector(BaseModel):
    """Deterministic numeric representation of one security event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    entity_id: str = Field(min_length=1)
    entity_type: EntityType
    timestamp: datetime
    features: dict[str, float] = Field(min_length=1)
    schema_version: Literal["1.0"] = "1.0"


class EntityBaseline(BaseModel):
    """Metadata and statistics for a future per-entity anomaly model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str = Field(min_length=1)
    entity_type: EntityType
    observation_count: int = Field(default=0, ge=0)
    feature_names: tuple[str, ...] = ()
    means: dict[str, float] = Field(default_factory=dict)
    standard_deviations: dict[str, float] = Field(default_factory=dict)
    updated_at: datetime
    schema_version: Literal["1.0"] = "1.0"


class FeatureAnomaly(BaseModel):
    """One feature's deviation from an entity baseline."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_name: str = Field(min_length=1)
    observed_value: float
    baseline_mean: float
    baseline_standard_deviation: float
    z_score: float


class AnomalyScore(BaseModel):
    """Explainable anomaly result for one feature vector."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    entity_id: str = Field(min_length=1)
    score: float = Field(ge=0.0)
    is_anomalous: bool
    features: tuple[FeatureAnomaly, ...] = ()
    top_contributors: tuple[str, ...] = ()
    baseline_observation_count: int = Field(ge=0)
    schema_version: Literal["1.0"] = "1.0"
