from datetime import UTC, datetime
from uuid import uuid4

from sentinel_detection.aggregator import IncidentAggregator
from sentinel_detection.models import RuleMatch
from sentinel_ingestion.models import SecurityEvent
from sentinel_risk import RiskInput, score_risk


def test_risk_audit_is_attached_to_matching_incident() -> None:
    aggregator = IncidentAggregator()
    event = SecurityEvent(
        event_id=uuid4(),
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        actor_id="alice",
        actor_type="user",
        action="login",
        resource="console",
        result="failure",
        severity="high",
        source="risk-test",
    )
    match = RuleMatch(
        rule_id="risk_signal",
        rule_version=1,
        event_id=event.event_id,
        matched_at=event.timestamp,
        severity="high",
        evidence={"action": "login"},
        fingerprint="alice:console",
    )
    incident = aggregator.add(event, (match,))[0]
    audit = score_risk(
        RiskInput(
            incident_id=incident.incident_id,
            severity="high",
            anomaly_score=70,
            graph_risk_score=60,
            evidence_count=2,
        )
    )

    updated = aggregator.apply_risk(audit)

    assert updated is not None
    assert updated.risk_score == audit.assessment.score
    assert updated.risk_band == audit.assessment.band
    assert updated.risk_audit == audit
