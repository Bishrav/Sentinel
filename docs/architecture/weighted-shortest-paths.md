# Weighted shortest paths

Phase 3 Milestone 4 adds deterministic Dijkstra shortest-path analysis.

## Cost model

Each directed edge has a confidence in the range `[0, 1]`. The traversal cost is:

```text
cost(edge) = 1 / max(confidence, 0.01)
```

A high-confidence relationship costs approximately one hop. Lower-confidence relationships cost more, so the selected route prefers stronger evidence while still allowing uncertain edges when they are the only connection.

## Behavior

- Missing source or target nodes fail explicitly.
- Valid but disconnected targets return `None`.
- Edge-type filters restrict the route to selected relationship kinds.
- Equal-cost traversal ordering is deterministic by target node ID and edge ID.
- The result contains node IDs, edge IDs, edge types, and total cost for auditability.

This milestone measures relationship confidence only. Asset criticality, privilege changes, blast radius, and attack-route risk belong to the later attack-path and risk-engine milestones.
