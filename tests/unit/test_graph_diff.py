from datetime import datetime, timezone
from uuid import UUID

from sentinel_graph.diff import diff_graphs
from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot


def snapshot(*edges: GraphEdge, include_secret: bool = True) -> ThreatGraphSnapshot:
    observed_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    nodes = [
        GraphNode(node_id="role:developer", node_type="role", label="developer"),
        GraphNode(node_id="database:billing", node_type="database", label="billing"),
    ]
    if include_secret:
        nodes.append(GraphNode(node_id="secret:key", node_type="secret", label="key"))
    return ThreatGraphSnapshot(
        snapshot_id=UUID("12345678-1234-4234-8234-123456789012"),
        created_at=observed_at,
        nodes=tuple(nodes),
        edges=edges,
    )


def test_diff_flags_newly_exposed_assets() -> None:
    observed_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    before = snapshot()
    after = snapshot(
        GraphEdge(
            edge_id="grant-1",
            edge_type="grants",
            source_node_id="role:developer",
            target_node_id="secret:key",
            observed_at=observed_at,
        )
    )

    result = diff_graphs(before, after)

    assert result.added_edge_ids == ("grant-1",)
    assert result.newly_exposed_edge_ids == ("grant-1",)
    assert result.newly_exposed_node_ids == ("secret:key",)


def test_diff_reports_removed_and_changed_relationships() -> None:
    observed_at = datetime(2026, 8, 12, tzinfo=timezone.utc)
    before_edge = GraphEdge(
        edge_id="reach-1",
        edge_type="can_reach",
        source_node_id="role:developer",
        target_node_id="database:billing",
        observed_at=observed_at,
        confidence=0.5,
    )
    after_edge = before_edge.model_copy(update={"confidence": 0.9})
    before = snapshot(before_edge)
    after = snapshot(after_edge, include_secret=False)

    result = diff_graphs(before, after)

    assert result.removed_node_ids == ("secret:key",)
    assert result.changed_edge_ids == ("reach-1",)
    assert result.newly_exposed_node_ids == ("database:billing",)
