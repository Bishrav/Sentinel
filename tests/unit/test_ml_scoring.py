from datetime import UTC, datetime
from uuid import UUID

from sentinel_ml.models import BehavioralFeatureVector, EntityBaseline
from sentinel_ml.scoring import score_vector


def vector(value: float) -> BehavioralFeatureVector:
    return BehavioralFeatureVector(
        event_id=UUID("12345678-1234-4234-8234-123456789099"),
        entity_id="user-42",
        entity_type="user",
        timestamp=datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
        features={"request_rate": value, "bytes_transferred": 100.0},
    )


def baseline(observation_count: int = 5) -> EntityBaseline:
    return EntityBaseline(
        entity_id="user-42",
        entity_type="user",
        observation_count=observation_count,
        feature_names=("bytes_transferred", "request_rate"),
        means={"request_rate": 10.0, "bytes_transferred": 100.0},
        standard_deviations={"request_rate": 2.0, "bytes_transferred": 0.0},
        updated_at=datetime(2026, 8, 13, 11, 0, tzinfo=UTC),
    )


def test_scoring_returns_z_score_and_top_contributor() -> None:
    result = score_vector(vector(20.0), baseline())

    assert result.score == 5.0
    assert result.is_anomalous is True
    assert result.top_contributors[0] == "request_rate"
    assert result.features[0].z_score == 5.0


def test_insufficient_baseline_is_not_anomalous() -> None:
    result = score_vector(vector(20.0), baseline(observation_count=1))

    assert result.score == 5.0
    assert result.is_anomalous is False


def test_mismatched_entity_and_invalid_threshold_fail() -> None:
    try:
        score_vector(vector(20.0), baseline().model_copy(update={"entity_id": "other"}))
    except ValueError as error:
        assert "different entities" in str(error)
    else:
        raise AssertionError("mismatched entity did not fail")

    try:
        score_vector(vector(20.0), baseline(), threshold=0)
    except ValueError:
        return
    raise AssertionError("invalid threshold did not fail")
