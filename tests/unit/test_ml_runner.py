from pathlib import Path

from sentinel_ml.runner import load_labeled_fixture, run_fixture

FIXTURE = Path("tests/fixtures/behavioral_evaluation.jsonl")


def test_fixture_loader_and_runner_are_reproducible() -> None:
    samples = load_labeled_fixture(FIXTURE)
    first = run_fixture(FIXTURE, training_count=2)
    second = run_fixture(FIXTURE, training_count=2)

    assert len(samples) == 4
    assert first == second
    assert first.training_sample_count == 2
    assert first.evaluation_sample_count == 2
    assert first.comparison.results[0].estimator_name == "z_score_baseline"


def test_runner_rejects_invalid_split() -> None:
    try:
        run_fixture(FIXTURE, training_count=4)
    except ValueError as error:
        assert "training_count" in str(error)
        return
    raise AssertionError("invalid training split did not fail")
