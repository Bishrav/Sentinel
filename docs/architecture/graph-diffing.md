# Permission graph diffing

Phase 3 compares two immutable threat graph snapshots to make permission changes reviewable.

The diff reports added and removed nodes, added and removed edges, and changed edges. An added or changed `can_reach`, `exposed_to`, or `grants` relationship is classified as newly exposing its target node.

The output is sorted by identifier and retains edge IDs so a permission change can be traced back to the graph ingestion event or persistence record that created it.
