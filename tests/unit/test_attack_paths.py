from datetime import UTC, datetime
from uuid import UUID

from sentinel_graph.attack_paths import assess_attack_path
from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot


def graph() -> ThreatGraphSnapshot:
    observed_at = datetime(2026, 8, 12, tzinfo=UTC)
    nodes = (
        GraphNode(node_id="user:alice", node_type="user", label="alice"),
        GraphNode(node_id="role:developer", node_type="role", label="developer"),
        GraphNode(
            node_id="database:billing",
            node_type="database",
            label="billing",
            criticality=90,
        ),
        GraphNode(node_id="database:isolated", node_type="database", label="isolated"),
    )
    edges = (
        GraphEdge(
            edge_id="grant-1",
            edge_type="has_role",
            source_node_id="user:alice",
            target_node_id="role:developer",
            observed_at=observed_at,
            confidence=0.95,
        ),
        GraphEdge(
            edge_id="access-1",
            edge_type="can_reach",
            source_node_id="role:developer",
            target_node_id="database:billing",
            observed_at=observed_at,
            confidence=0.9,
        ),
    )
    return ThreatGraphSnapshot(
        snapshot_id=UUID("12345678-1234-4234-8234-123456789012"),
        created_at=observed_at,
        nodes=nodes,
        edges=edges,
    )


def test_attack_path_reports_evidence_and_score_components() -> None:
    result = assess_attack_path(graph(), "user:alice", "database:billing")

    assert result.path_exists is True
    assert result.edge_ids == ("grant-1", "access-1")
    assert result.target_criticality == 90
    assert result.privilege_edge_count == 1
    assert result.risk_score == (
        result.criticality_component + result.privilege_component + result.confidence_component
    )
    assert result.risk_score > 70


def test_unreachable_target_has_no_path_risk() -> None:
    result = assess_attack_path(graph(), "user:alice", "database:isolated")

    assert result.path_exists is False
    assert result.node_ids == ()
    assert result.risk_score == 0


def test_missing_attack_path_node_fails_explicitly() -> None:
    try:
        assess_attack_path(graph(), "user:missing", "database:billing")
    except ValueError as error:
        assert "does not exist" in str(error)
        return
    raise AssertionError("missing attack-path node did not fail")
