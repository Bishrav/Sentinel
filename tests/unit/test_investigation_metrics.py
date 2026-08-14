from sentinel_investigation.metrics import ProviderMetrics


def test_provider_metrics_render_requests_failures_and_retries() -> None:
    metrics = ProviderMetrics()
    metrics.observe_request()
    metrics.observe_retry()
    metrics.observe_success(4.0)
    metrics.observe_request()
    metrics.observe_failure(6.0)

    output = metrics.prometheus()

    assert metrics.requests == 2
    assert metrics.successes == 1
    assert metrics.failures == 1
    assert metrics.retries == 1
    assert "sentinel_investigation_provider_retries_total 1" in output
    assert "sentinel_investigation_provider_latency_ms_average 5.0" in output
