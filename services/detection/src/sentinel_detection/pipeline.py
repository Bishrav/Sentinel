"""End-to-end event-to-incident detection pipeline."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from sentinel_ingestion.models import SecurityEvent
from sentinel_ml.models import AnomalyScore

from .anomaly import anomaly_to_match
from .aggregator import IncidentAggregator
from .engine import RuleEngine
from .models import Incident


class DetectionPipeline:
    """Evaluate events and retain the current incident projection."""

    def __init__(
        self,
        engine: RuleEngine,
        aggregator: IncidentAggregator | None = None,
        anomaly_scorer: Callable[[SecurityEvent], AnomalyScore | None] | None = None,
    ) -> None:
        self.engine = engine
        self.aggregator = aggregator or IncidentAggregator()
        self.anomaly_scorer = anomaly_scorer

    def process(self, event: SecurityEvent) -> tuple[Incident, ...]:
        """Evaluate one event and return incidents changed by that event."""

        matches = self.engine.evaluate(event)
        if self.anomaly_scorer is not None:
            anomaly_score = self.anomaly_scorer(event)
            if anomaly_score is not None:
                anomaly_match = anomaly_to_match(event, anomaly_score)
                if anomaly_match is not None:
                    matches.append(anomaly_match)
        return self.aggregator.add(event, matches)

    def process_many(self, events: Iterable[SecurityEvent]) -> tuple[Incident, ...]:
        """Process events in arrival order and return the final incident projection."""

        for event in events:
            self.process(event)
        return self.aggregator.all()

    def incidents(self) -> tuple[Incident, ...]:
        """Return all currently aggregated incidents."""

        return self.aggregator.all()
