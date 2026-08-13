# Baseline-relative anomaly scoring

Phase 4 Milestone 3 adds a deterministic anomaly score over entity baselines.

For each feature present in both the vector and baseline:

```text
z = (observed - baseline_mean) / baseline_standard_deviation
```

Zero-variance features receive a z-score of zero. The event score is the maximum absolute z-score, and the top three contributors are retained in descending absolute deviation order. An event is marked anomalous only when the score reaches the configured threshold and the baseline has enough observations.

This is an explainable statistical baseline, not yet an Isolation Forest or autoencoder. Later model milestones can emit the same `AnomalyScore` contract.
