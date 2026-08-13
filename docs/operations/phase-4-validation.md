# Phase 4 validation and failure modes

Phase 4 now covers feature extraction, online baselines, statistical anomaly scoring, Isolation Forest integration, labeled evaluation, model comparison, artifact persistence, API serving, incident integration, and ML observability.

## Evaluation evidence

- `tests/fixtures/behavioral_evaluation.jsonl` is a small wiring fixture.
- `tests/fixtures/behavioral_evaluation_extended.jsonl` adds benign variation and multiple labeled anomalies for repeatable local evaluation.
- The CLI reports confusion counts, precision, recall, F1, selected model, and skipped estimators.
- Training samples precede evaluation samples to prevent evaluation data from contaminating the baseline.

## Known failure modes

- A new entity has no meaningful baseline and must not be treated as anomalous solely because it is unseen.
- Zero-variance features produce a z-score of zero in the statistical detector.
- Baselines and models are feature-order-sensitive; artifact metadata validates the expected ordering.
- Isolation Forest quality depends on representative training data and contamination configuration.
- The current in-process registry and metrics collector are not durable across restarts.
- Joblib artifacts must only be loaded from trusted sources because deserialization can execute code.

Full dependency-backed validation remains a GitHub Actions responsibility when `uv`, pytest, mypy, Ruff, scikit-learn, and joblib are installed.
