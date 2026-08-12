from datetime import datetime, timezone
from uuid import UUID

from sentinel_graph.centrality import degree_centrality
from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot


def graph() -> ThreatGraphSnapshot:
    observed_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    nodes = tuple(
        GraphNode(node_id=node_id, node_type=node_type, label=node_id)
        for node_id, node_type in (
            ("user:alice", "user"),
            ("service:api", "service"),
            ("database:billing", "database"),
            ("secret:key", "secret"),
        )
    )
    edges = (
        GraphEdge(
            edge_id="e1",
            edge_type="calls",
            source_node_id="user:alice",
            target_node_id="service:api",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="e2",
            edge_type="accessed",
            source_node_id="service:api",
            target_node_id="database:billing",
            observed_at=observed_at,
        ),
        GraphEdge(
            edge_id="e3",
            edge_type="reads",
            source_node_id="service:api",
            target_node_id="secret:key",
            observed_at=observed_at,
        ),
    )
    return ThreatGraphSnapshot(
        snapshot_id=UUID("12345678-1234-4234-8234-123456789012"),
        created_at=observed_at,
        nodes=nodes,
        edges=edges,
    )


def test_degree_centrality_identifies_the_choke_point() -> None:
    result = degree_centrality(graph())
    scores = {score.node_id: score for score in result.scores}

    assert scores["service:api"].total_degree == 3
    assert scores["service:api"].normalized_score == 0.5
    assert scores["service:api"].normalized_score > scores["user:alice"].normalized_score


def test_centrality_can_filter_relationship_types() -> None:
    result = degree_centrality(graph(), edge_types={"calls"})

    assert result.edge_types == ("calls",)
    scores = {score.node_id: score for score in result.scores}
    assert scores["service:api"].total_degree == 1
    assert scores["user:alice"].total_degree == 1
