# ML evaluation runner

Phase 4 Milestone 7 adds `run_fixture`, a reproducible evaluation entry point.

The runner loads labeled JSONL samples, uses the training prefix to build the z-score baseline, evaluates the remaining samples, and attempts to fit Isolation Forest with the same training vectors. If scikit-learn is unavailable, the run records `isolation_forest` in `skipped_estimators` and still returns the baseline metrics.

The fixture is intentionally small and illustrative. It is suitable for checking wiring and reproducibility, not for claiming production model quality.
