# Strongly connected components

Phase 3 adds deterministic Tarjan SCC analysis for directed threat graphs.

An SCC is cyclic when it contains more than one node or a self-loop. A cyclic component is flagged as a privilege loop when one of its internal edges is `has_role`, `grants`, or `owns`.

The result preserves sorted node IDs and internal edge IDs. Callers can filter the analysis by relationship type, which makes it possible to distinguish ordinary service cycles from privilege escalation loops.
