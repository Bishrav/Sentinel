"""Reproducible fixture runner for behavioral anomaly detectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from .baselines import OnlineBaselineStore
from .comparison import compare_detectors
from .estimators import IsolationForestEstimator
from .models import EntityBaseline, EvaluationRun, LabeledFeatureVector
from .scoring import score_vector


def load_labeled_fixture(path: str | Path) -> tuple[LabeledFeatureVector, ...]:
    """Load one labeled feature-vector JSON object per line."""

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if "vector" not in record:
                vector_fields = {
                    "event_id": record.pop("event_id"),
                    "entity_id": record.pop("entity_id"),
                    "entity_type": record.pop("entity_type", "unknown"),
                    "timestamp": record.pop("timestamp", "2026-08-13T12:00:00Z"),
                    "features": record.pop("features"),
                }
                record = {"vector": vector_fields, "is_anomalous": record["is_anomalous"]}
            else:
                record["vector"].setdefault("timestamp", "2026-08-13T12:00:00Z")
            records.append(record)
        except (KeyError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid labeled fixture record at line {line_number}") from error
    return tuple(TypeAdapter(list[LabeledFeatureVector]).validate_python(records))


def build_baseline(samples: tuple[LabeledFeatureVector, ...]) -> EntityBaseline:
    """Build a baseline from the provided training vectors."""

    if not samples:
        raise ValueError("at least one training sample is required")
    store = OnlineBaselineStore()
    vectors = [sample.vector for sample in samples]
    store.update_many(vectors)
    baseline = store.get(vectors[0].entity_id)
    if baseline is None:
        raise RuntimeError("baseline was not created")
    return baseline


def run_fixture(path: str | Path, *, training_count: int = 2) -> EvaluationRun:
    """Evaluate the fixture with the baseline and available Isolation Forest."""

    samples = load_labeled_fixture(path)
    if not 1 <= training_count < len(samples):
        raise ValueError("training_count must be between 1 and sample_count - 1")
    training = samples[:training_count]
    evaluation = samples[training_count:]
    baseline = build_baseline(training)
    predictors = [
        (
            "z_score_baseline",
            lambda vector: score_vector(vector, baseline, minimum_observations=1).is_anomalous,
        )
    ]
    skipped: list[str] = []
    estimator = IsolationForestEstimator(random_state=42, n_estimators=50)
    try:
        estimator.fit([sample.vector for sample in training])
    except RuntimeError:
        skipped.append("isolation_forest")
    else:
        predictors.append(("isolation_forest", lambda vector: estimator.score(vector).is_anomalous))
    comparison = compare_detectors(evaluation, predictors)
    return EvaluationRun(
        training_sample_count=len(training),
        evaluation_sample_count=len(evaluation),
        comparison=comparison,
        skipped_estimators=tuple(skipped),
    )
