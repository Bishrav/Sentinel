from datetime import datetime, timezone
from pathlib import Path

import pytest

from sentinel_ml.baselines import BaselineArtifactStore, BaselineRegistry
from sentinel_ml.models import EntityBaseline


def baseline() -> EntityBaseline:
    return EntityBaseline(
        entity_id="user-42",
        entity_type="user",
        observation_count=5,
        feature_names=("request_rate",),
        means={"request_rate": 10.0},
        standard_deviations={"request_rate": 2.0},
        updated_at=datetime(2026, 8, 13, 11, 0, tzinfo=timezone.utc),
    )


def test_baseline_artifact_round_trip_and_registry(tmp_path: Path) -> None:
    store = BaselineArtifactStore()
    manifest = store.save(baseline(), tmp_path / "baseline")
    restored = store.load(tmp_path / "baseline")
    registry = BaselineRegistry()
    registry.load("user-42", tmp_path / "baseline")

    assert manifest.baseline == restored
    assert registry.get("user-42") == baseline()


def test_tampered_baseline_is_rejected(tmp_path: Path) -> None:
    store = BaselineArtifactStore()
    store.save(baseline(), tmp_path / "baseline")
    (tmp_path / "baseline" / "baseline.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        store.load(tmp_path / "baseline")
