from pathlib import Path

from sentinel_ingestion.collectors import JsonLinesCollector
from sentinel_ingestion.pipeline import ingest
from sentinel_ingestion.transport import InMemoryEventPublisher


def test_jsonl_replay_uses_the_same_ingestion_pipeline() -> None:
    collector = JsonLinesCollector(Path("tests/fixtures/auth_events.jsonl"))
    publisher = InMemoryEventPublisher()

    events = ingest(collector.collect(), source="auth-fixture", publisher=publisher)

    assert len(events) == 3
    assert list(publisher.events()) == events
    assert events[0].attributes["derived"]["is_authentication"] is True
    assert events[1].severity == "high"
    assert events[2].attributes["bytes"] == 52428800
