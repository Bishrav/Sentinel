"""Deterministic Tarjan SCC and privilege-loop analysis."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    EdgeType,
    GraphEdge,
    StronglyConnectedComponent,
    StronglyConnectedComponentsResult,
    ThreatGraphSnapshot,
)

_PRIVILEGE_EDGES = frozenset({"has_role", "grants", "owns"})


def strongly_connected_components(
    snapshot: ThreatGraphSnapshot,
    *,
    edge_types: Iterable[EdgeType] | None = None,
) -> StronglyConnectedComponentsResult:
    """Find directed SCCs and flag cyclic components with privilege edges."""

    selected_types = frozenset(edge_types) if edge_types is not None else None
    node_ids = sorted(node.node_id for node in snapshot.nodes)
    edges = tuple(
        edge
        for edge in snapshot.edges
        if selected_types is None or edge.edge_type in selected_types
    )
    adjacency: dict[str, tuple[str, ...]] = {
        node_id: tuple(
            sorted(edge.target_node_id for edge in edges if edge.source_node_id == node_id)
        )
        for node_id in node_ids
    }
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    raw_components: list[tuple[str, ...]] = []

    def visit(node_id: str) -> None:
        nonlocal index
        indices[node_id] = index
        lowlinks[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)
        for neighbor in adjacency[node_id]:
            if neighbor not in indices:
                visit(neighbor)
                lowlinks[node_id] = min(lowlinks[node_id], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node_id] = min(lowlinks[node_id], indices[neighbor])
        if lowlinks[node_id] != indices[node_id]:
            return
        component: list[str] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node_id:
                break
        raw_components.append(tuple(sorted(component)))

    for node_id in node_ids:
        if node_id not in indices:
            visit(node_id)

    components = tuple(
        _component_result(component, edges)
        for component in sorted(raw_components)
    )
    return StronglyConnectedComponentsResult(
        components=components,
        privilege_loops=tuple(
            component
            for component in components
            if component.contains_privilege_edge and component.is_cycle
        ),
        edge_types=tuple(sorted(selected_types)) if selected_types is not None else None,
    )


def _component_result(
    node_ids: tuple[str, ...],
    edges: tuple[GraphEdge, ...],
) -> StronglyConnectedComponent:
    members = set(node_ids)
    internal_edges = tuple(
        edge for edge in edges if edge.source_node_id in members and edge.target_node_id in members
    )
    is_cycle = len(node_ids) > 1 or any(
        edge.source_node_id == edge.target_node_id for edge in internal_edges
    )
    return StronglyConnectedComponent(
        node_ids=node_ids,
        internal_edge_ids=tuple(sorted(edge.edge_id for edge in internal_edges)),
        is_cycle=is_cycle,
        contains_privilege_edge=any(edge.edge_type in _PRIVILEGE_EDGES for edge in internal_edges),
    )
