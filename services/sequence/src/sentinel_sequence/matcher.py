"""Deterministic finite-state matching for ordered security event sequences."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from time import perf_counter
from uuid import UUID

from sentinel_detection.engine import RuleEngine
from sentinel_detection.models import DetectionRule
from sentinel_ingestion.models import SecurityEvent

from .metrics import SequenceMetrics, default_metrics
from .models import SequenceMatch, SequenceSignature, SequenceStep


@dataclass(frozen=True)
class _PartialMatch:
    actor_id: str
    event_ids: tuple[UUID, ...]
    evidence: tuple[dict[str, object], ...]
    started_at: datetime
    next_step_index: int


class FiniteStateSequenceMatcher:
    """Match signatures with event-time lateness and bounded in-memory state."""

    def __init__(
        self,
        signatures: tuple[SequenceSignature, ...],
        *,
        max_active_per_actor: int = 1000,
        max_processed_event_ids: int = 10_000,
        metrics: SequenceMetrics | None = None,
    ) -> None:
        if max_active_per_actor < 1 or max_processed_event_ids < 1:
            raise ValueError("state bounds must be positive")
        self._signatures = tuple(signature for signature in signatures if signature.enabled)
        self._max_active_per_actor = max_active_per_actor
        self._max_processed_event_ids = max_processed_event_ids
        self.metrics = metrics or default_metrics
        self._partials: dict[tuple[str, str], list[_PartialMatch]] = {}
        self._processed_event_ids: set[UUID] = set()
        self._processed_event_order: deque[UUID] = deque()
        self._max_seen_at: datetime | None = None
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
            self.metrics.observe_duplicate()
            return ()
        started = perf_counter()
        self._processed_event_ids.add(event.event_id)
        self._processed_event_order.append(event.event_id)
        if len(self._processed_event_order) > self._max_processed_event_ids:
            self._processed_event_ids.remove(self._processed_event_order.popleft())
        if self._max_seen_at is None or event.timestamp > self._max_seen_at:
            self._max_seen_at = event.timestamp

        evicted = self._evict_expired()

        matches: list[SequenceMatch] = []
        late_for_signature = False
        for signature in self._signatures:
            watermark = self._watermark(signature)
            if event.timestamp < watermark:
                late_for_signature = True
                continue
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

        self._enforce_actor_bound(event.actor_id)
        self.metrics.observe(
            latency_ms=(perf_counter() - started) * 1000,
            completed=len(matches),
            late=late_for_signature,
            evicted=evicted,
            active_states=self.active_state_count,
        )

        return tuple(matches)

    @property
    def watermark(self) -> datetime | None:
        """Return the highest observed event time, before signature lateness offsets."""

        return self._max_seen_at

    @property
    def active_state_count(self) -> int:
        """Return the number of currently retained partial sequence matches."""

        return sum(len(partials) for partials in self._partials.values())

    def _watermark(self, signature: SequenceSignature) -> datetime:
        if self._max_seen_at is None:
            raise RuntimeError("watermark requested before any event")
        return self._max_seen_at - timedelta(seconds=signature.allowed_lateness_seconds)

    def _evict_expired(self) -> int:
        if self._max_seen_at is None:
            return 0
        evicted = 0
        for signature in self._signatures:
            watermark = self._watermark(signature)
            for key in [key for key in self._partials if key[0] == signature.signature_id]:
                retained = [
                    partial
                    for partial in self._partials[key]
                    if watermark - partial.started_at <= timedelta(seconds=signature.window_seconds)
                ]
                evicted += len(self._partials[key]) - len(retained)
                if retained:
                    self._partials[key] = retained
                else:
                    self._partials.pop(key, None)
        return evicted

    def _enforce_actor_bound(self, actor_id: str) -> None:
        entries = [
            (key, partial)
            for key, partials in self._partials.items()
            if key[1] == actor_id
            for partial in partials
        ]
        if len(entries) <= self._max_active_per_actor:
            return
        keep = {
            id(partial)
            for _, partial in sorted(entries, key=lambda item: item[1].started_at, reverse=True)[
                : self._max_active_per_actor
            ]
        }
        for key, partials in list(self._partials.items()):
            if key[1] != actor_id:
                continue
            retained = [partial for partial in partials if id(partial) in keep]
            if retained:
                self._partials[key] = retained
            else:
                self._partials.pop(key, None)

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
