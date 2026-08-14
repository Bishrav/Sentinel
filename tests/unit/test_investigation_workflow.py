from uuid import uuid4

from sentinel_investigation import (
    EvidenceReference,
    InvestigationRequest,
    InvestigationWorkflow,
)


def test_workflow_returns_all_input_evidence_without_unverified_hypotheses() -> None:
    request = InvestigationRequest(
        incident_id=uuid4(),
        question="What evidence is available?",
        evidence=(
            EvidenceReference(
                reference_type="event",
                reference_id="event-001",
                source="replay-fixture",
            ),
            EvidenceReference(
                reference_type="graph_path",
                reference_id="path-001",
                source="neo4j-projection",
            ),
        ),
    )

    response = InvestigationWorkflow().investigate(request)

    assert response.incident_id == request.incident_id
    assert response.cited_evidence == request.evidence
    assert response.hypotheses == ()
    assert [item.runbook_id for item in response.runbooks] == [
        "credential-compromise-response",
        "graph-relationship-investigation",
    ]
    assert "1 event" in response.summary
    assert "1 graph path" in response.summary
