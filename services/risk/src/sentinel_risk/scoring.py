"""Deterministic evidence-weighted risk scoring."""

from datetime import UTC, datetime

from .models import RiskAssessment, RiskAuditRecord, RiskBand, RiskInput

_SEVERITY_SCORE = {"low": 25.0, "medium": 50.0, "high": 75.0, "critical": 100.0}
_WEIGHTS = {
    "severity": 0.30,
    "anomaly": 0.25,
    "sequence": 0.20,
    "graph": 0.20,
    "evidence": 0.05,
}


def _band(score: float) -> RiskBand:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    return "low"


def score_risk(inputs: RiskInput) -> RiskAuditRecord:
    """Calculate a bounded score and retain the full replayable audit record."""

    components = {
        "severity": _SEVERITY_SCORE[inputs.severity] * _WEIGHTS["severity"],
        "anomaly": inputs.anomaly_score * _WEIGHTS["anomaly"],
        "sequence": inputs.sequence_confidence * 100 * _WEIGHTS["sequence"],
        "graph": inputs.graph_risk_score * _WEIGHTS["graph"],
        "evidence": min(100.0, inputs.evidence_count * 10) * _WEIGHTS["evidence"],
    }
    score = round(min(100.0, sum(components.values())), 4)
    assessment = RiskAssessment(
        incident_id=inputs.incident_id,
        score=score,
        band=_band(score),
        components=components,
    )
    return RiskAuditRecord(
        recorded_at=datetime.now(UTC),
        inputs=inputs,
        assessment=assessment,
    )
