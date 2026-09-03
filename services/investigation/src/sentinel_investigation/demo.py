"""Small terminal demonstration for Sentinel investigation preparation."""

import argparse
import json
from pathlib import Path
from uuid import UUID, uuid4

from .models import EvidenceReference, InvestigationRequest
from .workflow import InvestigationWorkflow


def _load_evidence(path: Path) -> tuple[EvidenceReference, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("evidence fixture must contain a JSON array")
    return tuple(EvidenceReference.model_validate(item) for item in payload)


def run_demo(
    evidence_path: Path,
    *,
    incident_id: UUID | None = None,
    question: str = "What evidence and operational guidance are available?",
) -> str:
    """Run the local deterministic investigation demo and return human-readable output."""

    request = InvestigationRequest(
        incident_id=incident_id or uuid4(),
        question=question,
        evidence=_load_evidence(evidence_path),
    )
    response = InvestigationWorkflow().investigate(request)
    lines = [
        "Sentinel investigation demo",
        f"Incident: {response.incident_id}",
        f"Evidence references: {len(response.cited_evidence)}",
        f"Summary: {response.summary}",
        "Recommended runbooks:",
    ]
    lines.extend(
        f"- {runbook.title} ({runbook.runbook_id}): {runbook.reason}"
        for runbook in response.runbooks
    )
    if not response.runbooks:
        lines.append("- None")
    lines.append("Hypotheses: none (deterministic workflow)")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Sentinel investigation demonstration.")
    parser.add_argument(
        "--evidence",
        type=Path,
        default=Path("tests/fixtures/investigation_evidence.json"),
        help="JSON array of typed evidence references",
    )
    parser.add_argument("--incident-id", type=UUID)
    parser.add_argument(
        "--question", default="What evidence and operational guidance are available?"
    )
    args = parser.parse_args()
    print(run_demo(args.evidence, incident_id=args.incident_id, question=args.question))


if __name__ == "__main__":
    main()
