# Model comparison

Phase 4 Milestone 6 adds a common comparison API for anomaly detectors.

`compare_baseline` evaluates the current z-score detector. `compare_detectors` accepts named predictors, evaluates each against the same labeled samples, and selects the first model with the best F1, then recall, then precision. This keeps model selection reproducible and makes the comparison criteria explicit.

Isolation Forest can be passed as a predictor after fitting, while environments without scikit-learn can still run the statistical baseline and comparison tests.
