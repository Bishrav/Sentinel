from uuid import uuid4

from sentinel_investigation import EvidenceReference, InvestigationRequest, InvestigationWorkflow


def test_deterministic_investigation_replay_preserves_output_contract() -> None:
    request = InvestigationRequest(
        incident_id=uuid4(),
        question="What evidence is available?",
        evidence=(
            EvidenceReference(
                reference_type="event",
                reference_id="event-001",
                source="replay-fixture",
            ),
        ),
    )
    workflow = InvestigationWorkflow()

    first = workflow.investigate(request)
    second = workflow.investigate(request)

    assert first.model_dump(exclude={"generated_at"}) == second.model_dump(exclude={"generated_at"})
