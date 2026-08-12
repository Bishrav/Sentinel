"""Deterministic degree-centrality analysis for threat graphs."""

from __future__ import annotations

from collections.abc import Iterable

from .models import CentralityResult, CentralityScore, EdgeType, ThreatGraphSnapshot


def degree_centrality(
    snapshot: ThreatGraphSnapshot,
    *,
    edge_types: Iterable[EdgeType] | None = None,
) -> CentralityResult:
    """Calculate normalized directed degree centrality for every graph node."""

    selected_types = frozenset(edge_types) if edge_types is not None else None
    node_ids = {node.node_id for node in snapshot.nodes}
    in_degree = {node_id: 0 for node_id in node_ids}
    out_degree = {node_id: 0 for node_id in node_ids}
    for edge in snapshot.edges:
        if selected_types is not None and edge.edge_type not in selected_types:
            continue
        if edge.source_node_id in node_ids and edge.target_node_id in node_ids:
            out_degree[edge.source_node_id] += 1
            in_degree[edge.target_node_id] += 1
    denominator = max(1, 2 * max(0, len(node_ids) - 1))
    scores = tuple(
        CentralityScore(
            node_id=node_id,
            in_degree=in_degree[node_id],
            out_degree=out_degree[node_id],
            total_degree=in_degree[node_id] + out_degree[node_id],
            normalized_score=(in_degree[node_id] + out_degree[node_id]) / denominator,
        )
        for node_id in sorted(node_ids)
    )
    return CentralityResult(
        scores=scores,
        edge_types=tuple(sorted(selected_types)) if selected_types is not None else None,
    )
