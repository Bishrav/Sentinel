from datetime import datetime, timezone
from uuid import UUID

from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot
from sentinel_graph.traversal import reachability


def graph() -> ThreatGraphSnapshot:
    nodes = tuple(
        GraphNode(node_id=node_id, node_type=node_type, label=node_id)
        for node_id, node_type in (
            ("user:alice", "user"),
            ("role:developer", "role"),
            ("service:api", "service"),
            ("database:billing", "database"),
            ("secret:billing-key", "secret"),
        )
    )
    observed_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    edges = (
        GraphEdge(
            edge_id="e1",
            edge_type="has_role",
            source_node_id="user:alice",
            target_node_id="role:developer",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="e2",
            edge_type="calls",
            source_node_id="role:developer",
            target_node_id="service:api",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="e3",
            edge_type="accessed",
            source_node_id="service:api",
            target_node_id="database:billing",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="e4",
            edge_type="reads",
            source_node_id="database:billing",
            target_node_id="secret:billing-key",
            observed_at=observed_at,
        ),
    )
    return ThreatGraphSnapshot(
        snapshot_id=UUID("12345678-1234-4234-8234-123456789012"),
        created_at=observed_at,
        nodes=nodes,
        edges=edges,
    )


def test_bfs_returns_shortest_depths_and_stable_order() -> None:
    result = reachability(graph(), "user:alice", algorithm="bfs")

    assert result.reachable_node_ids == (
        "role:developer",
        "service:api",
        "database:billing",
        "secret:billing-key",
    )
    assert result.depth_by_node_id["secret:billing-key"] == 4


def test_dfs_can_filter_relationship_types() -> None:
    result = reachability(graph(), "user:alice", algorithm="dfs", edge_types={"has_role", "calls"})

    assert result.reachable_node_ids == ("role:developer", "service:api")
    assert result.edge_types == ("calls", "has_role")


def test_invalid_source_and_algorithm_fail_explicitly() -> None:
    try:
        reachability(graph(), "user:missing")
    except ValueError as error:
        assert "does not exist" in str(error)
    else:
        raise AssertionError("missing source did not fail")

    try:
        reachability(graph(), "user:alice", algorithm="dijkstra")
    except ValueError:
        return
    raise AssertionError("invalid traversal algorithm did not fail")
