# Attack-path assessment

Phase 3 Milestone 5 adds an explainable assessment on top of the weighted shortest-path result.

## Score model

The current heuristic is:

```text
risk_score = min(
    100,
    0.70 * target_criticality
    + min(30, privilege_edge_count * 10)
    + min(20, max(0, 20 - total_path_cost * 2))
)
```

The output preserves all three components, the selected node path, edge path, relationship types, and total traversal cost. This makes the score auditable and prevents a single opaque number from becoming the only explanation.

An unreachable target has no attack-path evidence and receives a score of zero. Missing nodes fail explicitly. This is a graph-risk heuristic, not the final incident risk engine; anomaly scores, sequence confidence, asset exposure, and data sensitivity will be added later.
