"""Provider boundary for future AI-assisted investigations."""

from typing import Protocol

from .models import InvestigationRequest, InvestigationResponse


class ProviderNotConfiguredError(RuntimeError):
    """Raised when provider mode is requested without an adapter."""


class ProviderGroundingError(ValueError):
    """Raised when a provider cites evidence outside the request boundary."""


class InvestigationProvider(Protocol):
    """Minimal adapter expected from an investigation provider."""

    def generate(self, request: InvestigationRequest) -> InvestigationResponse:
        """Generate a response using only the request contract."""


def validate_provider_response(
    request: InvestigationRequest, response: InvestigationResponse
) -> InvestigationResponse:
    """Ensure provider output remains inside the trusted request boundary."""

    if response.incident_id != request.incident_id:
        raise ProviderGroundingError("provider response incident_id does not match request")
    available_ids = {item.reference_id for item in request.evidence}
    outside_boundary = {item.reference_id for item in response.cited_evidence} - available_ids
    if outside_boundary:
        references = ", ".join(sorted(outside_boundary))
        raise ProviderGroundingError(
            f"provider cited evidence outside request boundary: {references}"
        )
    return response
