# Sequence FSM matching

`FiniteStateSequenceMatcher` consumes canonical `SecurityEvent` objects and evaluates enabled
`SequenceSignature` definitions as ordered finite-state machines.

- Partial state is keyed by `(signature_id, actor_id)`, preventing one actor from completing
  another actor's sequence.
- Every transition reuses the safe declarative detection rule evaluator; sequence steps cannot
  execute arbitrary expressions.
- A partial match expires when its event-time age exceeds `window_seconds`.
- Completed matches preserve event IDs, timestamps, step IDs, actor identity, and severity as
  explainable `SequenceMatch` evidence.
- Event IDs are tracked for replay safety, so re-delivery does not create duplicate transitions.

Allowed-lateness watermarks and bounded state eviction are intentionally separate concerns and
will be added in the next streaming milestone.
