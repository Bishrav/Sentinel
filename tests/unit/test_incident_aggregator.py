from sentinel_ingestion.normalizer import normalize

from sentinel_detection.aggregator import IncidentAggregator
from sentinel_detection.engine import RuleEngine
from sentinel_detection.loader import load_rules


def make_event(event_id: str, timestamp: str, **overrides: object):
    raw = {
        "event_id": event_id,
        "timestamp": timestamp,
        "actor_id": "user-42",
        "actor_type": "user",
        "action": "login",
        "resource": "identity-provider",
        "result": "failure",
    }
    raw.update(overrides)
    return normalize(raw, source="test")


def test_aggregation_is_idempotent_and_preserves_evidence() -> None:
    engine = RuleEngine(load_rules("config/rules/default.json"))
    aggregator = IncidentAggregator()
    first_event = make_event("12345678-1234-4234-8234-123456789012", "2026-08-12T12:00:00Z")
    second_event = make_event("12345678-1234-4234-8234-123456789013", "2026-08-12T12:01:00Z")

    first = aggregator.add(first_event, engine.evaluate(first_event))
    duplicate = aggregator.add(first_event, engine.evaluate(first_event))
    second = aggregator.add(second_event, engine.evaluate(second_event))

    assert len(first) == 1
    assert duplicate == ()
    assert len(second) == 1
    incident = aggregator.all()[0]
    assert incident.match_count == 2
    assert len(incident.event_ids) == 2
    assert incident.first_seen.isoformat().startswith("2026-08-12T12:00")
    assert incident.last_seen.isoformat().startswith("2026-08-12T12:01")
    assert incident.evidence[0] == {"action": "login", "result": "failure"}


def test_incident_severity_escalates_for_same_fingerprint() -> None:
    engine = RuleEngine(load_rules("config/rules/default.json"))
    aggregator = IncidentAggregator()
    failed_login = make_event("12345678-1234-4234-8234-123456789012", "2026-08-12T12:00:00Z")
    privilege_change = make_event(
        "12345678-1234-4234-8234-123456789013",
        "2026-08-12T12:01:00Z",
        action="role_change",
        result="success",
        resource="identity-provider",
    )

    aggregator.add(failed_login, engine.evaluate(failed_login))
    aggregator.add(privilege_change, engine.evaluate(privilege_change))

    incidents = aggregator.all()
    assert len(incidents) == 1
    assert incidents[0].severity == "high"
    assert incidents[0].match_count == 2
