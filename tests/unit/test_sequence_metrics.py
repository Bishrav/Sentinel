from sentinel_sequence.metrics import SequenceMetrics


def test_sequence_metrics_track_processing_and_render_prometheus() -> None:
    metrics = SequenceMetrics()
    metrics.observe(
        latency_ms=2.5,
        completed=1,
        late=True,
        evicted=2,
        active_states=4,
    )
    metrics.observe_duplicate()

    output = metrics.prometheus()
    assert metrics.events_processed == 1
    assert metrics.duplicate_events == 1
    assert metrics.matches_completed == 1
    assert "sentinel_sequence_late_events_total 1" in output
    assert "sentinel_sequence_active_states_peak 4" in output
