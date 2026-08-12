# ADR 0002: Use declarative rules with replay-safe incident aggregation

- Status: Accepted
- Date: 2026-08-12

## Context

Phase 2 needs known-pattern detection and basic incident aggregation without coupling detection logic to a particular event source. Security decisions must be explainable, testable, and safe to replay.

## Decision

- Represent rules as validated JSON data using the `DetectionRule` contract.
- Support a bounded set of comparison operators; never execute rule-provided code.
- Emit `RuleMatch` records containing the rule version, event ID, matched fields, and fingerprint.
- Group matches by actor/resource fingerprint into `Incident` projections.
- Deduplicate replayed matches using `(rule_id, event_id)`.
- Derive incident IDs deterministically with UUID5.
- Keep the first implementation in memory; introduce a durable incident store when the service integration and PostgreSQL schema are defined.

## Consequences

Rules can be reviewed and changed independently of code, and every match carries evidence for investigation. The initial actor/resource fingerprint is intentionally simple and may group events that require a later time-window or graph-aware strategy. That limitation is explicit and will be measured before production use.
