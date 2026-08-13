# Anomaly scoring API

The API exposes baseline-relative scoring at:

```text
POST /v1/anomaly/score
```

The request includes a typed behavioral feature vector, its entity baseline, and an optional positive threshold. The response contains the anomaly score, boolean decision, per-feature z-scores, top contributors, and baseline observation count.

This endpoint currently accepts the baseline explicitly so the contract can be tested without a persistence dependency. A later serving milestone can load versioned baseline/model artifacts from a trusted store.
