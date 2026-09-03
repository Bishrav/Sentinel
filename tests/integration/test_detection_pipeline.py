from pathlib import Path

from sentinel_detection.engine import RuleEngine
from sentinel_detection.loader import load_rules
from sentinel_detection.pipeline import DetectionPipeline
from sentinel_ingestion.collectors import JsonLinesCollector
from sentinel_ingestion.enricher import enrich
from sentinel_ingestion.normalizer import normalize


def test_fixture_ingestion_produces_incidents_end_to_end() -> None:
    collector = JsonLinesCollector(Path("tests/fixtures/auth_events.jsonl"))
    pipeline = DetectionPipeline(RuleEngine(load_rules("config/rules/default.json")))
    events = [enrich(normalize(raw, source="auth-fixture")) for raw in collector.collect()]

    incidents = pipeline.process_many(events)

    assert len(incidents) == 2
    assert {incident.match_count for incident in incidents} == {1}
    assert {incident.severity for incident in incidents} == {"high"}
    assert {rule_id for incident in incidents for rule_id in incident.rule_ids} == {
        "privilege_change",
        "large_export",
    }
