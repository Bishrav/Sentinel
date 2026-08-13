"""Replay-safe online entity baseline statistics."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from .models import BehavioralFeatureVector, EntityBaseline


class _RunningFeature:
    def __init__(self) -> None:
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta_after = value - self.mean
        self.m2 += delta * delta_after

    @property
    def standard_deviation(self) -> float:
        if self.count < 2:
            return 0.0
        return (self.m2 / self.count) ** 0.5


class OnlineBaselineStore:
    """Maintain per-entity population statistics with event replay protection."""

    def __init__(self) -> None:
        self._features: dict[str, dict[str, _RunningFeature]] = {}
        self._entity_types: dict[str, str] = {}
        self._updated_at: dict[str, datetime] = {}
        self._processed_events: set[str] = set()

    def update(self, vector: BehavioralFeatureVector) -> bool:
        """Apply one vector; return ``False`` when its event was already seen."""

        event_key = str(vector.event_id)
        if event_key in self._processed_events:
            return False
        feature_state = self._features.setdefault(vector.entity_id, {})
        for name, value in vector.features.items():
            feature_state.setdefault(name, _RunningFeature()).update(value)
        self._entity_types[vector.entity_id] = vector.entity_type
        self._updated_at[vector.entity_id] = vector.timestamp
        self._processed_events.add(event_key)
        return True

    def update_many(self, vectors: Iterable[BehavioralFeatureVector]) -> int:
        """Apply vectors in order and return the number of new observations."""

        return sum(self.update(vector) for vector in vectors)

    def get(self, entity_id: str) -> EntityBaseline | None:
        """Return the current immutable baseline for one entity."""

        feature_state = self._features.get(entity_id)
        if feature_state is None:
            return None
        count = next(iter(feature_state.values())).count if feature_state else 0
        return EntityBaseline(
            entity_id=entity_id,
            entity_type=self._entity_types[entity_id],  # type: ignore[arg-type]
            observation_count=count,
            feature_names=tuple(sorted(feature_state)),
            means={name: state.mean for name, state in sorted(feature_state.items())},
            standard_deviations={
                name: state.standard_deviation for name, state in sorted(feature_state.items())
            },
            updated_at=self._updated_at[entity_id],
        )

    def all(self) -> tuple[EntityBaseline, ...]:
        """Return all baselines ordered by entity ID."""

        baselines = [self.get(entity_id) for entity_id in sorted(self._features)]
        return tuple(baseline for baseline in baselines if baseline is not None)
