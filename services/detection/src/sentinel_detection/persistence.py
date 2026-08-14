"""Persistence boundary for replay-safe incident projections."""

from collections.abc import Iterable
from typing import Protocol

from .models import Incident


class IncidentStore(Protocol):
    """Minimal durable-store interface used by the incident aggregator."""

    def upsert(self, incident: Incident) -> None:
        """Persist one complete incident projection."""

    def get(self, fingerprint: str) -> Incident | None:
        """Load one incident by deterministic fingerprint."""

    def all(self) -> Iterable[Incident]:
        """Load all persisted incidents."""
