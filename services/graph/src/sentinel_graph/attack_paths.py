"""Explainable attack-path assessment built on weighted graph paths."""

from __future__ import annotations

from collections.abc import Iterable

from .models import AttackPathAssessment, EdgeType, ThreatGraphSnapshot
from .paths import shortest_path

_PRIVILEGE_EDGES = frozenset({"has_role", "grants", "owns"})


def assess_attack_path(
    snapshot: ThreatGraphSnapshot,
    source_node_id: str,
    target_node_id: str,
    *,
    edge_types: Iterable[EdgeType] | None = None,
) -> AttackPathAssessment:
    """Assess path evidence and calculate a bounded heuristic risk score.

    The score is deliberately transparent, not a production incident score:
    ``0.70 * target criticality + privilege component + confidence component``.
    The components are capped so the final score remains in ``[0, 100]``.
    """

    nodes = {node.node_id: node for node in snapshot.nodes}
    if source_node_id not in nodes or target_node_id not in nodes:
        missing = source_node_id if source_node_id not in nodes else target_node_id
        raise ValueError(f"graph node does not exist: {missing}")
    path = shortest_path(
        snapshot,
        source_node_id,
        target_node_id,
        edge_types=edge_types,
    )
    criticality_component = nodes[target_node_id].criticality * 0.70
    if path is None:
        return AttackPathAssessment(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            path_exists=False,
            target_criticality=nodes[target_node_id].criticality,
            criticality_component=criticality_component,
            privilege_component=0.0,
            confidence_component=0.0,
            risk_score=0.0,
        )
    privilege_edge_count = sum(edge_type in _PRIVILEGE_EDGES for edge_type in path.edge_types or ())
    privilege_component = min(30.0, privilege_edge_count * 10.0)
    confidence_component = min(20.0, max(0.0, 20.0 - path.total_cost * 2.0))
    risk_score = min(100.0, criticality_component + privilege_component + confidence_component)
    return AttackPathAssessment(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        path_exists=True,
        node_ids=path.node_ids,
        edge_ids=path.edge_ids,
        edge_types=path.edge_types or (),
        total_cost=path.total_cost,
        target_criticality=nodes[target_node_id].criticality,
        privilege_edge_count=privilege_edge_count,
        criticality_component=criticality_component,
        privilege_component=privilege_component,
        confidence_component=confidence_component,
        risk_score=risk_score,
    )
