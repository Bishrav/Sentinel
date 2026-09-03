from datetime import UTC, datetime
from uuid import UUID

import pytest

from sentinel_ml.estimators import IsolationForestEstimator
from sentinel_ml.models import BehavioralFeatureVector


def vector(event_id: int, value: float) -> BehavioralFeatureVector:
    return BehavioralFeatureVector(
        event_id=UUID(f"12345678-1234-4234-8234-{event_id:012d}"),
        entity_id="user-42",
        entity_type="user",
        timestamp=datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
        features={"request_rate": value, "failure_rate": value / 10},
    )


def test_estimator_validates_lifecycle_and_training_shape() -> None:
    estimator = IsolationForestEstimator(n_estimators=20)
    with pytest.raises(RuntimeError, match="required"):
        estimator.score(vector(1, 10))
    with pytest.raises(ValueError, match="at least two"):
        estimator.fit([vector(1, 10)])
    with pytest.raises(ValueError, match="one entity"):
        estimator.fit([vector(1, 10), vector(2, 11).model_copy(update={"entity_id": "other"})])


def test_estimator_fits_and_scores_when_sklearn_is_available() -> None:
    pytest.importorskip("sklearn")
    estimator = IsolationForestEstimator(n_estimators=20, random_state=7)
    metadata = estimator.fit([vector(index, 10 + index * 0.1) for index in range(1, 11)])
    result = estimator.score(vector(99, 100))

    assert metadata.estimator_name == "isolation_forest"
    assert metadata.feature_names == ("failure_rate", "request_rate")
    assert metadata.observation_count == 10
    assert result.estimator == "isolation_forest"
    assert result.entity_id == "user-42"
