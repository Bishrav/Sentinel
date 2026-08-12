"""Typed canonical event models."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ActorType = Literal["user", "service_account", "api_client", "device", "unknown"]
EventResult = Literal["success", "failure", "unknown"]
Severity = Literal["low", "medium", "high", "critical"]


class SecurityEvent(BaseModel):
    """Normalized event shared by every Sentinel downstream service."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    timestamp: datetime
    actor_id: str = Field(min_length=1)
    actor_type: ActorType
    source_ip: str | None = None
    device_id: str | None = None
    action: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    result: EventResult
    attributes: dict[str, Any] = Field(default_factory=dict)
    severity: Severity
    source: str = Field(min_length=1)
    schema_version: Literal["1.0"] = "1.0"
