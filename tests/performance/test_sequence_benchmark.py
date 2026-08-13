from benchmarks.sequence_benchmark import run_benchmark


def test_sequence_benchmark_smoke_produces_expected_matches() -> None:
    result = run_benchmark(200)

    assert result["events"] == 200
    assert result["completed_matches"] == 100
    assert result["events_per_second"] > 0
    assert result["average_latency_ms"] > 0
