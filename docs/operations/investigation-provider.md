# Investigation provider configuration

Provider mode is disabled by default. The API uses the deterministic workflow unless `SENTINEL_INVESTIGATION_ENDPOINT` is set.

Optional environment variables:

```text
SENTINEL_INVESTIGATION_ENDPOINT=https://provider.example.com/investigate
SENTINEL_INVESTIGATION_API_KEY=<secret>
SENTINEL_INVESTIGATION_TIMEOUT_SECONDS=10
SENTINEL_INVESTIGATION_MAX_RETRIES=2
SENTINEL_INVESTIGATION_BACKOFF_SECONDS=0.25
```

The API constructs the HTTP adapter at process startup. Provider requests use the typed investigation contract. A provider response that cites evidence outside the request boundary is rejected. Transient transport failures, HTTP 408/429, and 5xx responses receive bounded exponential-backoff retries. Malformed responses, non-retryable 4xx responses, exhausted retries, and grounding failures return HTTP `502`; an unconfigured provider request returns HTTP `501`.

No endpoint or credential is stored in the repository. Configure secrets through the deployment platform’s environment/secret manager.
