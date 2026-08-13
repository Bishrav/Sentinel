from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from sentinel_api.main import app, incident_store
from sentinel_detection.models import RuleMatch
from sentinel_ingestion.models import SecurityEvent


client = TestClient(app)


def _seed_incident() -> str:
    event = SecurityEvent(
        event_id=uuid4(),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        actor_id="api-user",
        actor_type="user",
        action="login",
        resource="console",
        result="failure",
        severity="high",
        source="api-test",
    )
    match = RuleMatch(
        rule_id="test_signal",
        rule_version=1,
        event_id=event.event_id,
        matched_at=event.timestamp,
        severity="high",
        evidence={"action": "login"},
        fingerprint="api-user:console",
    )
    incident_store.add(event, (match,))
    return match.fingerprint


def test_incident_list_and_detail_endpoints_return_projection() -> None:
    fingerprint = _seed_incident()

    collection = client.get("/v1/incidents")
    detail = client.get(f"/v1/incidents/{fingerprint}")

    assert collection.status_code == 200
    assert collection.json()["total"] >= 1
    assert any(item["fingerprint"] == fingerprint for item in collection.json()["items"])
    assert detail.status_code == 200
    assert detail.json()["fingerprint"] == fingerprint
    assert detail.json()["match_count"] == 1


def test_incident_detail_returns_not_found() -> None:
    response = client.get("/v1/incidents/missing-fingerprint")
    assert response.status_code == 404
    assert response.json()["detail"] == "incident not found: missing-fingerprint"
