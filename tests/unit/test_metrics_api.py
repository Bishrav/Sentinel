from fastapi.testclient import TestClient

from sentinel_api.main import app


client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_text() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "sentinel_ml_score_requests_total" in response.text
    assert response.headers["content-type"].startswith("text/plain")
