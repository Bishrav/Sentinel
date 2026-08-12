import json
from pathlib import Path

from sentinel_ingestion.models import SecurityEvent


def test_security_event_matches_public_schema_shape() -> None:
    schema_path = Path("schemas/security-event.schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    event = SecurityEvent(
        event_id="12345678-1234-4234-8234-123456789012",
        timestamp="2026-08-12T12:00:00Z",
        actor_id="user-42",
        actor_type="user",
        action="login",
        resource="identity-provider",
        result="success",
        severity="low",
        source="auth-service",
    )

    payload = event.model_dump(mode="json")
    assert set(schema["required"]).issubset(payload)
    assert payload["schema_version"] == "1.0"


def test_security_event_rejects_unknown_fields() -> None:
    try:
        SecurityEvent(
            event_id="12345678-1234-4234-8234-123456789012",
            timestamp="2026-08-12T12:00:00Z",
            actor_id="user-42",
            actor_type="user",
            action="login",
            resource="identity-provider",
            result="success",
            severity="low",
            source="auth-service",
            unexpected="value",
        )
    except ValueError:
        return
    raise AssertionError("SecurityEvent accepted an unknown field")
