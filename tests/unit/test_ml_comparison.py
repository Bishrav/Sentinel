from datetime import UTC, datetime
from uuid import UUID

from sentinel_ml.comparison import compare_baseline, compare_detectors
from sentinel_ml.models import BehavioralFeatureVector, EntityBaseline, LabeledFeatureVector


def sample(number: int, label: bool) -> LabeledFeatureVector:
    return LabeledFeatureVector(
        vector=BehavioralFeatureVector(
            event_id=UUID(f"12345678-1234-4234-8234-{number:012d}"),
            entity_id="user-42",
            entity_type="user",
            timestamp=datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
            features={"request_rate": float(number)},
        ),
        is_anomalous=label,
    )


def test_comparison_selects_highest_f1_predictor() -> None:
    samples = [sample(1, False), sample(2, False), sample(10, True), sample(12, True)]
    result = compare_detectors(
        samples,
        [
            ("always-benign", lambda vector: False),
            ("threshold", lambda vector: vector.features["request_rate"] >= 10),
        ],
    )

    assert [metric.estimator_name for metric in result.results] == ["always-benign", "threshold"]
    assert result.best_by_f1 == "threshold"
    assert result.results[1].f1 == 1.0


def test_baseline_comparison_uses_typed_result() -> None:
    baseline = EntityBaseline(
        entity_id="user-42",
        entity_type="user",
        observation_count=5,
        feature_names=("request_rate",),
        means={"request_rate": 10.0},
        standard_deviations={"request_rate": 1.0},
        updated_at=datetime(2026, 8, 13, 11, 0, tzinfo=UTC),
    )
    result = compare_baseline(
        [sample(10, False), sample(15, True)],
        baseline,
        threshold=3.0,
    )

    assert result.best_by_f1 == "z_score_baseline"
    assert result.results[0].true_positives == 1
