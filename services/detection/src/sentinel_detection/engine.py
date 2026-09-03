"""Safe declarative rule evaluation over canonical security events."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from sentinel_ingestion.models import SecurityEvent

from .models import DetectionRule, RuleCondition, RuleMatch

_MISSING = object()


def _event_data(event: SecurityEvent) -> dict[str, Any]:
    return event.model_dump(mode="python")


def _resolve(data: Mapping[str, Any], field: str) -> Any:
    """Resolve a dotted path from event fields or the attributes bag."""

    current: Any = data
    parts = field.split(".")
    if parts[0] not in data and parts[0] not in {"attributes", "derived"}:
        current = data.get("attributes", _MISSING)
    for part in parts:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def _compare(condition: RuleCondition, actual: Any) -> bool:
    expected = condition.value
    if condition.operator == "exists":
        return bool((actual is not _MISSING) == bool(expected if expected is not None else True))
    if actual is _MISSING:
        return condition.operator == "neq"
    if condition.operator == "eq":
        return bool(actual == expected)
    if condition.operator == "neq":
        return bool(actual != expected)
    if condition.operator == "in":
        return (
            isinstance(expected, Collection)
            and not isinstance(expected, (str, bytes))
            and actual in expected
        )
    if condition.operator == "not_in":
        return (
            isinstance(expected, Collection)
            and not isinstance(expected, (str, bytes))
            and actual not in expected
        )
    if condition.operator == "contains":
        if isinstance(actual, (str, bytes, Collection)):
            return expected in actual
        return False
    if condition.operator == "regex":
        return (
            isinstance(actual, str)
            and isinstance(expected, str)
            and re.search(expected, actual) is not None
        )
    try:
        if condition.operator == "gt":
            return bool(actual > expected)
        if condition.operator == "gte":
            return bool(actual >= expected)
        if condition.operator == "lt":
            return bool(actual < expected)
        if condition.operator == "lte":
            return bool(actual <= expected)
    except TypeError:
        return False
    return False


class RuleEngine:
    """Evaluate immutable rules without executing rule-provided code."""

    def __init__(self, rules: Sequence[DetectionRule]) -> None:
        self._rules = tuple(rules)

    def evaluate(self, event: SecurityEvent) -> list[RuleMatch]:
        data = _event_data(event)
        matches: list[RuleMatch] = []
        for rule in self._rules:
            if not rule.enabled:
                continue
            results = [
                _compare(condition, _resolve(data, condition.field))
                for condition in rule.conditions
            ]
            matched = all(results) if rule.match_mode == "all" else any(results)
            if not matched:
                continue
            evidence = {
                condition.field: _resolve(data, condition.field)
                for condition, result in zip(rule.conditions, results, strict=True)
                if result
            }
            # Keep the fingerprint independent of the rule so multiple signals
            # about the same actor/resource become one explainable incident.
            fingerprint = f"{event.actor_id}:{event.resource}"
            matches.append(
                RuleMatch(
                    rule_id=rule.rule_id,
                    rule_version=rule.version,
                    event_id=event.event_id,
                    matched_at=event.timestamp,
                    severity=rule.severity,
                    evidence=evidence,
                    fingerprint=fingerprint,
                )
            )
        return matches
