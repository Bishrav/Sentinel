"""Reproducible evaluation utilities for anomaly detectors."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from .models import BehavioralFeatureVector, EvaluationMetrics, LabeledFeatureVector

Predictor = Callable[[BehavioralFeatureVector], bool]


def evaluate_predictions(
    samples: Sequence[LabeledFeatureVector],
    predictor: Predictor,
    *,
    estimator_name: str,
) -> EvaluationMetrics:
    """Calculate binary metrics from fixed labels and a predictor."""

    counts = {"tp": 0, "tn": 0, "fp": 0, "fn": 0}
    for sample in samples:
        predicted = predictor(sample.vector)
        if predicted and sample.is_anomalous:
            counts["tp"] += 1
        elif not predicted and not sample.is_anomalous:
            counts["tn"] += 1
        elif predicted:
            counts["fp"] += 1
        else:
            counts["fn"] += 1
    precision = _ratio(counts["tp"], counts["tp"] + counts["fp"])
    recall = _ratio(counts["tp"], counts["tp"] + counts["fn"])
    f1 = _ratio(2 * precision * recall, precision + recall)
    return EvaluationMetrics(
        estimator_name=estimator_name,
        sample_count=len(samples),
        true_positives=counts["tp"],
        true_negatives=counts["tn"],
        false_positives=counts["fp"],
        false_negatives=counts["fn"],
        precision=precision,
        recall=recall,
        f1=f1,
    )


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
