# Registered-baseline scoring API

The serving layer can score vectors against a process-local baseline registry:

```text
POST /v1/anomaly/score/{entity_id}?threshold=3
```

Baselines are loaded from trusted JSON artifacts with SHA-256 manifest verification, then registered by entity ID. Unknown entities return `404`; vector/baseline mismatches return `422`.

The registry is intentionally process-local for this milestone. A later operations milestone can load artifacts during service startup and replace the registry with a durable artifact/catalog integration.
