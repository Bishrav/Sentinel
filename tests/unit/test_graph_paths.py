from datetime import UTC, datetime
from uuid import UUID

from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot
from sentinel_graph.paths import shortest_path


def graph() -> ThreatGraphSnapshot:
    observed_at = datetime(2026, 8, 12, tzinfo=UTC)
    nodes = tuple(
        GraphNode(node_id=node_id, node_type=node_type, label=node_id)
        for node_id, node_type in (
            ("user:alice", "user"),
            ("service:trusted", "service"),
            ("service:weak", "service"),
            ("database:billing", "database"),
            ("secret:billing-key", "secret"),
            ("database:isolated", "database"),
        )
    )
    edges = (
        GraphEdge(
            edge_id="trusted-1",
            edge_type="calls",
            source_node_id="user:alice",
            target_node_id="service:trusted",
            observed_at=observed_at,
            confidence=0.95,
        ),
        GraphEdge(
            edge_id="trusted-2",
            edge_type="accessed",
            source_node_id="service:trusted",
            target_node_id="database:billing",
            observed_at=observed_at,
            confidence=0.95,
        ),
        GraphEdge(
            edge_id="trusted-3",
            edge_type="reads",
            source_node_id="database:billing",
            target_node_id="secret:billing-key",
            observed_at=observed_at,
            confidence=0.95,
        ),
        GraphEdge(
            edge_id="weak-1",
            edge_type="calls",
            source_node_id="user:alice",
            target_node_id="service:weak",
            observed_at=observed_at,
            confidence=0.4,
        ),
        GraphEdge(
            edge_id="weak-2",
            edge_type="accessed",
            source_node_id="service:weak",
            target_node_id="secret:billing-key",
            observed_at=observed_at,
            confidence=0.4,
        ),
    )
    return ThreatGraphSnapshot(
        snapshot_id=UUID("12345678-1234-4234-8234-123456789012"),
        created_at=observed_at,
        nodes=nodes,
        edges=edges,
    )


def test_dijkstra_prefers_the_high_confidence_route() -> None:
    result = shortest_path(graph(), "user:alice", "secret:billing-key")

    assert result is not None
    assert result.node_ids == (
        "user:alice",
        "service:trusted",
        "database:billing",
        "secret:billing-key",
    )
    assert result.edge_ids == ("trusted-1", "trusted-2", "trusted-3")
    assert result.total_cost < 4.0


def test_path_filter_and_disconnected_target() -> None:
    result = shortest_path(graph(), "user:alice", "secret:billing-key", edge_types={"calls"})
    disconnected = shortest_path(graph(), "user:alice", "database:isolated")

    assert result is None
    assert disconnected is None


def test_missing_path_nodes_fail_explicitly() -> None:
    try:
        shortest_path(graph(), "user:missing", "secret:billing-key")
    except ValueError as error:
        assert "does not exist" in str(error)
        return
    raise AssertionError("missing path node did not fail")
