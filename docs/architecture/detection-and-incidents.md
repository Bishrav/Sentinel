# Detection and incidents

Phase 2 separates three concerns:

1. `RuleEngine` evaluates immutable, declarative `DetectionRule` objects.
2. `RuleMatch` records the exact event, rule version, matched fields, and deterministic fingerprint.
3. `IncidentAggregator` groups related matches into a replay-safe incident projection.

## Rule evaluation

Rules are JSON configuration, not executable code. Supported operators are:

`eq`, `neq`, `in`, `not_in`, `contains`, `regex`, `exists`, `gt`, `gte`, `lt`, and `lte`.

Fields can refer to canonical event properties such as `action` and `result`, or nested attributes such as `attributes.bytes`. A match stores only the fields whose predicates passed, making the reason for a detection inspectable.

Disabled rules are skipped. Invalid rules fail validation when loaded, before they enter the evaluation path.

## Incident grouping

The initial fingerprint is:

```text
actor_id + ":" + resource
```

The rule ID is intentionally excluded. A failed login followed by a privilege change for the same actor and resource can therefore become one incident with multiple rule IDs and an escalated severity.

The aggregator deduplicates on `(rule_id, event_id)`. Replaying the same event does not increase `match_count`, duplicate evidence, or create a second incident. Incident IDs are UUID5 values derived from the fingerprint, so the same fingerprint produces the same incident identity across deterministic replays.

## Current rules

`config/rules/default.json` currently contains:

- `failed_login` — failed authentication, medium severity;
- `privilege_change` — role or permission change, high severity;
- `large_export` — export of at least 10 MiB, high severity.

These are intentionally small baseline rules. Stateful thresholds, ordered sequences, and model-generated signals belong in later phases and will feed the same `RuleMatch` and `Incident` contracts.
