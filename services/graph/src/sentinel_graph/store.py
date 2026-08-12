"""Idempotent in-memory graph store for local development and tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from sentinel_ingestion.models import SecurityEvent

from .models import GraphEdge, GraphNode, ThreatGraphSnapshot
from .projection import project_event


class InMemoryGraphStore:
    """Upsert graph projections while preserving event-level idempotency."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._processed_events: set[str] = set()

    def ingest(self, event: SecurityEvent) -> bool:
        """Ingest one event; return ``False`` when it was already replayed."""

        event_key = str(event.event_id)
        if event_key in self._processed_events:
            return False
        nodes, edges = project_event(event)
        self._nodes.update({node.node_id: node for node in nodes})
        self._edges.update({edge.edge_id: edge for edge in edges})
        self._processed_events.add(event_key)
        return True

    def snapshot(self) -> ThreatGraphSnapshot:
        """Return a stable snapshot ordered by graph identifiers."""

        node_ids = ":".join(sorted(self._nodes))
        snapshot_id = uuid5(NAMESPACE_URL, f"sentinel:graph:{node_ids}")
        return ThreatGraphSnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(timezone.utc),
            nodes=tuple(self._nodes[key] for key in sorted(self._nodes)),
            edges=tuple(self._edges[key] for key in sorted(self._edges)),
        )

    def node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def edge(self, edge_id: str) -> GraphEdge | None:
        return self._edges.get(edge_id)
