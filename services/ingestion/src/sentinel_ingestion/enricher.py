"""Deterministic derived signals added after normalization."""

from .models import SecurityEvent


def enrich(event: SecurityEvent) -> SecurityEvent:
    """Attach explainable signals used by later detection stages."""

    action = event.action.lower()
    attributes = dict(event.attributes)
    attributes["derived"] = {
        "is_authentication": any(term in action for term in ("login", "logout", "auth")),
        "is_privilege_change": any(
            term in action for term in ("role", "permission", "grant", "revoke")
        ),
        "is_data_movement": any(
            term in action for term in ("export", "download", "read", "transfer")
        ),
        "is_failure": event.result == "failure",
    }
    return event.model_copy(update={"attributes": attributes})
