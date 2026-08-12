"""Deterministic projection from canonical events into threat graph entities."""

from __future__ import annotations

from sentinel_ingestion.models import SecurityEvent

from .models import EdgeType, GraphEdge, GraphNode, NodeType

_ACTOR_NODE_TYPES: dict[str, NodeType] = {
    "user": "user",
    "service_account": "service",
    "api_client": "api",
    "device": "device",
    "unknown": "user",
}
_RESOURCE_NODE_TYPES = {
    "api",
    "service",
    "container",
    "database",
    "table",
    "secret",
    "repository",
}


def _resource_type(event: SecurityEvent) -> NodeType:
    candidate = str(event.attributes.get("resource_type", "service")).lower()
    return (
        candidate if candidate in _RESOURCE_NODE_TYPES else "service"
    )  # type: ignore[return-value]


def _edge_type(event: SecurityEvent) -> EdgeType | None:
    action = event.action.lower()
    if action in {"login", "authenticate", "logout"} and event.source_ip:
        return "logged_in_from"
    if action in {"call", "request", "invoke"}:
        return "calls"
    if action in {"read", "select", "download", "export"}:
        return "reads"
    if action in {"write", "insert", "update", "upload"}:
        return "writes"
    if action in {"deploy", "run"}:
        return "deployed_on"
    if action in {"grant_permission", "role_change"}:
        return "grants"
    if action in {"access", "accessed"}:
        return "accessed"
    return None


def project_event(event: SecurityEvent) -> tuple[tuple[GraphNode, ...], tuple[GraphEdge, ...]]:
    """Convert one canonical event into stable graph entities and relationships."""

    actor_type = _ACTOR_NODE_TYPES[event.actor_type]
    actor_id = f"{actor_type}:{event.actor_id}"
    resource_type = _resource_type(event)
    resource_id = f"{resource_type}:{event.resource}"
    nodes = [
        GraphNode(
            node_id=actor_id,
            node_type=actor_type,
            label=event.actor_id,
            properties={"source": event.source, "actor_type": event.actor_type},
        ),
        GraphNode(
            node_id=resource_id,
            node_type=resource_type,
            label=event.resource,
            properties={"source": event.source},
            criticality=100 if event.severity == "critical" else 0,
        ),
    ]
    if event.source_ip:
        nodes.append(
            GraphNode(
                node_id=f"ip:{event.source_ip}",
                node_type="ip",
                label=event.source_ip,
            )
        )
    if event.device_id:
        nodes.append(
            GraphNode(
                node_id=f"device:{event.device_id}",
                node_type="device",
                label=event.device_id,
            )
        )

    relationship = _edge_type(event)
    if relationship == "logged_in_from" and event.source_ip:
        target_id = f"ip:{event.source_ip}"
    else:
        target_id = resource_id
    edges: list[GraphEdge] = []
    if relationship:
        edges.append(
            GraphEdge(
                edge_id=f"event:{event.event_id}",
                edge_type=relationship,
                source_node_id=actor_id,
                target_node_id=target_id,
                properties={"event_id": str(event.event_id), "result": event.result},
                observed_at=event.timestamp,
                confidence=1.0 if event.result == "success" else 0.7,
            )
        )
    return tuple(nodes), tuple(edges)
