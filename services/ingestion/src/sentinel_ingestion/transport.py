"""Event transport interfaces and implementations."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Protocol

from .models import SecurityEvent


class EventPublisher(Protocol):
    """Destination contract used by the ingestion pipeline."""

    def publish(self, event: SecurityEvent) -> None:
        """Publish one normalized event."""


class InMemoryEventPublisher:
    """Deterministic publisher for unit tests and local pipeline inspection."""

    def __init__(self) -> None:
        self._events: list[SecurityEvent] = []

    def publish(self, event: SecurityEvent) -> None:
        self._events.append(event)

    def events(self) -> Iterator[SecurityEvent]:
        yield from self._events


class KafkaEventPublisher:
    """Publish canonical events to a Kafka-compatible topic."""

    def __init__(self, *, bootstrap_servers: str, topic: str) -> None:
        from confluent_kafka import Producer  # type: ignore[import-untyped]

        self.topic = topic
        self._producer = Producer({"bootstrap.servers": bootstrap_servers})

    def publish(self, event: SecurityEvent) -> None:
        self._producer.produce(
            self.topic,
            key=str(event.event_id),
            value=json.dumps(event.model_dump(mode="json"), separators=(",", ":")),
        )
        self._producer.poll(0)

    def flush(self, timeout: float = 10.0) -> int:
        """Wait for buffered messages and return the number still queued."""

        return self._producer.flush(timeout)  # type: ignore[no-any-return]
