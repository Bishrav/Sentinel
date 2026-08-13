"""Deterministic, baseline-relative anomaly scoring."""

from __future__ import annotations

from sentinel_ml.models import AnomalyScore, BehavioralFeatureVector, EntityBaseline, FeatureAnomaly


def score_vector(
    vector: BehavioralFeatureVector,
    baseline: EntityBaseline,
    *,
    threshold: float = 3.0,
    minimum_observations: int = 2,
) -> AnomalyScore:
    """Calculate an explainable max-absolute-z-score anomaly result."""

    if vector.entity_id != baseline.entity_id:
        raise ValueError("feature vector and baseline belong to different entities")
    if threshold <= 0:
        raise ValueError("threshold must be positive")
    anomalies: list[FeatureAnomaly] = []
    for feature_name in sorted(vector.features):
        if feature_name not in baseline.means:
            continue
        observed = vector.features[feature_name]
        mean = baseline.means[feature_name]
        standard_deviation = baseline.standard_deviations.get(feature_name, 0.0)
        z_score = 0.0 if standard_deviation == 0 else (observed - mean) / standard_deviation
        anomalies.append(
            FeatureAnomaly(
                feature_name=feature_name,
                observed_value=observed,
                baseline_mean=mean,
                baseline_standard_deviation=standard_deviation,
                z_score=z_score,
            )
        )
    ranked = sorted(anomalies, key=lambda item: (-abs(item.z_score), item.feature_name))
    score = max((abs(item.z_score) for item in ranked), default=0.0)
    contributors = tuple(item.feature_name for item in ranked[:3])
    return AnomalyScore(
        event_id=vector.event_id,
        entity_id=vector.entity_id,
        score=score,
        is_anomalous=baseline.observation_count >= minimum_observations and score >= threshold,
        features=tuple(ranked),
        top_contributors=contributors,
        baseline_observation_count=baseline.observation_count,
    )
