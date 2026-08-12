"""Deterministic weighted shortest-path queries."""

from __future__ import annotations

import heapq
from collections.abc import Iterable

from .models import EdgeType, ShortestPathResult, ThreatGraphSnapshot


def _cost(confidence: float) -> float:
    """Translate confidence into a positive traversal cost."""

    return 1.0 / max(confidence, 0.01)


def shortest_path(
    snapshot: ThreatGraphSnapshot,
    source_node_id: str,
    target_node_id: str,
    *,
    edge_types: Iterable[EdgeType] | None = None,
) -> ShortestPathResult | None:
    """Find the least-cost directed path using Dijkstra's algorithm.

    A confidence of ``1.0`` costs one hop. Lower-confidence relationships cost
    more, so the result prefers routes supported by stronger evidence. Missing
    nodes raise ``ValueError``; valid but disconnected nodes return ``None``.
    """

    node_ids = {node.node_id for node in snapshot.nodes}
    for node_id in (source_node_id, target_node_id):
        if node_id not in node_ids:
            raise ValueError(f"graph node does not exist: {node_id}")
    selected_types = frozenset(edge_types) if edge_types is not None else None
    adjacency: dict[str, list[tuple[str, str, float, EdgeType]]] = {
        node_id: [] for node_id in node_ids
    }
    for edge in snapshot.edges:
        if selected_types is None or edge.edge_type in selected_types:
            adjacency.setdefault(edge.source_node_id, []).append(
                (edge.target_node_id, edge.edge_id, _cost(edge.confidence), edge.edge_type)
            )
    for neighbors in adjacency.values():
        neighbors.sort(key=lambda item: (item[0], item[1]))

    distances = {source_node_id: 0.0}
    previous: dict[str, tuple[str, str, EdgeType]] = {}
    frontier: list[tuple[float, str]] = [(0.0, source_node_id)]
    while frontier:
        distance, current = heapq.heappop(frontier)
        if distance > distances.get(current, float("inf")):
            continue
        if current == target_node_id:
            break
        for neighbor, edge_id, edge_cost, edge_type in adjacency.get(current, []):
            candidate = distance + edge_cost
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = (current, edge_id, edge_type)
                heapq.heappush(frontier, (candidate, neighbor))

    if target_node_id not in distances:
        return None
    node_path = [target_node_id]
    edge_path: list[str] = []
    path_types: list[EdgeType] = []
    current = target_node_id
    while current != source_node_id:
        parent, edge_id, edge_type = previous[current]
        node_path.append(parent)
        edge_path.append(edge_id)
        path_types.append(edge_type)
        current = parent
    node_path.reverse()
    edge_path.reverse()
    path_types.reverse()
    return ShortestPathResult(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        node_ids=tuple(node_path),
        edge_ids=tuple(edge_path),
        total_cost=distances[target_node_id],
        edge_types=tuple(path_types),
    )
