from uuid import uuid4

from sentinel_risk import RiskInput, score_risk


def test_risk_score_preserves_weighted_components_and_audit_inputs() -> None:
    inputs = RiskInput(
        incident_id=uuid4(),
        severity="high",
        anomaly_score=80,
        sequence_confidence=0.9,
        graph_risk_score=70,
        evidence_count=4,
    )

    record = score_risk(inputs)

    assert record.inputs == inputs
    assert record.assessment.incident_id == inputs.incident_id
    assert record.assessment.formula_version == "1.0"
    assert record.assessment.score == 76.5
    assert record.assessment.band == "high"
    assert record.assessment.components["sequence"] == 18.0


def test_risk_score_is_bounded_and_replayable() -> None:
    inputs = RiskInput(
        incident_id=uuid4(),
        severity="critical",
        anomaly_score=100,
        sequence_confidence=1,
        graph_risk_score=100,
        evidence_count=1000,
    )

    first = score_risk(inputs)
    second = score_risk(inputs)

    assert first.assessment.score == 100
    assert first.assessment.band == "critical"
    assert first.assessment == second.assessment
