"""Dependency-free metrics for sequence correlation."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class SequenceMetrics:
    """Thread-safe counters and latency aggregates for sequence matching."""

    events_processed: int = 0
    duplicate_events: int = 0
    late_events: int = 0
    matches_completed: int = 0
    states_evicted: int = 0
    total_latency_ms: float = 0.0
    peak_active_states: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def observe(
        self,
        *,
        latency_ms: float,
        completed: int,
        late: bool,
        evicted: int,
        active_states: int,
    ) -> None:
        if latency_ms < 0 or completed < 0 or evicted < 0 or active_states < 0:
            raise ValueError("sequence metric values cannot be negative")
        with self._lock:
            self.events_processed += 1
            self.late_events += int(late)
            self.matches_completed += completed
            self.states_evicted += evicted
            self.total_latency_ms += latency_ms
            self.peak_active_states = max(self.peak_active_states, active_states)

    def observe_duplicate(self) -> None:
        with self._lock:
            self.duplicate_events += 1

    def prometheus(self) -> str:
        """Render sequence counters and average processing latency."""

        with self._lock:
            average = (
                self.total_latency_ms / self.events_processed if self.events_processed else 0.0
            )
            lines = [
                "# TYPE sentinel_sequence_events_processed_total counter",
                f"sentinel_sequence_events_processed_total {self.events_processed}",
                "# TYPE sentinel_sequence_duplicate_events_total counter",
                f"sentinel_sequence_duplicate_events_total {self.duplicate_events}",
                "# TYPE sentinel_sequence_late_events_total counter",
                f"sentinel_sequence_late_events_total {self.late_events}",
                "# TYPE sentinel_sequence_matches_completed_total counter",
                f"sentinel_sequence_matches_completed_total {self.matches_completed}",
                "# TYPE sentinel_sequence_states_evicted_total counter",
                f"sentinel_sequence_states_evicted_total {self.states_evicted}",
                "# TYPE sentinel_sequence_process_latency_ms_sum counter",
                f"sentinel_sequence_process_latency_ms_sum {self.total_latency_ms}",
                "# TYPE sentinel_sequence_process_latency_ms_average gauge",
                f"sentinel_sequence_process_latency_ms_average {average}",
                "# TYPE sentinel_sequence_active_states_peak gauge",
                f"sentinel_sequence_active_states_peak {self.peak_active_states}",
            ]
            return "\n".join(lines) + "\n"


default_metrics = SequenceMetrics()
