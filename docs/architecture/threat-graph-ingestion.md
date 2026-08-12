# Threat graph ingestion

Phase 3 Milestone 2 projects canonical `SecurityEvent` records into graph entities.

## Projection rules

- Actors become typed nodes such as `user:user-42`, `service:exporter`, or `api:client-7`.
- Resources become typed nodes using the optional `attributes.resource_type`; unknown resource types default to `service` until a richer source mapping exists.
- Source IPs and device IDs become separate nodes when present.
- Actions map to a bounded relationship vocabulary such as `logged_in_from`, `reads`, `writes`, `calls`, `grants`, and `accessed`.
- Every event relationship uses `event:<event_id>` as its edge ID, preserving event provenance and replay identity.

## Idempotency

`InMemoryGraphStore` tracks processed event IDs. Replaying an event returns `False` and does not add duplicate nodes or edges. Snapshots sort nodes and edges by identifier so serialized output is stable for tests and later persistence adapters.

The in-memory store is intentionally limited to local development and tests. A Neo4j adapter belongs in a later milestone after reachability query semantics and transaction boundaries are defined.
