# Sequence-to-incident integration

The detection pipeline can optionally receive a `FiniteStateSequenceMatcher`. Completed
`SequenceMatch` records are projected into the existing `Incident` contract through
`IncidentAggregator.add_sequences`.

- Sequence incidents use the deterministic fingerprint `sequence:<signature_id>:<actor_id>`.
- The incident preserves every event ID and step evidence from the completed sequence.
- Sequence version is represented in `rule_ids` as `sequence:<signature_id>:v<version>`.
- Replays are ignored using the signature version and complete event-ID tuple.
- Existing rule and anomaly detection remains unchanged when no sequence matcher is supplied.

This keeps rule, behavioral, and sequence signals on one incident projection while preserving
their source-specific evidence and replay semantics.
