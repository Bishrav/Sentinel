from math import isclose

from sentinel_ingestion.normalizer import normalize
from sentinel_ml.features import extract_features


def test_feature_extraction_is_deterministic_and_numeric() -> None:
    event = normalize(
        {
            "event_id": "12345678-1234-4234-8234-123456789012",
            "timestamp": "2026-08-13T06:00:00Z",
            "actor_id": "user-42",
            "actor_type": "user",
            "action": "role_change",
            "resource": "billing-admin",
            "result": "failure",
            "request_rate": 12,
            "bytes": "2048",
            "endpoint_frequency": 4,
        },
        source="test",
    )

    first = extract_features(event)
    second = extract_features(event)

    assert first == second
    assert first.entity_id == "user-42"
    assert first.features["is_failure"] == 1.0
    assert first.features["permission_usage"] == 1.0
    assert first.features["request_rate"] == 12.0
    assert first.features["bytes_transferred"] == 2048.0
    assert isclose(first.features["login_hour_sin"], 1.0)


def test_missing_optional_telemetry_defaults_to_zero() -> None:
    event = normalize(
        {
            "event_id": "12345678-1234-4234-8234-123456789013",
            "timestamp": "2026-08-13T12:00:00Z",
            "actor_id": "service-1",
            "actor_type": "service",
            "action": "read",
            "resource": "billing.transactions",
            "result": "success",
        },
        source="test",
    )

    features = extract_features(event).features

    assert features["request_rate"] == 0.0
    assert features["response_size"] == 0.0
    assert features["bytes_transferred"] == 0.0
    assert features["permission_usage"] == 0.0
