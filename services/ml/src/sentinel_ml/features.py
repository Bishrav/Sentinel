"""Deterministic behavioral feature extraction from canonical events."""

from __future__ import annotations

import math
from typing import Any

from sentinel_ingestion.models import SecurityEvent

from .models import BehavioralFeatureVector


def _number(attributes: dict[str, Any], *names: str) -> float:
    for name in names:
        value = attributes.get(name)
        if isinstance(value, bool):
            return float(value)
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return 0.0


def extract_features(event: SecurityEvent) -> BehavioralFeatureVector:
    """Extract stable numeric features without fitting or external state."""

    hour = event.timestamp.hour + event.timestamp.minute / 60.0
    hour_angle = 2.0 * math.pi * hour / 24.0
    attributes = event.attributes
    action = event.action.lower()
    permission_action = any(term in action for term in ("role", "permission", "grant", "revoke"))
    features = {
        "login_hour_sin": math.sin(hour_angle),
        "login_hour_cos": math.cos(hour_angle),
        "day_of_week": float(event.timestamp.weekday()),
        "is_failure": float(event.result == "failure"),
        "is_authentication": float(any(term in action for term in ("login", "logout", "auth"))),
        "permission_usage": float(permission_action),
        "request_rate": _number(attributes, "request_rate", "requests_per_minute"),
        "response_size": _number(attributes, "response_size", "response_bytes"),
        "bytes_transferred": _number(attributes, "bytes", "bytes_transferred"),
        "endpoint_frequency": _number(attributes, "endpoint_frequency", "endpoint_count"),
    }
    return BehavioralFeatureVector(
        event_id=event.event_id,
        entity_id=event.actor_id,
        entity_type=event.actor_type,
        timestamp=event.timestamp,
        features=features,
    )
