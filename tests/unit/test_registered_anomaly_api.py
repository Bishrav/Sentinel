from fastapi.testclient import TestClient

from sentinel_api.main import app, baseline_registry
from tests.unit.test_anomaly_api import payload
from sentinel_ml.models import EntityBaseline


client = TestClient(app)


def test_registered_anomaly_endpoint_uses_process_registry() -> None:
    request = payload()
    baseline_registry.register(EntityBaseline.model_validate(request["baseline"]))

    response = client.post(
        "/v1/anomaly/score/user-42?threshold=3",
        json=request["vector"],
    )

    assert response.status_code == 200
    assert response.json()["score"] == 5.0


def test_registered_anomaly_endpoint_returns_404_for_unknown_entity() -> None:
    response = client.post(
        "/v1/anomaly/score/unknown-user?threshold=3",
        json=payload()["vector"],
    )

    assert response.status_code == 404
