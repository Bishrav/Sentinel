from uuid import uuid4

from fastapi.testclient import TestClient

from sentinel_api.main import app

client = TestClient(app)


def test_investigation_endpoint_returns_citation_complete_envelope() -> None:
    response = client.post(
        "/v1/investigations",
        json={
            "incident_id": str(uuid4()),
            "question": "What evidence is available?",
            "evidence": [
                {
                    "reference_type": "incident",
                    "reference_id": "incident-001",
                    "source": "incident-store",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "1.0"
    assert payload["hypotheses"] == []
    assert payload["cited_evidence"][0]["reference_id"] == "incident-001"
    assert payload["runbooks"][0]["runbook_id"] == "graph-relationship-investigation"


def test_provider_mode_returns_not_implemented_until_adapter_is_configured() -> None:
    response = client.post(
        "/v1/investigations",
        json={
            "incident_id": str(uuid4()),
            "question": "Explain this incident.",
            "mode": "provider",
            "evidence": [
                {
                    "reference_type": "event",
                    "reference_id": "event-001",
                    "source": "fixture",
                }
            ],
        },
    )

    assert response.status_code == 501
    assert response.json()["detail"] == "no investigation provider is configured"
