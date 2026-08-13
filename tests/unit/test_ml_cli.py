import json
from pathlib import Path

from sentinel_ml.cli import main


FIXTURE = Path("tests/fixtures/behavioral_evaluation.jsonl")


def test_cli_writes_machine_readable_report(tmp_path, monkeypatch) -> None:
    output = tmp_path / "evaluation.json"
    monkeypatch.setattr(
        "sys.argv",
        ["sentinel-ml-evaluate", str(FIXTURE), "--training-count", "2", "--output", str(output)],
    )

    assert main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["training_sample_count"] == 2
    assert report["evaluation_sample_count"] == 2
    assert report["comparison"]["results"][0]["estimator_name"] == "z_score_baseline"
