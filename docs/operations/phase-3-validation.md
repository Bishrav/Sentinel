# Phase 3 validation

Phase 3 graph capabilities are validated at the focused algorithm level:

- graph contracts reject invalid node and edge values;
- event projection creates stable actor, resource, IP, and relationship entities;
- replayed event IDs do not duplicate graph data;
- BFS and DFS traversal are deterministic and filterable;
- Dijkstra selects confidence-weighted paths;
- attack-path assessment preserves evidence and score components;
- centrality identifies high-degree choke points;
- Tarjan SCC analysis identifies privilege loops;
- graph diffs identify newly exposed assets.

The local environment currently does not include `uv` or `pytest`, so the checks available to the agent execute the same test functions directly. GitHub Actions remains the authoritative environment for the configured Ruff, mypy, pytest, and coverage commands.
