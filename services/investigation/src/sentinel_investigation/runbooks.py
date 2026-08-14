"""Deterministic runbook catalog and evidence-type matching."""

from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field

from .models import EvidenceReference, EvidenceType, RunbookRecommendation


class Runbook(BaseModel):
    """An operational guide with explicit evidence triggers."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    runbook_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,63}$")
    title: str = Field(min_length=1, max_length=160)
    trigger_types: frozenset[EvidenceType] = Field(min_length=1)


DEFAULT_RUNBOOKS: tuple[Runbook, ...] = (
    Runbook(
        runbook_id="credential-compromise-response",
        title="Credential compromise response",
        trigger_types=frozenset({"event", "sequence_match"}),
    ),
    Runbook(
        runbook_id="graph-relationship-investigation",
        title="Graph relationship investigation",
        trigger_types=frozenset({"graph_path", "incident"}),
    ),
    Runbook(
        runbook_id="behavioral-anomaly-triage",
        title="Behavioral anomaly triage",
        trigger_types=frozenset({"baseline"}),
    ),
)


class RunbookCatalog:
    """Select runbooks using stable evidence-type matching."""

    def __init__(self, runbooks: Iterable[Runbook] = DEFAULT_RUNBOOKS) -> None:
        self._runbooks = tuple(sorted(runbooks, key=lambda item: item.runbook_id))

    def recommend(
        self, evidence: tuple[EvidenceReference, ...]
    ) -> tuple[RunbookRecommendation, ...]:
        evidence_types = {item.reference_type for item in evidence}
        recommendations: list[RunbookRecommendation] = []
        for runbook in self._runbooks:
            matched_types = sorted(runbook.trigger_types & evidence_types)
            if not matched_types:
                continue
            formatted_types = ", ".join(item.replace("_", " ") for item in matched_types)
            recommendations.append(
                RunbookRecommendation(
                    runbook_id=runbook.runbook_id,
                    title=runbook.title,
                    reason=f"Evidence includes: {formatted_types}.",
                )
            )
        return tuple(recommendations)
