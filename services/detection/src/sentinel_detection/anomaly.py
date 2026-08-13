"""Adapters that turn ML anomaly scores into detection evidence."""

from __future__ import annotations

from sentinel_ingestion.models import SecurityEvent
from sentinel_ml.models import AnomalyScore

from .models import RuleMatch, Severity


def anomaly_to_match(event: SecurityEvent, score: AnomalyScore) -> RuleMatch | None:
    """Convert an anomalous ML result into an incident-compatible match."""

    if score.event_id != event.event_id or score.entity_id != event.actor_id:
        raise ValueError("anomaly score does not belong to the supplied event")
    if not score.is_anomalous:
        return None
    severity: Severity = "critical" if score.score >= 10 else "high"
    evidence = {
        "detector": "behavioral_baseline",
        "anomaly_score": score.score,
        "baseline_observation_count": score.baseline_observation_count,
        "top_contributors": list(score.top_contributors),
        "feature_scores": [feature.model_dump(mode="json") for feature in score.features],
    }
    return RuleMatch(
        rule_id="behavioral_anomaly",
        rule_version=1,
        event_id=event.event_id,
        matched_at=event.timestamp,
        severity=severity,
        evidence=evidence,
        fingerprint=f"{event.actor_id}:{event.resource}",
    )
