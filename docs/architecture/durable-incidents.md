# Durable incident persistence

Phase 6 adds an optional `SqliteIncidentStore` behind the `IncidentStore` protocol. The aggregator loads existing projections at startup and upserts the complete incident JSON after every mutation. SQLite WAL mode permits concurrent readers while the service writes projections.

Set `SENTINEL_INCIDENT_DB_PATH` to activate persistence. If the variable is absent, the API keeps the in-memory store for lightweight local development. The current adapter is intended for a single-service deployment; a shared database adapter and migration policy belong to later production hardening.
