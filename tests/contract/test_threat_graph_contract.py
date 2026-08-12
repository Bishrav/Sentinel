import json
from pathlib import Path

from sentinel_graph.models import GraphEdge, GraphNode, ThreatGraphSnapshot


def test_threat_graph_snapshot_has_stable_typed_contract() -> None:
    schema = json.loads(Path("schemas/threat-graph.schema.json").read_text(encoding="utf-8"))
    node = GraphNode(
        node_id="user:user-42",
        node_type="user",
        label="user-42",
        criticality=35,
    )
    edge = GraphEdge(
        edge_id="user:user-42/role:developer",
        edge_type="has_role",
        source_node_id=node.node_id,
        target_node_id="role:developer",
        observed_at="2026-08-12T12:00:00Z",
    )
    snapshot = ThreatGraphSnapshot(
        snapshot_id="12345678-1234-4234-8234-123456789012",
        created_at="2026-08-12T12:00:00Z",
        nodes=(node,),
        edges=(edge,),
    )

    payload = snapshot.model_dump(mode="json")
    assert set(schema["required"]).issubset(payload)
    assert payload["schema_version"] == "1.0"
    assert payload["edges"][0]["source_node_id"] == "user:user-42"


def test_graph_contract_rejects_invalid_criticality_and_confidence() -> None:
    try:
        GraphNode(node_id="database:billing", node_type="database", label="billing", criticality=101)
    except ValueError:
        pass
    else:
        raise AssertionError("GraphNode accepted criticality above 100")

    try:
        GraphEdge(
            edge_id="edge-1",
            edge_type="reads",
            source_node_id="user:user-42",
            target_node_id="table:payments",
            observed_at="2026-08-12T12:00:00Z",
            confidence=1.1,
        )
    except ValueError:
        return
    raise AssertionError("GraphEdge accepted confidence above 1")
