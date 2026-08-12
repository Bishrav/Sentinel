# ADR 0001: Establish an event-driven Python service foundation

- Status: Accepted
- Date: 2026-08-12

## Context

Sentinel must correlate security telemetry from multiple sources while keeping critical decisions deterministic, replayable, and observable. The repository is starting from an empty remote, so the first milestone needs a small foundation that can grow into the ingestion and detection pipeline without hiding architectural decisions in ad-hoc scripts.

## Decision

- Use Python 3.12 for the initial API and detection services.
- Use FastAPI for typed HTTP contracts and operational endpoints.
- Use Kafka-compatible Redpanda locally for event transport.
- Use PostgreSQL for transactional records, Redis for hot state, and Neo4j for threat relationships.
- Keep local infrastructure reproducible through Docker Compose.
- Enforce formatting, linting, static typing, and tests in GitHub Actions.
- Keep service code under `services/`, shared contracts under `schemas/`, and operational documentation under `docs/`.

## Consequences

This gives the project a reproducible local environment and visible quality gates early. It also introduces several local dependencies, so later phases must add service-level health checks, integration fixtures, and resource-specific tests rather than assuming that containers being available means the system is correct.

The `/health` endpoint reports process health only. `/ready` represents application readiness and will gain dependency checks when the API begins using external services.
