"""Normalize, enrich, and publish a stream of source records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .enricher import enrich
from .models import SecurityEvent
from .normalizer import normalize
from .transport import EventPublisher


def ingest(
    records: Iterable[Mapping[str, Any]],
    *,
    source: str,
    publisher: EventPublisher,
) -> list[SecurityEvent]:
    """Process records in order and return the events accepted by the publisher."""

    events: list[SecurityEvent] = []
    for raw in records:
        event = enrich(normalize(raw, source=source))
        publisher.publish(event)
        events.append(event)
    return events
