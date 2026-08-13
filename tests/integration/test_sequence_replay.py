from pathlib import Path

from sentinel_detection.pipeline import build_pipeline
from sentinel_ingestion.collectors import JsonLinesCollector
from sentinel_ingestion.enricher import enrich
from sentinel_ingestion.normalizer import normalize


def _replay() -> list[dict[str, object]]:
    events = [
        enrich(normalize(raw, source="sequence-fixture"))
        for raw in JsonLinesCollector(Path("tests/fixtures/sequence_attack.jsonl")).collect()
    ]
    pipeline = build_pipeline("config/rules/default.json", "config/sequences/default.json")
    pipeline.process_many(events)
    return [incident.model_dump(mode="json") for incident in pipeline.incidents()]


def test_sequence_replay_produces_identical_incident_projection() -> None:
    first = _replay()
    second = _replay()

    assert first == second
    sequence_incidents = [
        incident for incident in first if "sequence:credential_attack:v1" in incident["rule_ids"]
    ]
    assert len(sequence_incidents) == 1
    assert sequence_incidents[0]["event_ids"] == [
        "12345678-1234-4234-8234-123456789101",
        "12345678-1234-4234-8234-123456789102",
        "12345678-1234-4234-8234-123456789103",
    ]


def test_replaying_same_events_does_not_increase_sequence_incident_count() -> None:
    events = [
        enrich(normalize(raw, source="sequence-fixture"))
        for raw in JsonLinesCollector(Path("tests/fixtures/sequence_attack.jsonl")).collect()
    ]
    pipeline = build_pipeline("config/rules/default.json", "config/sequences/default.json")
    pipeline.process_many(events)
    before = [incident.model_dump(mode="json") for incident in pipeline.incidents()]
    pipeline.process_many(events)
    after = [incident.model_dump(mode="json") for incident in pipeline.incidents()]

    assert after == before
