from sentinel_ingestion.enricher import enrich
from sentinel_ingestion.normalizer import normalize

RAW_EVENT = {
    "timestamp": "2026-08-12T12:00:00Z",
    "user_id": "user-42",
    "principal_type": "user",
    "ip": "192.0.2.10",
    "operation": "role_change",
    "target": "billing-admin",
    "status": "denied",
    "request_id": "req-123",
}


def test_normalization_maps_aliases_and_derives_id() -> None:
    first = normalize(RAW_EVENT, source="iam")
    second = normalize(RAW_EVENT, source="iam")

    assert first == second
    assert first.actor_id == "user-42"
    assert first.action == "role_change"
    assert first.result == "failure"
    assert first.severity == "high"
    assert first.attributes == {"request_id": "req-123"}


def test_enrichment_adds_explainable_signals() -> None:
    event = enrich(normalize(RAW_EVENT, source="iam"))

    assert event.attributes["derived"] == {
        "is_authentication": False,
        "is_privilege_change": True,
        "is_data_movement": False,
        "is_failure": True,
    }
