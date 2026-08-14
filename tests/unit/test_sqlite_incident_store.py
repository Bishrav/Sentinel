from datetime import datetime, timezone
from uuid import uuid4

from sentinel_detection.aggregator import IncidentAggregator
from sentinel_detection.models import RuleMatch
from sentinel_ingestion.models import SecurityEvent
from sentinel_storage import SqliteIncidentStore


def _incident_input() -> tuple[SecurityEvent, RuleMatch]:
    event = SecurityEvent(
        event_id=uuid4(),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        actor_id="persistent-user",
        actor_type="user",
        action="login",
        resource="console",
        result="failure",
        severity="high",
        source="persistence-test",
    )
    return event, RuleMatch(
        rule_id="persistent_signal",
        rule_version=1,
        event_id=event.event_id,
        matched_at=event.timestamp,
        severity="high",
        evidence={"action": "login"},
        fingerprint="persistent-user:console",
    )


def test_sqlite_store_rehydrates_incident_across_aggregators(tmp_path) -> None:
    store = SqliteIncidentStore(tmp_path / "sentinel.db")
    event, match = _incident_input()
    created = IncidentAggregator(store=store).add(event, (match,))[0]

    rehydrated = IncidentAggregator(store=store).get(created.fingerprint)

    assert rehydrated == created
    assert tuple(store.all()) == (created,)
    store.close()
