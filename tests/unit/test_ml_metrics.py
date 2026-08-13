from uuid import UUID

from sentinel_ml.metrics import AnomalyMetrics
from sentinel_ml.models import AnomalyScore


def score(anomalous: bool) -> AnomalyScore:
    return AnomalyScore(
        event_id=UUID("12345678-1234-4234-8234-123456789012"),
        entity_id="user-42",
        score=5.0,
        is_anomalous=anomalous,
        baseline_observation_count=5,
    )


def test_metrics_render_counters_and_average_latency() -> None:
    metrics = AnomalyMetrics()
    metrics.observe(score(False), 2.0)
    metrics.observe(score(True), 4.0, model="isolation_forest")

    output = metrics.prometheus()

    assert "sentinel_ml_score_requests_total 2" in output
    assert "sentinel_ml_anomalous_requests_total 1" in output
    assert "sentinel_ml_score_latency_ms_average 3.0" in output
    assert 'model="isolation_forest"} 1' in output


def test_negative_latency_is_rejected() -> None:
    metrics = AnomalyMetrics()
    try:
        metrics.observe(score(False), -1.0)
    except ValueError:
        return
    raise AssertionError("negative latency was accepted")
