"""Comparison orchestration for baseline and trained anomaly detectors."""

from __future__ import annotations

from collections.abc import Sequence

from .evaluation import Predictor, evaluate_predictions
from .models import (
    BehavioralFeatureVector,
    EntityBaseline,
    LabeledFeatureVector,
    ModelComparison,
)
from .scoring import score_vector


def compare_baseline(
    samples: Sequence[LabeledFeatureVector],
    baseline: EntityBaseline,
    *,
    threshold: float = 3.0,
) -> ModelComparison:
    """Evaluate the statistical z-score detector on labeled samples."""

    def predictor(vector: BehavioralFeatureVector) -> bool:
        return score_vector(vector, baseline, threshold=threshold).is_anomalous

    result = evaluate_predictions(samples, predictor, estimator_name="z_score_baseline")
    return ModelComparison(results=(result,), best_by_f1=result.estimator_name)


def compare_detectors(
    samples: Sequence[LabeledFeatureVector],
    predictors: Sequence[tuple[str, Predictor]],
) -> ModelComparison:
    """Evaluate named predictors and select the first highest-F1 model."""

    results = tuple(
        evaluate_predictions(samples, predictor, estimator_name=name)
        for name, predictor in predictors
    )
    best = max(
        results,
        key=lambda result: (result.f1, result.recall, result.precision),
        default=None,
    )
    return ModelComparison(
        results=results,
        best_by_f1=best.estimator_name if best is not None else None,
    )
