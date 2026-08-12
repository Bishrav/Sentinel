# Ingestion replay

Phase 1 uses JSON Lines as the deterministic boundary for source exports and test fixtures. Each line is one source event. The same collector and normalization pipeline can be connected to a live collector later without changing the canonical event contract.

## Fixture replay

The current fixture contains authentication, privilege-change, and data-export events:

```powershell
$env:PYTHONPATH = "services/api/src;services/ingestion/src"
@'
from pathlib import Path
from sentinel_ingestion.collectors import JsonLinesCollector
from sentinel_ingestion.pipeline import ingest
from sentinel_ingestion.transport import InMemoryEventPublisher

publisher = InMemoryEventPublisher()
events = ingest(
    JsonLinesCollector(Path("tests/fixtures/auth_events.jsonl")).collect(),
    source="auth-fixture",
    publisher=publisher,
)
print(f"replayed {len(events)} events")
'@ | python -
```

## Transport behavior

`InMemoryEventPublisher` is used for deterministic tests. `KafkaEventPublisher` writes the JSON representation of each canonical event to a configured Kafka-compatible topic, using `event_id` as the message key. The producer is intentionally behind the `EventPublisher` protocol so downstream services can be tested without a broker.

The canonical event ID is preserved when a source supplies one. If it does not, Sentinel derives a UUID5 from the source name and canonical source payload. Replaying the same record therefore produces the same ID and supports idempotent downstream handling.

## Failure policy

Malformed JSON and records that cannot satisfy the canonical contract fail the current replay operation rather than being silently discarded. A dead-letter policy will be added with the first production collector, when the repository has a defined quarantine destination and operator workflow.
