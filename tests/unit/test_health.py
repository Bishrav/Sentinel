from fastapi.testclient import TestClient

from sentinel_api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["authentication"] in {"enabled", "local-disabled"}
    assert response.json()["persistence"] in {"sqlite", "in-memory"}
