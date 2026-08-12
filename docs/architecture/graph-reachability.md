# Graph reachability

Phase 3 Milestone 3 adds directed BFS and DFS traversal over immutable `ThreatGraphSnapshot` values.

## Behavior

- Traversal starts from an existing node; missing sources fail explicitly.
- Neighbors are sorted by node ID, making traversal output deterministic.
- BFS records shortest unweighted depth from the source.
- DFS provides depth-first exploration for graph inspection.
- Callers may restrict traversal to selected edge types.
- The source is included in `visited_node_ids` and excluded from `reachable_node_ids`.

This milestone answers: “Which entities can this node reach through the selected relationships?” Weighted paths, asset criticality, blast radius, and attack-route scoring are intentionally deferred to later milestones.
