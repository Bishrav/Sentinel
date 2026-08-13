# Isolation Forest estimator

Phase 4 Milestone 4 adds an optional Isolation Forest adapter behind a typed lifecycle.

The estimator:

- fits one entity at a time;
- requires at least two vectors;
- requires identical feature names for every training vector;
- sorts feature names before constructing the matrix;
- records contamination, random state, feature names, and observation count;
- converts scikit-learn’s decision function into a higher-is-more-anomalous score;
- preserves the existing typed anomaly result boundary.

The statistical z-score baseline remains the explainable reference model. This milestone introduces the estimator implementation only; model quality claims require a labeled evaluation dataset and comparison metrics in a later milestone.
