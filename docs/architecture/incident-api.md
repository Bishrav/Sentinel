# Incident investigation API

The API exposes the current in-process `IncidentAggregator` projection through two read-only
endpoints:

- `GET /v1/incidents` returns `{items, total}` for the current incident collection.
- `GET /v1/incidents/{fingerprint}` returns one deterministic incident or `404`.

Responses use the versioned `Incident` contract, including severity, event IDs, source rule IDs,
actor/resource scope, and explainable evidence. The store is intentionally process-local in this
milestone; durable persistence and authenticated investigator workflows remain deployment work.
