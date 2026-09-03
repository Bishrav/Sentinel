# Failed-login investigation demo API

## `GET /v1/demo/replay/failed-login`

This protected, deterministic endpoint replays `tests/fixtures/failed_login_replay.jsonl` through normalization, the configured `credential_attack` finite-state sequence, risk scoring, and the deterministic investigation workflow.

Authentication requires an investigator-level bearer key when `SENTINEL_API_KEYS` is configured. The response contains:

- `normalized_events`: canonical `SecurityEvent` records;
- `incident`: replay-safe incident projection and sequence evidence;
- `risk_explanation`: versioned inputs and weighted risk components;
- `investigation_response`: cited evidence and safe runbook recommendations.

The deterministic workflow intentionally returns no AI-generated hypothesis. Provider mode remains a separate optional endpoint and rejects ungrounded citations.
