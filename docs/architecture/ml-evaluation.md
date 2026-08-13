# Behavioral ML evaluation

Phase 4 Milestone 5 adds a reproducible binary evaluation harness.

Each `LabeledFeatureVector` carries a known benign/anomalous label. A predictor is evaluated against those labels and produces confusion counts plus precision, recall, and F1. Zero-denominator metrics are defined as zero rather than producing undefined values.

The repository includes a small JSONL fixture for repeatable development checks. It is intentionally not presented as a production-quality dataset; future work should expand it with controlled attacks, benign traffic, time-based splits, and documented class balance.
