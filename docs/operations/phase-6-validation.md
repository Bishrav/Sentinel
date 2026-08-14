# Phase 6 validation and deployment readiness

Phase 6 productionization is implemented as opt-in deployment capabilities so local development remains lightweight.

## Runtime capabilities

- Incident projections can persist to SQLite with WAL mode through `SENTINEL_INCIDENT_DB_PATH`.
- Investigator routes support Bearer API keys and role authorization through `SENTINEL_API_KEYS`.
- The provider adapter activates from `SENTINEL_INVESTIGATION_ENDPOINT` and related settings.
- `/health` remains a liveness probe; `/ready` reports authentication, persistence, and provider mode without exposing secrets.
- `/metrics` reports ML, sequence, and investigation-provider counters.

The repository does not claim a live vendor or production credential. Deployment owners must configure and evaluate their selected provider endpoint through the documented environment contract.

## Phase 6 review boundary

Durable shared-database migrations, centralized secret rotation, and infrastructure-specific deployment manifests are intentionally deployment-owned concerns. The application exposes the interfaces and readiness signals required for those integrations.
