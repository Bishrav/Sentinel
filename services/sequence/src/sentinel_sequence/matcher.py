"""Deterministic finite-state matching for ordered security event sequences."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sentinel_detection.engine import RuleEngine
from sentinel_detection.models import DetectionRule
from sentinel_ingestion.models import SecurityEvent

from .models import SequenceMatch, SequenceSignature, SequenceStep


@dataclass(frozen=True)
class _PartialMatch:
    actor_id: str
    event_ids: tuple[UUID, ...]
    evidence: tuple[dict[str, object], ...]
    started_at: datetime
    next_step_index: int


class FiniteStateSequenceMatcher:
    """Match enabled signatures while keeping state isolated per actor."""

    def __init__(self, signatures: tuple[SequenceSignature, ...]) -> None:
        self._signatures = tuple(signature for signature in signatures if signature.enabled)
        self._partials: dict[tuple[str, str], list[_PartialMatch]] = {}
        self._processed_event_ids: set[UUID] = set()
        self._step_engines = {
            (signature.signature_id, step.step_id): RuleEngine(
                [
                    DetectionRule(
                        rule_id="sequence_step",
                        name="Sequence step",
                        description="Internal sequence step predicate",
                        severity=signature.severity,
                        conditions=list(step.conditions),
                    )
                ]
            )
            for signature in self._signatures
            for step in signature.steps
        }

    def process(self, event: SecurityEvent) -> tuple[SequenceMatch, ...]:
        """Consume one event and return any sequences completed by it."""

        if event.event_id in self._processed_event_ids:
            return ()
        self._processed_event_ids.add(event.event_id)

        matches: list[SequenceMatch] = []
        for signature in self._signatures:
            key = (signature.signature_id, event.actor_id)
            active = self._partials.get(key, [])
            retained: list[_PartialMatch] = []
            for partial in active:
                elapsed = (event.timestamp - partial.started_at).total_seconds()
                if elapsed > signature.window_seconds:
                    continue
                step = signature.steps[partial.next_step_index]
                if not self._matches_step(signature, step, event):
                    retained.append(partial)
                    continue

                event_ids = (*partial.event_ids, event.event_id)
                evidence = (*partial.evidence, self._evidence(step, event))
                if partial.next_step_index == len(signature.steps) - 1:
                    matches.append(
                        SequenceMatch(
                            signature_id=signature.signature_id,
                            signature_version=signature.version,
                            actor_id=event.actor_id,
                            event_ids=event_ids,
                            started_at=partial.started_at,
                            completed_at=event.timestamp,
                            evidence=evidence,
                            severity=signature.severity,
                        )
                    )
                else:
                    retained.append(
                        _PartialMatch(
                            actor_id=partial.actor_id,
                            event_ids=event_ids,
                            evidence=evidence,
                            started_at=partial.started_at,
                            next_step_index=partial.next_step_index + 1,
                        )
                    )

            if self._matches_step(signature, signature.steps[0], event):
                retained.append(
                    _PartialMatch(
                        actor_id=event.actor_id,
                        event_ids=(event.event_id,),
                        evidence=(self._evidence(signature.steps[0], event),),
                        started_at=event.timestamp,
                        next_step_index=1,
                    )
                )
            if retained:
                self._partials[key] = retained
            else:
                self._partials.pop(key, None)

        return tuple(matches)

    def _matches_step(
        self, signature: SequenceSignature, step: SequenceStep, event: SecurityEvent
    ) -> bool:
        return bool(self._step_engines[(signature.signature_id, step.step_id)].evaluate(event))

    @staticmethod
    def _evidence(step: SequenceStep, event: SecurityEvent) -> dict[str, object]:
        return {
            "step_id": step.step_id,
            "event_id": str(event.event_id),
            "timestamp": event.timestamp.isoformat(),
            "action": event.action,
            "resource": event.resource,
            "result": event.result,
        }
