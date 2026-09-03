"""Replay-safe online entity baseline statistics."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from hashlib import sha256
from pathlib import Path

from .models import BaselineArtifactManifest, BehavioralFeatureVector, EntityBaseline


class _RunningFeature:
    def __init__(self) -> None:
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta_after = value - self.mean
        self.m2 += delta * delta_after

    @property
    def standard_deviation(self) -> float:
        if self.count < 2:
            return 0.0
        return float((self.m2 / self.count) ** 0.5)


class OnlineBaselineStore:
    """Maintain per-entity population statistics with event replay protection."""

    def __init__(self) -> None:
        self._features: dict[str, dict[str, _RunningFeature]] = {}
        self._entity_types: dict[str, str] = {}
        self._updated_at: dict[str, datetime] = {}
        self._processed_events: set[str] = set()

    def update(self, vector: BehavioralFeatureVector) -> bool:
        """Apply one vector; return ``False`` when its event was already seen."""

        event_key = str(vector.event_id)
        if event_key in self._processed_events:
            return False
        feature_state = self._features.setdefault(vector.entity_id, {})
        for name, value in vector.features.items():
            feature_state.setdefault(name, _RunningFeature()).update(value)
        self._entity_types[vector.entity_id] = vector.entity_type
        self._updated_at[vector.entity_id] = vector.timestamp
        self._processed_events.add(event_key)
        return True

    def update_many(self, vectors: Iterable[BehavioralFeatureVector]) -> int:
        """Apply vectors in order and return the number of new observations."""

        return sum(self.update(vector) for vector in vectors)

    def get(self, entity_id: str) -> EntityBaseline | None:
        """Return the current immutable baseline for one entity."""

        feature_state = self._features.get(entity_id)
        if feature_state is None:
            return None
        count = next(iter(feature_state.values())).count if feature_state else 0
        return EntityBaseline(
            entity_id=entity_id,
            entity_type=self._entity_types[entity_id],  # type: ignore[arg-type]
            observation_count=count,
            feature_names=tuple(sorted(feature_state)),
            means={name: state.mean for name, state in sorted(feature_state.items())},
            standard_deviations={
                name: state.standard_deviation for name, state in sorted(feature_state.items())
            },
            updated_at=self._updated_at[entity_id],
        )

    def all(self) -> tuple[EntityBaseline, ...]:
        """Return all baselines ordered by entity ID."""

        baselines = [self.get(entity_id) for entity_id in sorted(self._features)]
        return tuple(baseline for baseline in baselines if baseline is not None)


class BaselineArtifactStore:
    """Persist and load trusted entity baselines with checksum validation."""

    def save(self, baseline: EntityBaseline, artifact_dir: str | Path) -> BaselineArtifactManifest:
        directory = Path(artifact_dir)
        directory.mkdir(parents=True, exist_ok=True)
        baseline_path = directory / "baseline.json"
        manifest_path = directory / "manifest.json"
        baseline_path.write_text(
            json.dumps(baseline.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        manifest = BaselineArtifactManifest(
            artifact_name=baseline_path.name,
            artifact_sha256=sha256(baseline_path.read_bytes()).hexdigest(),
            baseline=baseline,
        )
        manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return manifest

    def load(self, artifact_dir: str | Path) -> EntityBaseline:
        directory = Path(artifact_dir)
        manifest = BaselineArtifactManifest.model_validate_json(
            (directory / "manifest.json").read_text(encoding="utf-8")
        )
        artifact_path = directory / manifest.artifact_name
        if sha256(artifact_path.read_bytes()).hexdigest() != manifest.artifact_sha256:
            raise ValueError("baseline artifact checksum does not match manifest")
        baseline = EntityBaseline.model_validate_json(artifact_path.read_text(encoding="utf-8"))
        if baseline != manifest.baseline:
            raise ValueError("baseline artifact does not match manifest")
        return baseline


class BaselineRegistry:
    """Process-local baseline registry used by the serving layer."""

    def __init__(self) -> None:
        self._baselines: dict[str, EntityBaseline] = {}

    def register(self, baseline: EntityBaseline) -> None:
        self._baselines[baseline.entity_id] = baseline

    def load(self, entity_id: str, artifact_dir: str | Path) -> EntityBaseline:
        baseline = BaselineArtifactStore().load(artifact_dir)
        if baseline.entity_id != entity_id:
            raise ValueError("baseline artifact entity does not match requested entity")
        self.register(baseline)
        return baseline

    def get(self, entity_id: str) -> EntityBaseline | None:
        return self._baselines.get(entity_id)
