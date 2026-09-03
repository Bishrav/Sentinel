from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sentinel_detection.models import RuleCondition
from sentinel_ingestion.models import EventResult, SecurityEvent
from sentinel_sequence.matcher import FiniteStateSequenceMatcher
from sentinel_sequence.models import SequenceSignature, SequenceStep


def _event(
    *, actor_id: str = "alice", result: EventResult = "failure", at: datetime | None = None
) -> SecurityEvent:
    return SecurityEvent(
        event_id=uuid4(),
        timestamp=at or datetime(2026, 1, 1, tzinfo=UTC),
        actor_id=actor_id,
        actor_type="user",
        action="login",
        resource="console",
        result=result,
        severity="medium",
        source="test",
    )


def _signature(window_seconds: int = 300) -> SequenceSignature:
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
        window_seconds=window_seconds,
        severity="high",
    )


def test_matcher_emits_ordered_match_with_evidence() -> None:
    first = _event()
    second = _event(result="success", at=first.timestamp + timedelta(seconds=30))
    matcher = FiniteStateSequenceMatcher((_signature(),))

    assert matcher.process(first) == ()
    matches = matcher.process(second)

    assert len(matches) == 1
    assert matches[0].actor_id == "alice"
    assert matches[0].event_ids == (first.event_id, second.event_id)
    assert [item["step_id"] for item in matches[0].evidence] == [
        "failed_login",
        "successful_login",
    ]


def test_matcher_isolates_actors_and_rejects_wrong_order() -> None:
    first = _event()
    other_actor = _event(
        actor_id="bob", result="success", at=first.timestamp + timedelta(seconds=1)
    )
    wrong_order = _event(result="success", at=first.timestamp + timedelta(seconds=2))
    matcher = FiniteStateSequenceMatcher((_signature(),))

    assert matcher.process(first) == ()
    assert matcher.process(other_actor) == ()
    assert len(matcher.process(wrong_order)) == 1


def test_matcher_expires_partial_state_and_deduplicates_replay() -> None:
    first = _event()
    second = _event(result="success", at=first.timestamp + timedelta(seconds=301))
    matcher = FiniteStateSequenceMatcher((_signature(window_seconds=300),))

    assert matcher.process(first) == ()
    assert matcher.process(first) == ()
    assert matcher.process(second) == ()


def test_matcher_does_not_start_disabled_signatures() -> None:
    signature = _signature().model_copy(update={"enabled": False})
    matcher = FiniteStateSequenceMatcher((signature,))
    assert matcher.process(_event()) == ()


def test_matcher_accepts_late_event_inside_allowed_lateness() -> None:
    first = _event(at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC))
    clock = _event(
        actor_id="bob",
        result="failure",
        at=first.timestamp + timedelta(seconds=100),
    )
    late_success = _event(result="success", at=first.timestamp + timedelta(seconds=30))
    signature = _signature().model_copy(update={"allowed_lateness_seconds": 80})
    matcher = FiniteStateSequenceMatcher((signature,))

    matcher.process(first)
    matcher.process(clock)
    assert len(matcher.process(late_success)) == 1


def test_matcher_rejects_event_beyond_watermark_and_bounds_state() -> None:
    signature = _signature().model_copy(update={"allowed_lateness_seconds": 0})
    matcher = FiniteStateSequenceMatcher((signature,), max_active_per_actor=2)
    base = datetime(2026, 1, 1, tzinfo=UTC)

    matcher.process(_event(at=base))
    matcher.process(_event(at=base + timedelta(seconds=1)))
    matcher.process(_event(at=base + timedelta(seconds=2)))
    assert matcher.active_state_count == 2
    assert matcher.watermark == base + timedelta(seconds=2)

    too_late = _event(result="success", at=base - timedelta(seconds=1))
    assert matcher.process(too_late) == ()
