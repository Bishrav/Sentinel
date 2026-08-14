"""Versioned contracts for deterministic and AI-assisted investigations."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

EvidenceType = Literal[
    "event",
    "incident",
    "sequence_match",
    "graph_path",
    "baseline",
    "rule",
]
InvestigationMode = Literal["deterministic", "provider"]


class EvidenceReference(BaseModel):
    """A source that can support a material investigation statement."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_type: EvidenceType
    reference_id: str = Field(min_length=1, max_length=256)
    source: str = Field(min_length=1, max_length=256)


class InvestigationRequest(BaseModel):
    """Bounded investigation input assembled from trusted Sentinel evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    question: str = Field(min_length=1, max_length=1_000)
    evidence: tuple[EvidenceReference, ...] = Field(min_length=1, max_length=100)
    mode: InvestigationMode = "deterministic"


class InvestigationHypothesis(BaseModel):
    """One proposed explanation with explicit supporting references."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hypothesis_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$")
    statement: str = Field(min_length=1, max_length=2_000)
    confidence: float = Field(ge=0, le=1)
    citations: tuple[str, ...] = Field(min_length=1, max_length=20)


class RunbookRecommendation(BaseModel):
    """A safe operational guide selected from evidence types, not model output."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    runbook_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$")
    title: str = Field(min_length=1, max_length=160)
    reason: str = Field(min_length=1, max_length=500)


class InvestigationResponse(BaseModel):
    """Evidence-grounded investigation output with citation integrity checks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: UUID
    summary: str = Field(min_length=1, max_length=4_000)
    hypotheses: tuple[InvestigationHypothesis, ...] = Field(max_length=20)
    cited_evidence: tuple[EvidenceReference, ...] = Field(min_length=1, max_length=100)
    runbooks: tuple[RunbookRecommendation, ...] = Field(default=(), max_length=20)
    generated_at: datetime
    schema_version: Literal["1.0"] = "1.0"

    @model_validator(mode="after")
    def validate_citations(self) -> "InvestigationResponse":
        available_ids = {item.reference_id for item in self.cited_evidence}
        missing = {
            citation
            for hypothesis in self.hypotheses
            for citation in hypothesis.citations
            if citation not in available_ids
        }
        if missing:
            missing_ids = ", ".join(sorted(missing))
            raise ValueError(f"hypothesis citations must reference cited_evidence: {missing_ids}")
        return self
