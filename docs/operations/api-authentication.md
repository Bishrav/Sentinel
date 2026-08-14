# API authentication and roles

Phase 6 adds an opt-in Bearer API-key boundary for investigator routes. Configure keys through the deployment secret manager:

```text
SENTINEL_API_KEYS=investigator-key:investigator,operator-key:operator,admin-key:admin
```

When configured:

- `investigator` can list incidents, inspect incidents, and submit investigation requests.
- `operator` can do all investigator actions and attach risk assessments.
- `admin` can do all operator actions.

Health and metrics remain available for deployment probes. When no keys are configured, authentication is disabled for local development only; production deployments must provide `SENTINEL_API_KEYS` through a secret manager.
