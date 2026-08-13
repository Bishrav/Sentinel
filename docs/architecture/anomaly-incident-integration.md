# Anomaly-to-incident integration

Phase 4 now connects ML output to the Phase 2 detection pipeline.

An anomalous `AnomalyScore` becomes a `RuleMatch` with rule ID `behavioral_anomaly`. The match preserves the anomaly score, baseline observation count, top contributors, and per-feature z-score evidence. Severity is `high` by default and becomes `critical` at a score of 10 or higher.

The detection pipeline accepts an optional anomaly scorer. This keeps deterministic rule detection usable by itself while allowing a serving layer to add ML evidence to the same replay-safe incident aggregator.
