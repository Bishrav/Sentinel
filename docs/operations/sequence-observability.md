# Sequence observability and performance

Sequence matching records process-level metrics through `SequenceMetrics`. The default collector
is shared by the matcher and API process, so `GET /metrics` includes:

- processed, duplicate, late, and completed-event counters;
- expired-state count and peak active-state gauge;
- total and average processing latency in milliseconds.

`benchmarks/sequence_benchmark.py` provides a dependency-light, deterministic throughput check:

```powershell
$env:PYTHONPATH = "services/ingestion/src;services/detection/src;services/sequence/src"
python benchmarks/sequence_benchmark.py
```

The benchmark reports event count, completed matches, elapsed time, events per second, and average
latency. It is an engineering signal for local comparisons, not a production capacity claim; CI
load tests will add controlled infrastructure and resource measurements later.
