from pathlib import Path

import pytest

from sentinel_ml.estimators import IsolationForestEstimator


def test_unfitted_estimator_cannot_be_persisted(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="fitted"):
        IsolationForestEstimator().save(tmp_path / "artifact")


def test_artifact_persistence_round_trip_when_joblib_is_available(tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    pytest.importorskip("joblib")
    from tests.unit.test_ml_estimators import vector

    estimator = IsolationForestEstimator(n_estimators=10, model_version="1.0.1")
    estimator.fit([vector(index, 10 + index * 0.1) for index in range(1, 8)])
    artifact_dir = tmp_path / "artifact"
    manifest = estimator.save(artifact_dir)
    restored = IsolationForestEstimator.load(artifact_dir)

    assert manifest.metadata.model_version == "1.0.1"
    assert restored.metadata is not None
    assert restored.metadata.feature_names == estimator.metadata.feature_names
    restored_result = restored.score(vector(99, 100)).is_anomalous
    original_result = estimator.score(vector(99, 100)).is_anomalous
    assert restored_result == original_result


def test_tampered_artifact_is_rejected(tmp_path: Path) -> None:
    pytest.importorskip("sklearn")
    pytest.importorskip("joblib")
    from tests.unit.test_ml_estimators import vector

    estimator = IsolationForestEstimator(n_estimators=10)
    estimator.fit([vector(index, 10 + index * 0.1) for index in range(1, 7)])
    artifact_dir = tmp_path / "artifact"
    estimator.save(artifact_dir)
    (artifact_dir / "model.joblib").write_bytes(b"tampered")

    with pytest.raises(ValueError, match="checksum"):
        IsolationForestEstimator.load(artifact_dir)
