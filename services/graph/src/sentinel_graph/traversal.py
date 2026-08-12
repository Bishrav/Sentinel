"""Directed BFS and DFS reachability over immutable graph snapshots."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from .models import EdgeType, ReachabilityResult, ThreatGraphSnapshot


def _adjacency(
    snapshot: ThreatGraphSnapshot,
    edge_types: frozenset[EdgeType] | None,
) -> dict[str, tuple[str, ...]]:
    adjacency: dict[str, list[str]] = {node.node_id: [] for node in snapshot.nodes}
    for edge in snapshot.edges:
        if edge_types is None or edge.edge_type in edge_types:
            adjacency.setdefault(edge.source_node_id, []).append(edge.target_node_id)
    return {node_id: tuple(sorted(targets)) for node_id, targets in adjacency.items()}


def reachability(
    snapshot: ThreatGraphSnapshot,
    source_node_id: str,
    *,
    algorithm: str = "bfs",
    edge_types: Iterable[EdgeType] | None = None,
) -> ReachabilityResult:
    """Return nodes reachable from ``source_node_id`` using directed edges.

    Traversal order is stable because neighbors are sorted by node ID. The
    source is included in ``visited_node_ids`` but excluded from reachable
    results. An unknown source raises ``ValueError`` rather than silently
    returning an empty graph result.
    """

    if algorithm not in {"bfs", "dfs"}:
        raise ValueError("algorithm must be 'bfs' or 'dfs'")
    node_ids = {node.node_id for node in snapshot.nodes}
    if source_node_id not in node_ids:
        raise ValueError(f"source node does not exist: {source_node_id}")
    selected_types = frozenset(edge_types) if edge_types is not None else None
    adjacency = _adjacency(snapshot, selected_types)
    visited: list[str] = []
    depth: dict[str, int] = {source_node_id: 0}
    seen = {source_node_id}
    frontier: deque[str] = deque([source_node_id])

    while frontier:
        current = frontier.popleft() if algorithm == "bfs" else frontier.pop()
        visited.append(current)
        neighbors = adjacency.get(current, ())
        if algorithm == "dfs":
            neighbors = tuple(reversed(neighbors))
        for neighbor in neighbors:
            if neighbor in seen:
                continue
            seen.add(neighbor)
            depth[neighbor] = depth[current] + 1
            frontier.append(neighbor)

    return ReachabilityResult(
        source_node_id=source_node_id,
        reachable_node_ids=tuple(node_id for node_id in visited if node_id != source_node_id),
        visited_node_ids=tuple(visited),
        depth_by_node_id=depth,
        algorithm=algorithm,  # type: ignore[arg-type]
        edge_types=tuple(sorted(selected_types)) if selected_types is not None else None,
    )
