# Sequence correlation

Phase 5 begins with a versioned finite-state sequence contract.

Each signature contains at least two ordered steps, data-only conditions, a bounded event-time window, optional allowed lateness, and a severity. A completed `SequenceMatch` preserves the actor, exact event IDs, timestamps, and step evidence required for incident investigation.

The runtime FSM, sliding-window state, event-time watermarks, timeout behavior, and prefix-sharing automata will be implemented in later Phase 5 milestones.
