import json
from datetime import UTC, datetime
from urllib.error import URLError
from uuid import uuid4

import pytest

from sentinel_investigation import (
    EvidenceReference,
    HttpInvestigationProvider,
    HttpProviderSettings,
    InvestigationRequest,
    ProviderRequestError,
)


def _request() -> InvestigationRequest:
    return InvestigationRequest(
        incident_id=uuid4(),
        question="Explain this incident.",
        mode="provider",
        evidence=(
            EvidenceReference(
                reference_type="event", reference_id="event-001", source="fixture"
            ),
        ),
    )


def test_http_provider_serializes_request_and_parses_response() -> None:
    request = _request()
    captured: dict[str, object] = {}

    def transport(outbound, timeout):
        captured["url"] = outbound.full_url
        captured["body"] = json.loads(outbound.data)
        captured["authorization"] = outbound.get_header("Authorization")
        captured["timeout"] = timeout
        return json.dumps(
            {
                "incident_id": str(request.incident_id),
                "summary": "Provider response.",
                "hypotheses": [],
                "cited_evidence": [
                    {
                        "reference_type": "event",
                        "reference_id": "event-001",
                        "source": "fixture",
                    }
                ],
                "runbooks": [],
                "generated_at": datetime.now(UTC).isoformat(),
                "schema_version": "1.0",
            }
        ).encode()

    response = HttpInvestigationProvider(
        HttpProviderSettings(
            endpoint="https://provider.example.test/investigate", api_key="secret"
        ),
        transport=transport,
    ).generate(request)

    assert response.incident_id == request.incident_id
    assert captured["url"] == "https://provider.example.test/investigate"
    assert captured["body"]["question"] == request.question
    assert captured["authorization"] == "Bearer secret"
    assert captured["timeout"] == 10.0


def test_http_provider_rejects_invalid_response_payload() -> None:
    with pytest.raises(ProviderRequestError, match="invalid response JSON"):
        HttpInvestigationProvider(
            HttpProviderSettings(endpoint="https://provider.example.test/investigate"),
            transport=lambda _request, _timeout: b"not-json",
        ).generate(_request())


def test_http_provider_retries_transient_failures_with_bounded_backoff() -> None:
    request = _request()
    attempts = 0
    delays: list[float] = []

    def transport(_request, _timeout):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise URLError("temporary outage")
        return json.dumps(
            {
                "incident_id": str(request.incident_id),
                "summary": "Recovered provider response.",
                "hypotheses": [],
                "cited_evidence": [
                    {
                        "reference_type": "event",
                        "reference_id": "event-001",
                        "source": "fixture",
                    }
                ],
                "runbooks": [],
                "generated_at": datetime.now(UTC).isoformat(),
                "schema_version": "1.0",
            }
        ).encode()

    response = HttpInvestigationProvider(
        HttpProviderSettings(
            endpoint="https://provider.example.test/investigate",
            max_retries=2,
            backoff_seconds=0.25,
        ),
        transport=transport,
        sleeper=delays.append,
    ).generate(request)

    assert response.summary == "Recovered provider response."
    assert attempts == 3
    assert delays == [0.25, 0.5]
