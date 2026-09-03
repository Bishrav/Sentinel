from pathlib import Path

from sentinel_api.demo import replay_failed_login

FIXTURE = Path("tests/fixtures/failed_login_replay.jsonl")


def test_failed_login_replay_returns_investigation_packet() -> None:
    result = replay_failed_login(FIXTURE)

    assert result["deterministic"] is True
    assert result["incident"]["fingerprint"] == "sequence:credential_attack:alice"
    assert result["incident"]["risk_score"] is not None
    assert result["risk_explanation"]["assessment"]["components"]["sequence"] == 20.0
    assert result["investigation_response"]["hypotheses"] == []


def test_failed_login_replay_is_byte_stable() -> None:
    assert replay_failed_login(FIXTURE) == replay_failed_login(FIXTURE)
