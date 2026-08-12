"""Typed threat graph node, edge, and snapshot contracts."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

NodeType = Literal[
    "user",
    "credential",
    "device",
    "ip",
    "role",
    "permission",
    "api",
    "service",
    "container",
    "database",
    "table",
    "secret",
    "repository",
]

EdgeType = Literal[
    "logged_in_from",
    "has_role",
    "grants",
    "calls",
    "accessed",
    "deployed_on",
    "can_reach",
    "owns",
    "reads",
    "writes",
    "exposed_to",
]


class GraphNode(BaseModel):
    """Stable identity and metadata for one threat graph entity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9:._/-]*$", min_length=1)
    node_type: NodeType
    label: str = Field(min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)
    criticality: int = Field(default=0, ge=0, le=100)


class GraphEdge(BaseModel):
    """Directed relationship between two graph nodes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    edge_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9:._/-]*$", min_length=1)
    edge_type: EdgeType
    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)
    properties: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ThreatGraphSnapshot(BaseModel):
    """Versioned graph projection used by algorithms and persistence adapters."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    snapshot_id: UUID
    created_at: datetime
    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
    schema_version: Literal["1.0"] = "1.0"
