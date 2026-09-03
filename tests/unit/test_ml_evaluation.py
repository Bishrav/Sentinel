from datetime import UTC, datetime
from uuid import UUID

from sentinel_ml.evaluation import evaluate_predictions
from sentinel_ml.models import BehavioralFeatureVector, LabeledFeatureVector


def sample(event_number: int, label: bool) -> LabeledFeatureVector:
    return LabeledFeatureVector(
        vector=BehavioralFeatureVector(
            event_id=UUID(f"12345678-1234-4234-8234-{event_number:012d}"),
            entity_id="user-42",
            entity_type="user",
            timestamp=datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
            features={"request_rate": float(event_number)},
        ),
        is_anomalous=label,
    )


def test_evaluation_reports_confusion_matrix_and_metrics() -> None:
    samples = [sample(1, False), sample(2, True), sample(3, False), sample(4, True)]

    result = evaluate_predictions(
        samples,
        lambda vector: vector.features["request_rate"] in {2.0, 3.0},
        estimator_name="test-detector",
    )

    assert result.sample_count == 4
    assert result.true_positives == 1
    assert result.true_negatives == 1
    assert result.false_positives == 1
    assert result.false_negatives == 1
    assert result.precision == 0.5
    assert result.recall == 0.5
    assert result.f1 == 0.5


def test_zero_division_metrics_are_defined_as_zero() -> None:
    result = evaluate_predictions(
        [sample(1, False)],
        lambda vector: False,
        estimator_name="always-benign",
    )

    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.f1 == 0.0
