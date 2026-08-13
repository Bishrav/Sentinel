"""Typed contracts for finite-state sequence detection."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from sentinel_detection.models import RuleCondition, Severity


class SequenceStep(BaseModel):
    """One ordered state in a sequence signature."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    conditions: tuple[RuleCondition, ...] = Field(min_length=1)


class SequenceSignature(BaseModel):
    """Versioned, bounded temporal sequence definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    signature_id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    version: int = Field(default=1, ge=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    steps: tuple[SequenceStep, ...] = Field(min_length=2)
    window_seconds: int = Field(gt=0)
    allowed_lateness_seconds: int = Field(default=0, ge=0)
    severity: Severity
    enabled: bool = True


class SequenceMatch(BaseModel):
    """Completed sequence with exact event evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    signature_id: str
    signature_version: int
    actor_id: str = Field(min_length=1)
    event_ids: tuple[UUID, ...] = Field(min_length=2)
    started_at: datetime
    completed_at: datetime
    evidence: tuple[dict[str, object], ...] = Field(min_length=2)
    severity: Severity
    schema_version: Literal["1.0"] = "1.0"
