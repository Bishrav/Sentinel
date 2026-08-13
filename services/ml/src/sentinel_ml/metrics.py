"""Small dependency-free metrics collector for ML scoring paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from .models import AnomalyScore


@dataclass
class AnomalyMetrics:
    """Thread-safe counters and latency aggregates for anomaly scoring."""

    score_requests: int = 0
    anomalous_requests: int = 0
    total_latency_ms: float = 0.0
    _by_model: dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def observe(
        self,
        score: AnomalyScore,
        latency_ms: float,
        *,
        model: str = "z_score_baseline",
    ) -> None:
        if latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        with self._lock:
            self.score_requests += 1
            self.anomalous_requests += int(score.is_anomalous)
            self.total_latency_ms += latency_ms
            self._by_model[model] = self._by_model.get(model, 0) + 1

    def prometheus(self) -> str:
        """Render counters and average latency in Prometheus text format."""

        with self._lock:
            average = self.total_latency_ms / self.score_requests if self.score_requests else 0.0
            lines = [
                "# TYPE sentinel_ml_score_requests_total counter",
                f"sentinel_ml_score_requests_total {self.score_requests}",
                "# TYPE sentinel_ml_anomalous_requests_total counter",
                f"sentinel_ml_anomalous_requests_total {self.anomalous_requests}",
                "# TYPE sentinel_ml_score_latency_ms_sum counter",
                f"sentinel_ml_score_latency_ms_sum {self.total_latency_ms}",
                "# TYPE sentinel_ml_score_latency_ms_average gauge",
                f"sentinel_ml_score_latency_ms_average {average}",
            ]
            for model, count in sorted(self._by_model.items()):
                lines.append(
                    f'sentinel_ml_score_requests_by_model_total{{model="{model}"}} {count}'
                )
            return "\n".join(lines) + "\n"
