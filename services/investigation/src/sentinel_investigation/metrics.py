"""Dependency-free metrics for investigation provider calls."""

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class ProviderMetrics:
    """Thread-safe request, failure, retry, and latency counters."""

    requests: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    total_latency_ms: float = 0.0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def observe_request(self) -> None:
        with self._lock:
            self.requests += 1

    def observe_success(self, latency_ms: float) -> None:
        if latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        with self._lock:
            self.successes += 1
            self.total_latency_ms += latency_ms

    def observe_failure(self, latency_ms: float) -> None:
        if latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        with self._lock:
            self.failures += 1
            self.total_latency_ms += latency_ms

    def observe_retry(self) -> None:
        with self._lock:
            self.retries += 1

    def prometheus(self) -> str:
        with self._lock:
            average = self.total_latency_ms / self.requests if self.requests else 0.0
            lines = [
                "# TYPE sentinel_investigation_provider_requests_total counter",
                f"sentinel_investigation_provider_requests_total {self.requests}",
                "# TYPE sentinel_investigation_provider_successes_total counter",
                f"sentinel_investigation_provider_successes_total {self.successes}",
                "# TYPE sentinel_investigation_provider_failures_total counter",
                f"sentinel_investigation_provider_failures_total {self.failures}",
                "# TYPE sentinel_investigation_provider_retries_total counter",
                f"sentinel_investigation_provider_retries_total {self.retries}",
                "# TYPE sentinel_investigation_provider_latency_ms_average gauge",
                f"sentinel_investigation_provider_latency_ms_average {average}",
            ]
            return "\n".join(lines) + "\n"


default_metrics = ProviderMetrics()
