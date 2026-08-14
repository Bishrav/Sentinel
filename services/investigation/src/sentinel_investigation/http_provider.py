"""Vendor-neutral HTTP adapter for investigation providers."""

import json
import time
from collections.abc import Callable
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from .models import InvestigationRequest, InvestigationResponse
from .metrics import ProviderMetrics, default_metrics


class ProviderRequestError(RuntimeError):
    """Raised when an HTTP provider cannot return a valid response."""


class HttpProviderSettings(BaseModel):
    """Safe runtime settings for an external investigation provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    endpoint: AnyHttpUrl
    api_key: str | None = Field(default=None, min_length=1)
    timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    max_retries: int = Field(default=2, ge=0, le=3)
    backoff_seconds: float = Field(default=0.25, ge=0, le=5)


Transport = Callable[[Request, float], bytes]


def _request_bytes(request: Request, timeout: float) -> bytes:
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - configured endpoint
        return response.read()


class HttpInvestigationProvider:
    """Call a provider endpoint that returns an InvestigationResponse JSON object."""

    def __init__(
        self,
        settings: HttpProviderSettings,
        transport: Transport = _request_bytes,
        sleeper: Callable[[float], None] = time.sleep,
        metrics: ProviderMetrics = default_metrics,
    ) -> None:
        self._settings = settings
        self._transport = transport
        self._sleeper = sleeper
        self._metrics = metrics

    def generate(self, request: InvestigationRequest) -> InvestigationResponse:
        started = perf_counter()
        self._metrics.observe_request()
        try:
            response = self._generate(request)
        except ProviderRequestError:
            self._metrics.observe_failure((perf_counter() - started) * 1000)
            raise
        self._metrics.observe_success((perf_counter() - started) * 1000)
        return response

    def _generate(self, request: InvestigationRequest) -> InvestigationResponse:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._settings.api_key:
            headers["Authorization"] = f"Bearer {self._settings.api_key}"
        outbound = Request(
            str(self._settings.endpoint),
            data=json.dumps(request.model_dump(mode="json")).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        for attempt in range(self._settings.max_retries + 1):
            try:
                payload = json.loads(self._transport(outbound, self._settings.timeout_seconds))
                return InvestigationResponse.model_validate(payload)
            except HTTPError as error:
                retryable = error.code == 408 or error.code == 429 or error.code >= 500
                if not retryable:
                    raise ProviderRequestError(
                        f"investigation provider returned HTTP {error.code}"
                    ) from error
                last_error: Exception = error
            except (URLError, TimeoutError, OSError) as error:
                last_error = error
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                raise ProviderRequestError(
                    "investigation provider returned invalid response JSON"
                ) from error

            if attempt >= self._settings.max_retries:
                raise ProviderRequestError(
                    f"investigation provider request failed after {attempt + 1} attempt(s): "
                    f"{last_error}"
                ) from last_error
            self._metrics.observe_retry()
            self._sleeper(self._settings.backoff_seconds * (2**attempt))

        raise AssertionError("provider retry loop exited unexpectedly")
