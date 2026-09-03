from datetime import UTC, datetime
from uuid import UUID

from sentinel_graph.cycles import strongly_connected_components
from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot


def graph() -> ThreatGraphSnapshot:
    observed_at = datetime(2026, 8, 12, tzinfo=UTC)
    nodes = tuple(
        GraphNode(node_id=node_id, node_type=node_type, label=node_id)
        for node_id, node_type in (
            ("role:developer", "role"),
            ("role:admin", "role"),
            ("service:api", "service"),
            ("database:billing", "database"),
        )
    )
    edges = (
        GraphEdge(
            edge_id="loop-1",
            edge_type="grants",
            source_node_id="role:developer",
            target_node_id="role:admin",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="loop-2",
            edge_type="has_role",
            source_node_id="role:admin",
            target_node_id="role:developer",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="path-1",
            edge_type="calls",
            source_node_id="service:api",
            target_node_id="database:billing",
            observed_at=observed_at,
        ),
    )
    return ThreatGraphSnapshot(
        snapshot_id=UUID("12345678-1234-4234-8234-123456789012"),
        created_at=observed_at,
        nodes=nodes,
        edges=edges,
    )


def test_scc_analysis_identifies_privilege_loop() -> None:
    result = strongly_connected_components(graph())

    assert len(result.components) == 3
    assert len(result.privilege_loops) == 1
    loop = result.privilege_loops[0]
    assert loop.node_ids == ("role:admin", "role:developer")
    assert loop.internal_edge_ids == ("loop-1", "loop-2")
    assert loop.is_cycle is True
    assert loop.contains_privilege_edge is True


def test_scc_filter_can_remove_privilege_loop_edges() -> None:
    result = strongly_connected_components(graph(), edge_types={"calls"})

    assert result.privilege_loops == ()
    assert all(component.is_cycle is False for component in result.components)
