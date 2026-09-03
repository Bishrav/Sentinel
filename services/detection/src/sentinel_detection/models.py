"""Versioned contracts for rule evaluation and incident aggregation."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from sentinel_risk.models import RiskAuditRecord, RiskBand

ConditionOperator = Literal[
    "eq",
    "neq",
    "in",
    "not_in",
    "contains",
    "regex",
    "exists",
    "gt",
    "gte",
    "lt",
    "lte",
]
MatchMode = Literal["all", "any"]
IncidentStatus = Literal["open", "acknowledged", "closed"]
Severity = Literal["low", "medium", "high", "critical"]


class RuleCondition(BaseModel):
    """One safe, data-only predicate in a detection rule."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    field: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_.]*$", min_length=1)
    operator: ConditionOperator
    value: Any = None


class DetectionRule(BaseModel):
    """Declarative rule definition with no executable expressions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Severity
    conditions: list[RuleCondition] = Field(min_length=1)
    match_mode: MatchMode = "all"
    tags: frozenset[str] = frozenset()
    enabled: bool = True


class RuleMatch(BaseModel):
    """An explainable match between one rule and one canonical event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str
    rule_version: int
    event_id: UUID
    matched_at: datetime
    severity: Severity
    evidence: dict[str, Any] = Field(min_length=1)
    fingerprint: str = Field(min_length=1)


class Incident(BaseModel):
    """Replay-safe aggregate of related rule matches."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    fingerprint: str = Field(min_length=1)
    status: IncidentStatus = "open"
    first_seen: datetime
    last_seen: datetime
    severity: Severity
    rule_ids: frozenset[str] = frozenset()
    event_ids: tuple[UUID, ...] = ()
    actor_ids: frozenset[str] = frozenset()
    resources: frozenset[str] = frozenset()
    match_count: int = Field(default=0, ge=0)
    evidence: tuple[dict[str, Any], ...] = ()
    risk_score: float | None = Field(default=None, ge=0, le=100)
    risk_band: RiskBand | None = None
    risk_audit: RiskAuditRecord | None = None
    schema_version: Literal["1.0"] = "1.0"
