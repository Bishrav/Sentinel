"""Normalize source-specific telemetry into the canonical event contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from .models import ActorType, EventResult, SecurityEvent, Severity

_MISSING = object()


def _first(raw: Mapping[str, Any], *keys: str, default: Any = _MISSING) -> Any:
    for key in keys:
        value = raw.get(key, _MISSING)
        if value is not _MISSING and value not in (None, ""):
            return value
    if default is not _MISSING:
        return default
    raise ValueError(f"missing required source field; expected one of: {', '.join(keys)}")


def _actor_type(value: Any) -> ActorType:
    normalized = str(value or "unknown").strip().lower().replace("-", "_")
    aliases = {"service": "service_account", "api": "api_client"}
    candidate = aliases.get(normalized, normalized)
    return candidate if candidate in {"user", "service_account", "api_client", "device"} else "unknown"


def _result(value: Any) -> EventResult:
    normalized = str(value or "unknown").strip().lower()
    if normalized in {"success", "succeeded", "ok", "allowed", "200"}:
        return "success"
    if normalized in {"failure", "failed", "error", "denied", "blocked", "401", "403"}:
        return "failure"
    return "unknown"


def _severity(value: Any, *, action: str, result: EventResult) -> Severity:
    if value:
        normalized = str(value).strip().lower()
        if normalized in {"low", "medium", "high", "critical"}:
            return normalized  # type: ignore[return-value]
    if result == "failure" and any(term in action for term in ("login", "auth", "permission")):
        return "medium"
    if any(term in action for term in ("delete", "export", "secret", "role_change")):
        return "high"
    return "low"


def _timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def normalize(raw: Mapping[str, Any], *, source: str) -> SecurityEvent:
    """Map common source aliases into a stable, versioned ``SecurityEvent``.

    An absent event ID is derived from the source and canonical source payload,
    making ingestion idempotent when the same record is replayed.
    """

    action = str(
        _first(raw, "action", "event_action", "operation", default="unknown")
    ).strip().lower()
    result = _result(_first(raw, "result", "status", "outcome", default="unknown"))
    canonical = json.dumps({"source": source, "record": raw}, sort_keys=True, default=str)
    event_id = _first(raw, "event_id", "id", default=None)
    parsed_event_id = UUID(str(event_id)) if event_id else uuid5(NAMESPACE_URL, canonical)

    known_keys = {
        "event_id", "id", "timestamp", "time", "ts", "actor_id", "user_id", "principal",
        "actor_type", "principal_type", "source_ip", "ip", "device_id", "device",
        "action", "event_action", "operation", "resource", "resource_id", "target",
        "result", "status", "outcome", "severity",
    }
    attributes = {key: value for key, value in raw.items() if key not in known_keys}

    return SecurityEvent(
        event_id=parsed_event_id,
        timestamp=_timestamp(_first(raw, "timestamp", "time", "ts")),
        actor_id=str(_first(raw, "actor_id", "user_id", "principal")),
        actor_type=_actor_type(_first(raw, "actor_type", "principal_type", default="unknown")),
        source_ip=_first(raw, "source_ip", "ip", default=None),
        device_id=_first(raw, "device_id", "device", default=None),
        action=action,
        resource=str(_first(raw, "resource", "resource_id", "target", default="unknown")),
        result=result,
        attributes=attributes,
        severity=_severity(_first(raw, "severity", default=None), action=action, result=result),
        source=source,
    )
