# Investigation provider configuration

Provider mode is disabled by default. The API uses the deterministic workflow unless `SENTINEL_INVESTIGATION_ENDPOINT` is set.

Optional environment variables:

```text
SENTINEL_INVESTIGATION_ENDPOINT=https://provider.example.com/investigate
SENTINEL_INVESTIGATION_API_KEY=<secret>
SENTINEL_INVESTIGATION_TIMEOUT_SECONDS=10
```

The API constructs the HTTP adapter at process startup. Provider requests use the typed investigation contract. A provider response that cites evidence outside the request boundary is rejected. Transport failures and grounding failures return HTTP `502`; an unconfigured provider request returns HTTP `501`.

No endpoint or credential is stored in the repository. Configure secrets through the deployment platform’s environment/secret manager.
