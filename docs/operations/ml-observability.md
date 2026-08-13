# ML observability

The API exposes dependency-free Prometheus-compatible metrics at:

```text
GET /metrics
```

Current metrics include scoring request count, anomalous result count, total and average scoring latency, and request counts by model label. The collector is thread-safe for the in-process serving milestone; a later deployment milestone can replace it with a shared Prometheus client and scrape configuration.
