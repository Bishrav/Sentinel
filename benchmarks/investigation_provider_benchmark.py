"""Local benchmark for typed investigation provider serialization."""

from __future__ import annotations

import json
from time import perf_counter
from uuid import uuid4

from sentinel_investigation.http_provider import HttpInvestigationProvider, HttpProviderSettings
from sentinel_investigation.metrics import ProviderMetrics
from sentinel_investigation.models import EvidenceReference, InvestigationRequest


def run_benchmark(request_count: int = 1_000) -> dict[str, float | int]:
    """Round-trip a deterministic provider payload without network access."""

    if request_count < 1:
        raise ValueError("request_count must be at least 1")
    incident_id = uuid4()
    investigation_request = InvestigationRequest(
        incident_id=incident_id,
        question="Summarize the available evidence.",
        mode="provider",
        evidence=(EvidenceReference(reference_type="event", reference_id="benchmark-event", source="benchmark"),),
    )
    response = json.dumps(
        {
            "incident_id": str(incident_id),
            "summary": "Benchmark response.",
            "hypotheses": [],
            "cited_evidence": [
                {"reference_type": "event", "reference_id": "benchmark-event", "source": "benchmark"}
            ],
            "runbooks": [],
            "generated_at": "2026-01-01T00:00:00Z",
            "schema_version": "1.0",
        }
    ).encode()
    metrics = ProviderMetrics()
    provider = HttpInvestigationProvider(
        HttpProviderSettings(endpoint="https://benchmark.invalid/investigate", max_retries=0),
        transport=lambda _request, _timeout: response,
        metrics=metrics,
    )
    started = perf_counter()
    for _ in range(request_count):
        provider.generate(investigation_request)
    elapsed = perf_counter() - started
    return {
        "requests": request_count,
        "successful_requests": metrics.successes,
        "elapsed_seconds": elapsed,
        "requests_per_second": request_count / elapsed if elapsed else 0.0,
        "average_latency_ms": (elapsed * 1000) / request_count,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
