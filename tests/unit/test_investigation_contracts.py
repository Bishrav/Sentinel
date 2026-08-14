from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from sentinel_investigation.models import (
    EvidenceReference,
    InvestigationHypothesis,
    InvestigationRequest,
    InvestigationResponse,
)


def test_investigation_response_requires_citations_to_resolve() -> None:
    incident_id = uuid4()
    evidence = EvidenceReference(
        reference_type="event",
        reference_id="event-001",
        source="fixture",
    )

    response = InvestigationResponse(
        incident_id=incident_id,
        summary="A successful login followed a failed authentication attempt.",
        hypotheses=(
            InvestigationHypothesis(
                hypothesis_id="credential_reuse",
                statement="The account may have been accessed with reused credentials.",
                confidence=0.7,
                citations=("event-001",),
            ),
        ),
        cited_evidence=(evidence,),
        generated_at=datetime.now(UTC),
    )

    assert response.schema_version == "1.0"


def test_investigation_response_rejects_unknown_citation() -> None:
    with pytest.raises(ValidationError, match="event-missing"):
        InvestigationResponse(
            incident_id=uuid4(),
            summary="Unsupported conclusion.",
            hypotheses=(
                InvestigationHypothesis(
                    hypothesis_id="unsupported",
                    statement="This cannot be grounded.",
                    confidence=0.1,
                    citations=("event-missing",),
                ),
            ),
            cited_evidence=(
                EvidenceReference(
                    reference_type="event",
                    reference_id="event-present",
                    source="fixture",
                ),
            ),
            generated_at=datetime.now(UTC),
        )


def test_investigation_request_is_bounded_and_requires_evidence() -> None:
    request = InvestigationRequest(
        incident_id=uuid4(),
        question="What explains this incident?",
        evidence=(
            EvidenceReference(
                reference_type="incident",
                reference_id="incident-001",
                source="incident-store",
            ),
        ),
    )

    assert request.mode == "deterministic"

    with pytest.raises(ValidationError):
        InvestigationRequest(
            incident_id=uuid4(),
            question="",
            evidence=(),
        )
