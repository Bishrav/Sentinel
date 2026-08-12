"""Permission-aware graph snapshot diffing."""

from __future__ import annotations

from .models import GraphDiffResult, ThreatGraphSnapshot

_EXPOSURE_EDGE_TYPES = frozenset({"can_reach", "exposed_to", "grants"})


def diff_graphs(
    before: ThreatGraphSnapshot,
    after: ThreatGraphSnapshot,
) -> GraphDiffResult:
    """Compare graph snapshots and flag newly exposed relationship targets."""

    before_nodes = {node.node_id: node for node in before.nodes}
    after_nodes = {node.node_id: node for node in after.nodes}
    before_edges = {edge.edge_id: edge for edge in before.edges}
    after_edges = {edge.edge_id: edge for edge in after.edges}
    added_edge_ids = sorted(set(after_edges) - set(before_edges))
    removed_edge_ids = sorted(set(before_edges) - set(after_edges))
    changed_edge_ids = sorted(
        edge_id
        for edge_id in set(before_edges) & set(after_edges)
        if before_edges[edge_id] != after_edges[edge_id]
    )
    newly_exposed_edges = sorted(
        edge_id
        for edge_id in added_edge_ids + changed_edge_ids
        if after_edges[edge_id].edge_type in _EXPOSURE_EDGE_TYPES
    )
    newly_exposed_nodes = sorted(
        {
            after_edges[edge_id].target_node_id
            for edge_id in newly_exposed_edges
            if after_edges[edge_id].target_node_id in after_nodes
        }
    )
    return GraphDiffResult(
        added_node_ids=tuple(sorted(set(after_nodes) - set(before_nodes))),
        removed_node_ids=tuple(sorted(set(before_nodes) - set(after_nodes))),
        added_edge_ids=tuple(added_edge_ids),
        removed_edge_ids=tuple(removed_edge_ids),
        changed_edge_ids=tuple(changed_edge_ids),
        newly_exposed_edge_ids=tuple(newly_exposed_edges),
        newly_exposed_node_ids=tuple(newly_exposed_nodes),
    )
