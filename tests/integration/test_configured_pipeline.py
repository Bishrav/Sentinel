from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sentinel_detection.pipeline import build_pipeline
from sentinel_ingestion.models import SecurityEvent


def _event(action: str, result: str, at: datetime) -> SecurityEvent:
    return SecurityEvent(
        event_id=uuid4(),
        timestamp=at,
        actor_id="alice",
        actor_type="user",
        action=action,
        resource="console",
        result=result,  # type: ignore[arg-type]
        severity="high",
        source="test",
    )


def test_configured_pipeline_loads_rules_and_sequences() -> None:
    root = Path(".")
    pipeline = build_pipeline(
        root / "config/rules/default.json",
        root / "config/sequences/default.json",
    )
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    pipeline.process(_event("login", "failure", start))
    pipeline.process(_event("login", "success", start + timedelta(seconds=10)))
    incidents = pipeline.process(_event("role_change", "success", start + timedelta(seconds=20)))

    sequence_incidents = [
        incident for incident in incidents if "sequence:credential_attack:v1" in incident.rule_ids
    ]
    assert len(sequence_incidents) == 1
    assert sequence_incidents[0].severity == "critical"
    assert len(sequence_incidents[0].event_ids) == 3
