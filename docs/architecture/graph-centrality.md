# Graph centrality

Phase 3 centrality analysis currently provides deterministic directed degree centrality.

For each node it reports incoming degree, outgoing degree, total degree, and a normalized score:

```text
normalized_score = total_degree / (2 * (node_count - 1))
```

The result is sorted by node ID and can be restricted to selected edge types. High-degree nodes are useful candidate choke points for later attack-path analysis, but degree centrality alone does not prove that a node is dangerous; criticality, path evidence, and privilege semantics must be considered together.
