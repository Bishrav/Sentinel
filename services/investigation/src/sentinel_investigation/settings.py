"""Environment-backed configuration for optional provider activation."""

import os

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from .http_provider import HttpInvestigationProvider, HttpProviderSettings


class InvestigationProviderSettings(BaseModel):
    """Provider settings loaded from SENTINEL_INVESTIGATION_* variables."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint: AnyHttpUrl | None = None
    api_key: str | None = Field(default=None, min_length=1)
    timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    max_retries: int = Field(default=2, ge=0, le=3)
    backoff_seconds: float = Field(default=0.25, ge=0, le=5)

    @classmethod
    def from_environment(cls) -> "InvestigationProviderSettings":
        """Load settings without exposing secrets in source control."""

        endpoint = os.getenv("SENTINEL_INVESTIGATION_ENDPOINT")
        api_key = os.getenv("SENTINEL_INVESTIGATION_API_KEY")
        timeout_seconds = os.getenv("SENTINEL_INVESTIGATION_TIMEOUT_SECONDS", "10")
        max_retries = os.getenv("SENTINEL_INVESTIGATION_MAX_RETRIES", "2")
        backoff_seconds = os.getenv("SENTINEL_INVESTIGATION_BACKOFF_SECONDS", "0.25")
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )

    def build_provider(self) -> HttpInvestigationProvider | None:
        """Build the adapter only when an endpoint is explicitly configured."""

        if self.endpoint is None:
            return None
        return HttpInvestigationProvider(
            HttpProviderSettings(
                endpoint=self.endpoint,
                api_key=self.api_key,
                timeout_seconds=self.timeout_seconds,
                max_retries=self.max_retries,
                backoff_seconds=self.backoff_seconds,
            )
        )
