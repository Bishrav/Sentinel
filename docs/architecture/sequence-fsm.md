# Sequence FSM matching

`FiniteStateSequenceMatcher` consumes canonical `SecurityEvent` objects and evaluates enabled
`SequenceSignature` definitions as ordered finite-state machines.

- Partial state is keyed by `(signature_id, actor_id)`, preventing one actor from completing
  another actor's sequence.
- Every transition reuses the safe declarative detection rule evaluator; sequence steps cannot
  execute arbitrary expressions.
- A partial match expires when its event-time age exceeds `window_seconds`.
- The matcher derives a watermark from the highest observed event time minus each signature's
  `allowed_lateness_seconds`; events older than that watermark are ignored for that signature.
- `max_active_per_actor` bounds retained partial matches by keeping the newest states first.
- Completed matches preserve event IDs, timestamps, step IDs, actor identity, and severity as
  explainable `SequenceMatch` evidence.
- A bounded event-ID cache provides replay protection without allowing deduplication state to grow
  without limit.

This matcher is ready for integration with a stream processor that supplies events in arbitrary
arrival order; durable checkpoints and cross-process state remain deployment concerns.
