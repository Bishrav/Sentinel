"""Small reproducible benchmark for sequence matcher throughput."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from time import perf_counter
from uuid import uuid4

from sentinel_detection.models import RuleCondition
from sentinel_ingestion.models import SecurityEvent
from sentinel_sequence.matcher import FiniteStateSequenceMatcher
from sentinel_sequence.models import SequenceSignature, SequenceStep


def run_benchmark(event_count: int = 10_000) -> dict[str, float | int]:
    """Process a deterministic two-step workload and return throughput evidence."""

    if event_count < 2:
        raise ValueError("event_count must be at least 2")
    signature = SequenceSignature(
        signature_id="benchmark_sequence",
        name="Benchmark sequence",
        description="Two-step benchmark workload.",
        steps=(
            SequenceStep(
                step_id="start",
                conditions=(RuleCondition(field="action", operator="eq", value="start"),),
            ),
            SequenceStep(
                step_id="finish",
                conditions=(RuleCondition(field="action", operator="eq", value="finish"),),
            ),
        ),
        window_seconds=300,
        severity="low",
    )
    matcher = FiniteStateSequenceMatcher((signature,))
    start_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    started = perf_counter()
    completed = 0
    for index in range(event_count):
        event = SecurityEvent(
            event_id=uuid4(),
            timestamp=start_time + timedelta(seconds=index),
            actor_id=f"actor-{index // 2}",
            actor_type="user",
            action="start" if index % 2 == 0 else "finish",
            resource="benchmark",
            result="success",
            severity="low",
            source="benchmark",
        )
        completed += len(matcher.process(event))
    elapsed = perf_counter() - started
    return {
        "events": event_count,
        "completed_matches": completed,
        "elapsed_seconds": elapsed,
        "events_per_second": event_count / elapsed if elapsed else 0.0,
        "average_latency_ms": (elapsed * 1000) / event_count,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2))
