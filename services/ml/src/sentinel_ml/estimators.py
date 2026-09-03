"""Estimator adapters for behavioral anomaly detection."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from .models import (
    BehavioralFeatureVector,
    EstimatorAnomalyScore,
    EstimatorMetadata,
    ModelArtifactManifest,
)


class IsolationForestEstimator:
    """Small lifecycle-safe adapter around scikit-learn Isolation Forest."""

    def __init__(
        self,
        *,
        contamination: float = 0.05,
        random_state: int = 42,
        n_estimators: int = 100,
        model_version: str = "1.0.0",
    ) -> None:
        if not 0.0 < contamination < 0.5:
            raise ValueError("contamination must be between 0 and 0.5")
        if n_estimators < 1:
            raise ValueError("n_estimators must be positive")
        if not model_version.strip():
            raise ValueError("model_version must not be empty")
        self.contamination = contamination
        self.random_state = random_state
        self.n_estimators = n_estimators
        self.model_version = model_version
        self._model = None
        self._feature_names: tuple[str, ...] = ()
        self._observation_count = 0
        self._trained_at: datetime | None = None

    @property
    def metadata(self) -> EstimatorMetadata | None:
        """Return fitted metadata, or ``None`` before fitting."""

        if self._model is None:
            return None
        return EstimatorMetadata(
            estimator_name="isolation_forest",
            feature_names=self._feature_names,
            observation_count=self._observation_count,
            contamination=self.contamination,
            random_state=self.random_state,
            model_version=self.model_version,
            trained_at=self._trained_at or datetime.now(timezone.utc),
        )

    def fit(self, vectors: Sequence[BehavioralFeatureVector]) -> EstimatorMetadata:
        """Fit on vectors with a stable, alphabetically ordered feature layout."""

        if len(vectors) < 2:
            raise ValueError("at least two vectors are required to fit")
        entity_ids = {vector.entity_id for vector in vectors}
        if len(entity_ids) != 1:
            raise ValueError("an estimator must be fitted for one entity")
        feature_names = tuple(sorted(vectors[0].features))
        if not feature_names or any(
            tuple(sorted(vector.features)) != feature_names for vector in vectors
        ):
            raise ValueError("all vectors must have the same feature names")
        try:
            from sklearn.ensemble import IsolationForest
        except ImportError as error:
            raise RuntimeError("scikit-learn is required for IsolationForestEstimator") from error
        matrix = [[vector.features[name] for name in feature_names] for vector in vectors]
        self._model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=self.n_estimators,
        ).fit(matrix)
        self._feature_names = feature_names
        self._observation_count = len(vectors)
        self._trained_at = datetime.now(timezone.utc)
        return self.metadata  # type: ignore[return-value]

    def save(self, artifact_dir: str | Path) -> ModelArtifactManifest:
        """Persist the fitted model and integrity manifest to a directory."""

        if self._model is None or self.metadata is None:
            raise RuntimeError("estimator must be fitted before saving")
        try:
            import joblib
        except ImportError as error:
            raise RuntimeError("joblib is required for model persistence") from error
        directory = Path(artifact_dir)
        directory.mkdir(parents=True, exist_ok=True)
        model_path = directory / "model.joblib"
        manifest_path = directory / "manifest.json"
        joblib.dump(self._model, model_path)
        digest = sha256(model_path.read_bytes()).hexdigest()
        manifest = ModelArtifactManifest(
            artifact_name=model_path.name,
            artifact_sha256=digest,
            metadata=self.metadata,
        )
        manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest

    @classmethod
    def load(cls, artifact_dir: str | Path) -> "IsolationForestEstimator":
        """Restore a model after verifying its manifest checksum.

        Only load artifacts produced by a trusted Sentinel training pipeline;
        joblib deserialization can execute code from a malicious artifact.
        """

        try:
            import joblib
        except ImportError as error:
            raise RuntimeError("joblib is required for model persistence") from error
        directory = Path(artifact_dir)
        manifest = ModelArtifactManifest.model_validate_json(
            (directory / "manifest.json").read_text(encoding="utf-8")
        )
        model_path = directory / manifest.artifact_name
        if sha256(model_path.read_bytes()).hexdigest() != manifest.artifact_sha256:
            raise ValueError("model artifact checksum does not match manifest")
        estimator = cls(
            contamination=manifest.metadata.contamination,
            random_state=manifest.metadata.random_state,
            model_version=manifest.metadata.model_version,
        )
        estimator._model = joblib.load(model_path)
        estimator._feature_names = manifest.metadata.feature_names
        estimator._observation_count = manifest.metadata.observation_count
        estimator._trained_at = manifest.metadata.trained_at
        return estimator

    def score(self, vector: BehavioralFeatureVector) -> EstimatorAnomalyScore:
        """Score one vector; higher scores indicate more anomalous behavior."""

        if self._model is None or self.metadata is None:
            raise RuntimeError("required: estimator must be fitted before scoring")
        if tuple(sorted(vector.features)) != self._feature_names:
            raise ValueError("vector feature names do not match fitted estimator")
        values = [[vector.features[name] for name in self._feature_names]]
        decision_value = float(self._model.decision_function(values)[0])
        score = -decision_value
        prediction = int(self._model.predict(values)[0])
        return EstimatorAnomalyScore(
            event_id=vector.event_id,
            entity_id=vector.entity_id,
            score=score,
            is_anomalous=prediction == -1,
            estimator="isolation_forest",
            metadata=self.metadata,
        )
