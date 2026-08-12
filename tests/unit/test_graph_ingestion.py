from sentinel_ingestion.normalizer import normalize

from sentinel_graph.projection import project_event
from sentinel_graph.store import InMemoryGraphStore


def make_event(**overrides: object):
    raw = {
        "event_id": "12345678-1234-4234-8234-123456789012",
        "timestamp": "2026-08-12T12:00:00Z",
        "actor_id": "user-42",
        "actor_type": "user",
        "source_ip": "192.0.2.10",
        "action": "login",
        "resource": "identity-provider",
        "result": "success",
        "severity": "low",
    }
    raw.update(overrides)
    return normalize(raw, source="test")


def test_projection_creates_stable_nodes_and_login_edge() -> None:
    nodes, edges = project_event(make_event())

    assert {node.node_id for node in nodes} == {
        "user:user-42",
        "service:identity-provider",
        "ip:192.0.2.10",
    }
    assert edges[0].edge_type == "logged_in_from"
    assert edges[0].target_node_id == "ip:192.0.2.10"


def test_store_is_idempotent_and_snapshot_is_sorted() -> None:
    store = InMemoryGraphStore()
    event = make_event()

    assert store.ingest(event) is True
    assert store.ingest(event) is False
    snapshot = store.snapshot()

    assert len(snapshot.nodes) == 3
    assert len(snapshot.edges) == 1
    assert [node.node_id for node in snapshot.nodes] == sorted(node.node_id for node in snapshot.nodes)
    assert store.edge(f"event:{event.event_id}") is not None
