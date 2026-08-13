from pathlib import Path

from sentinel_sequence.loader import load_sequences


def test_default_sequence_configuration_loads() -> None:
    signatures = load_sequences(Path("config/sequences/default.json"))

    assert len(signatures) == 1
    assert signatures[0].signature_id == "credential_attack"
    assert [step.step_id for step in signatures[0].steps] == [
        "failed_login",
        "successful_login",
        "privilege_change",
    ]


def test_sequence_loader_rejects_invalid_json_shape(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")

    try:
        load_sequences(path)
    except ValueError:
        return
    raise AssertionError("invalid sequence configuration was accepted")
