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


class ReachabilityResult(BaseModel):
    """Deterministic result of a directed graph traversal."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_node_id: str = Field(min_length=1)
    reachable_node_ids: tuple[str, ...] = ()
    visited_node_ids: tuple[str, ...] = ()
    depth_by_node_id: dict[str, int] = Field(default_factory=dict)
    algorithm: Literal["bfs", "dfs"]
    edge_types: tuple[EdgeType, ...] | None = None


class ShortestPathResult(BaseModel):
    """Confidence-weighted directed path between two graph nodes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)
    node_ids: tuple[str, ...] = ()
    edge_ids: tuple[str, ...] = ()
    total_cost: float = Field(ge=0.0)
    edge_types: tuple[EdgeType, ...] | None = None
    algorithm: Literal["dijkstra"] = "dijkstra"


class AttackPathAssessment(BaseModel):
    """Explainable heuristic risk assessment for a candidate attack path."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_node_id: str = Field(min_length=1)
    target_node_id: str = Field(min_length=1)
    path_exists: bool
    node_ids: tuple[str, ...] = ()
    edge_ids: tuple[str, ...] = ()
    edge_types: tuple[EdgeType, ...] = ()
    total_cost: float | None = Field(default=None, ge=0.0)
    target_criticality: int = Field(ge=0, le=100)
    privilege_edge_count: int = Field(default=0, ge=0)
    criticality_component: float = Field(ge=0.0)
    privilege_component: float = Field(ge=0.0)
    confidence_component: float = Field(ge=0.0)
    risk_score: float = Field(ge=0.0, le=100.0)


class CentralityScore(BaseModel):
    """Degree-centrality measures for one graph node."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_id: str = Field(min_length=1)
    in_degree: int = Field(ge=0)
    out_degree: int = Field(ge=0)
    total_degree: int = Field(ge=0)
    normalized_score: float = Field(ge=0.0, le=1.0)


class CentralityResult(BaseModel):
    """Stable degree-centrality projection for a graph snapshot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scores: tuple[CentralityScore, ...] = ()
    edge_types: tuple[EdgeType, ...] | None = None


class StronglyConnectedComponent(BaseModel):
    """One deterministic strongly connected graph component."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node_ids: tuple[str, ...] = ()
    internal_edge_ids: tuple[str, ...] = ()
    is_cycle: bool
    contains_privilege_edge: bool


class StronglyConnectedComponentsResult(BaseModel):
    """SCC analysis and privilege-loop projection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    components: tuple[StronglyConnectedComponent, ...] = ()
    privilege_loops: tuple[StronglyConnectedComponent, ...] = ()
    edge_types: tuple[EdgeType, ...] | None = None
