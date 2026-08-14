"""Versioned contracts for evidence-weighted risk scoring."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RiskBand = Literal["low", "medium", "high", "critical"]


class RiskInput(BaseModel):
    """Normalized evidence signals used by the deterministic risk engine."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    severity: Literal["low", "medium", "high", "critical"]
    anomaly_score: float = Field(default=0, ge=0, le=100)
    sequence_confidence: float = Field(default=0, ge=0, le=1)
    graph_risk_score: float = Field(default=0, ge=0, le=100)
    evidence_count: int = Field(default=0, ge=0, le=1000)


class RiskAssessment(BaseModel):
    """Explainable bounded score with each weighted contribution preserved."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    score: float = Field(ge=0, le=100)
    band: RiskBand
    components: dict[str, float] = Field(min_length=1)
    formula_version: Literal["1.0"] = "1.0"


class RiskAuditRecord(BaseModel):
    """Immutable record of inputs and output used for later review or replay."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    recorded_at: datetime
    inputs: RiskInput
    assessment: RiskAssessment
