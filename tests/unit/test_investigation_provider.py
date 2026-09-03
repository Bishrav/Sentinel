from datetime import UTC, datetime
from uuid import uuid4

import pytest

from sentinel_investigation import (
    EvidenceReference,
    InvestigationHypothesis,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationWorkflow,
    ProviderGroundingError,
    ProviderNotConfiguredError,
)


def _request() -> InvestigationRequest:
    return InvestigationRequest(
        incident_id=uuid4(),
        question="Explain this incident.",
        mode="provider",
        evidence=(
            EvidenceReference(reference_type="event", reference_id="event-001", source="fixture"),
        ),
    )


class GroundedProvider:
    def generate(self, request: InvestigationRequest) -> InvestigationResponse:
        return InvestigationResponse(
            incident_id=request.incident_id,
            summary="The provider cited the supplied event.",
            hypotheses=(
                InvestigationHypothesis(
                    hypothesis_id="grounded_test",
                    statement="The event requires review.",
                    confidence=0.5,
                    citations=("event-001",),
                ),
            ),
            cited_evidence=request.evidence,
            generated_at=datetime.now(UTC),
        )


class UngroundedProvider:
    def generate(self, request: InvestigationRequest) -> InvestigationResponse:
        return InvestigationResponse(
            incident_id=request.incident_id,
            summary="The provider cited an unavailable event.",
            hypotheses=(),
            cited_evidence=(
                EvidenceReference(
                    reference_type="event", reference_id="outside", source="provider"
                ),
            ),
            generated_at=datetime.now(UTC),
        )


def test_provider_mode_requires_an_injected_provider() -> None:
    with pytest.raises(ProviderNotConfiguredError):
        InvestigationWorkflow().investigate(_request())


def test_provider_response_must_remain_inside_request_evidence() -> None:
    with pytest.raises(ProviderGroundingError, match="outside request boundary"):
        InvestigationWorkflow(provider=UngroundedProvider()).investigate(_request())


def test_grounded_provider_response_is_accepted() -> None:
    response = InvestigationWorkflow(provider=GroundedProvider()).investigate(_request())

    assert response.hypotheses[0].citations == ("event-001",)
