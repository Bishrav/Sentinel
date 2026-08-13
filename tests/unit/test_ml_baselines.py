from datetime import datetime, timezone
from uuid import UUID

from sentinel_ml.baselines import OnlineBaselineStore
from sentinel_ml.models import BehavioralFeatureVector


def vector(event_id: str, value: float) -> BehavioralFeatureVector:
    return BehavioralFeatureVector(
        event_id=UUID(event_id),
        entity_id="user-42",
        entity_type="user",
        timestamp=datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc),
        features={"request_rate": value, "failure_rate": value / 10},
    )


def test_online_baseline_uses_population_statistics() -> None:
    store = OnlineBaselineStore()
    assert store.update_many(
        [
            vector("12345678-1234-4234-8234-123456789012", 10),
            vector("12345678-1234-4234-8234-123456789013", 20),
            vector("12345678-1234-4234-8234-123456789014", 30),
        ]
    ) == 3

    baseline = store.get("user-42")

    assert baseline is not None
    assert baseline.observation_count == 3
    assert baseline.feature_names == ("failure_rate", "request_rate")
    assert baseline.means["request_rate"] == 20.0
    assert baseline.standard_deviations["request_rate"] == 8.16496580927726


def test_baseline_update_is_idempotent_and_ordered() -> None:
    store = OnlineBaselineStore()
    first = vector("12345678-1234-4234-8234-123456789012", 10)

    assert store.update(first) is True
    assert store.update(first) is False
    assert store.get("missing") is None
    assert [baseline.entity_id for baseline in store.all()] == ["user-42"]
