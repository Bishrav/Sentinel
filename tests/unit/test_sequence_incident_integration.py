from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sentinel_detection.aggregator import IncidentAggregator
from sentinel_detection.engine import RuleEngine
from sentinel_detection.models import RuleCondition
from sentinel_detection.pipeline import DetectionPipeline
from sentinel_ingestion.models import SecurityEvent
from sentinel_sequence.matcher import FiniteStateSequenceMatcher
from sentinel_sequence.models import SequenceSignature, SequenceStep


def _event(result: str, at: datetime) -> SecurityEvent:
    return SecurityEvent(
        event_id=uuid4(),
        timestamp=at,
        actor_id="alice",
        actor_type="user",
        action="login",
        resource="console",
        result=result,  # type: ignore[arg-type]
        severity="medium",
        source="test",
    )


def _signature() -> SequenceSignature:
    return SequenceSignature(
        signature_id="credential_attack",
        name="Credential attack",
        description="Failed login followed by success.",
        steps=(
            SequenceStep(
                step_id="failed_login",
                conditions=(RuleCondition(field="result", operator="eq", value="failure"),),
            ),
            SequenceStep(
                step_id="successful_login",
                conditions=(RuleCondition(field="result", operator="eq", value="success"),),
            ),
        ),
        window_seconds=300,
        severity="high",
    )


def test_pipeline_projects_sequence_match_as_incident() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    matcher = FiniteStateSequenceMatcher((_signature(),))
    pipeline = DetectionPipeline(RuleEngine([]), sequence_matcher=matcher)
    first = _event("failure", start)
    second = _event("success", start + timedelta(seconds=30))

    assert pipeline.process(first) == ()
    changed = pipeline.process(second)

    assert len(changed) == 1
    incident = pipeline.incidents()[0]
    assert incident.fingerprint == "sequence:credential_attack:alice"
    assert incident.rule_ids == frozenset({"sequence:credential_attack:v1"})
    assert incident.match_count == 1
    assert incident.event_ids == (first.event_id, second.event_id)
    assert {item["step_id"] for item in incident.evidence} == {
        "failed_login",
        "successful_login",
    }


def test_sequence_incident_projection_is_replay_safe() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    signature = _signature()
    first = _event("failure", start)
    second = _event("success", start + timedelta(seconds=30))
    matcher = FiniteStateSequenceMatcher((signature,))
    aggregator = IncidentAggregator()
    sequence_match = matcher.process(first) + matcher.process(second)
    assert len(sequence_match) == 1

    assert len(aggregator.add_sequences(sequence_match)) == 1
    assert aggregator.add_sequences(sequence_match) == ()
    assert aggregator.all()[0].match_count == 1
