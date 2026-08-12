"""End-to-end event-to-incident detection pipeline."""

from __future__ import annotations

from collections.abc import Iterable

from sentinel_ingestion.models import SecurityEvent

from .aggregator import IncidentAggregator
from .engine import RuleEngine
from .models import Incident


class DetectionPipeline:
    """Evaluate events and retain the current incident projection."""

    def __init__(self, engine: RuleEngine, aggregator: IncidentAggregator | None = None) -> None:
        self.engine = engine
        self.aggregator = aggregator or IncidentAggregator()

    def process(self, event: SecurityEvent) -> tuple[Incident, ...]:
        """Evaluate one event and return incidents changed by that event."""

        return self.aggregator.add(event, self.engine.evaluate(event))

    def process_many(self, events: Iterable[SecurityEvent]) -> tuple[Incident, ...]:
        """Process events in arrival order and return the final incident projection."""

        for event in events:
            self.process(event)
        return self.aggregator.all()

    def incidents(self) -> tuple[Incident, ...]:
        """Return all currently aggregated incidents."""

        return self.aggregator.all()
