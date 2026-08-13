import json
from pathlib import Path

from sentinel_detection.models import RuleCondition
from sentinel_sequence.models import SequenceSignature, SequenceStep


def test_sequence_signature_is_versioned_and_bounded() -> None:
    schema = json.loads(Path("schemas/sequence-signature.schema.json").read_text(encoding="utf-8"))
    signature = SequenceSignature(
        signature_id="credential_attack",
        name="Credential attack",
        description="Failed logins followed by a successful login.",
        steps=(
            SequenceStep(
                step_id="failed_login",
                conditions=(RuleCondition(field="action", operator="eq", value="login"),),
            ),
            SequenceStep(
                step_id="successful_login",
                conditions=(
                    RuleCondition(field="action", operator="eq", value="login"),
                    RuleCondition(field="result", operator="eq", value="success"),
                ),
            ),
        ),
        window_seconds=300,
        severity="high",
    )

    assert set(schema["required"]).issubset(signature.model_dump())
    assert signature.version == 1
    assert signature.window_seconds == 300


def test_sequence_signature_rejects_single_step_or_unbounded_window() -> None:
    try:
        SequenceSignature(
            signature_id="single_step",
            name="Invalid",
            description="Invalid signature",
            steps=(
                SequenceStep(
                    step_id="only_step",
                    conditions=(RuleCondition(field="action", operator="eq", value="login"),),
                ),
            ),
            window_seconds=0,
            severity="low",
        )
    except ValueError:
        return
    raise AssertionError("invalid sequence signature was accepted")
