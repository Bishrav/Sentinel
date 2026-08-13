# Model persistence and versioning

Phase 4 Milestone 9 persists a fitted Isolation Forest as a two-file artifact:

```text
artifact/
├── model.joblib
└── manifest.json
```

The manifest records the model version, feature ordering, training count, contamination, random state, training timestamp, and SHA-256 checksum. Loading verifies the checksum before deserializing the model.

Only artifacts produced by a trusted Sentinel training pipeline should be loaded because joblib deserialization is not safe for untrusted files.
