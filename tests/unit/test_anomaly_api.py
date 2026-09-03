from fastapi.testclient import TestClient

from sentinel_api.main import app

client = TestClient(app)


def payload() -> dict:
    return {
        "vector": {
            "event_id": "12345678-1234-4234-8234-123456789012",
            "entity_id": "user-42",
            "entity_type": "user",
            "timestamp": "2026-08-13T12:00:00Z",
            "features": {"request_rate": 20.0},
        },
        "baseline": {
            "entity_id": "user-42",
            "entity_type": "user",
            "observation_count": 5,
            "feature_names": ["request_rate"],
            "means": {"request_rate": 10.0},
            "standard_deviations": {"request_rate": 2.0},
            "updated_at": "2026-08-13T11:00:00Z",
        },
        "threshold": 3.0,
    }


def test_anomaly_endpoint_returns_explainable_score() -> None:
    response = client.post("/v1/anomaly/score", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 5.0
    assert body["is_anomalous"] is True
    assert body["top_contributors"] == ["request_rate"]


def test_anomaly_endpoint_rejects_mismatched_entity() -> None:
    request = payload()
    request["baseline"]["entity_id"] = "other-user"

    response = client.post("/v1/anomaly/score", json=request)

    assert response.status_code == 422
    assert "different entities" in response.json()["detail"]
