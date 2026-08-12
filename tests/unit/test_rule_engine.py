from sentinel_ingestion.normalizer import normalize

from sentinel_detection.engine import RuleEngine
from sentinel_detection.loader import load_rules
from sentinel_detection.models import DetectionRule, RuleCondition


def event(**overrides: object):
    raw = {
        "event_id": "12345678-1234-4234-8234-123456789012",
        "timestamp": "2026-08-12T12:00:00Z",
        "actor_id": "user-42",
        "actor_type": "user",
        "action": "login",
        "resource": "identity-provider",
        "result": "failure",
        "source": "test",
    }
    raw.update(overrides)
    return normalize(raw, source="test")


def test_default_rules_match_with_field_evidence() -> None:
    engine = RuleEngine(load_rules("config/rules/default.json"))

    matches = engine.evaluate(event())

    assert [match.rule_id for match in matches] == ["failed_login"]
    assert matches[0].evidence == {"action": "login", "result": "failure"}


def test_nested_attributes_and_numeric_operator_match() -> None:
    engine = RuleEngine(load_rules("config/rules/default.json"))

    matches = engine.evaluate(event(action="export", result="success", bytes=20_000_000))

    assert [match.rule_id for match in matches] == ["large_export"]
    assert matches[0].evidence["attributes.bytes"] == 20_000_000


def test_disabled_and_any_rules_are_supported_without_code_execution() -> None:
    rules = [
        DetectionRule(
            rule_id="disabled_rule",
            name="Disabled",
            description="Should not match",
            severity="low",
            enabled=False,
            conditions=[RuleCondition(field="action", operator="eq", value="login")],
        ),
        DetectionRule(
            rule_id="auth_or_export",
            name="Auth or export",
            description="Matches either event",
            severity="medium",
            match_mode="any",
            conditions=[
                RuleCondition(field="action", operator="eq", value="export"),
                RuleCondition(field="result", operator="eq", value="failure"),
            ],
        ),
    ]

    matches = RuleEngine(rules).evaluate(event())

    assert [match.rule_id for match in matches] == ["auth_or_export"]
