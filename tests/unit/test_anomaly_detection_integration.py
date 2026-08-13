from uuid import UUID

from sentinel_detection.anomaly import anomaly_to_match
from sentinel_detection.aggregator import IncidentAggregator
from sentinel_detection.pipeline import DetectionPipeline
from sentinel_detection.engine import RuleEngine
from sentinel_ml.models import AnomalyScore, FeatureAnomaly
from sentinel_ingestion.normalizer import normalize


def event():
    return normalize(
        {
            "event_id": "12345678-1234-4234-8234-123456789012",
            "timestamp": "2026-08-13T12:00:00Z",
            "actor_id": "user-42",
            "actor_type": "user",
            "action": "read",
            "resource": "billing.transactions",
            "result": "success",
        },
        source="test",
    )


def score() -> AnomalyScore:
    return AnomalyScore(
        event_id=UUID("12345678-1234-4234-8234-123456789012"),
        entity_id="user-42",
        score=5.0,
        is_anomalous=True,
        features=(
            FeatureAnomaly(
                feature_name="request_rate",
                observed_value=20.0,
                baseline_mean=10.0,
                baseline_standard_deviation=2.0,
                z_score=5.0,
            ),
        ),
        top_contributors=("request_rate",),
        baseline_observation_count=5,
    )


def test_anomaly_score_becomes_incident_evidence() -> None:
    match = anomaly_to_match(event(), score())

    assert match is not None
    assert match.rule_id == "behavioral_anomaly"
    assert match.severity == "high"
    assert match.evidence["top_contributors"] == ["request_rate"]


def test_detection_pipeline_aggregates_ml_signal() -> None:
    pipeline = DetectionPipeline(
        RuleEngine([]),
        aggregator=IncidentAggregator(),
        anomaly_scorer=lambda _: score(),
    )

    incidents = pipeline.process(event())

    assert len(incidents) == 1
    assert incidents[0].rule_ids == frozenset({"behavioral_anomaly"})
    assert incidents[0].evidence[0]["anomaly_score"] == 5.0
