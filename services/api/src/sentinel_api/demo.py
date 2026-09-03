"""Deterministic failed-login replay for local demonstration and review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sentinel_detection.pipeline import build_pipeline
from sentinel_ingestion.collectors import JsonLinesCollector
from sentinel_ingestion.enricher import enrich
from sentinel_ingestion.normalizer import normalize
from sentinel_investigation import EvidenceReference, InvestigationRequest, InvestigationWorkflow
from sentinel_risk import RiskInput, score_risk


def replay_failed_login(fixture: Path) -> dict[str, Any]:
    """Replay the checked-in failed-login scenario without external services."""

    events = [
        enrich(normalize(raw, source="failed-login-fixture"))
        for raw in JsonLinesCollector(fixture).collect()
    ]
    pipeline = build_pipeline(
        Path(__file__).parents[4] / "config" / "rules" / "default.json",
        Path(__file__).parents[4] / "config" / "sequences" / "default.json",
    )
    pipeline.process_many(events)
    sequence_incidents = [
        incident
        for incident in pipeline.incidents()
        if any("sequence:" in rule for rule in incident.rule_ids)
    ]
    if len(sequence_incidents) != 1:
        raise ValueError("expected exactly one failed-login sequence incident")
    incident = sequence_incidents[0]
    replay_at = max(event.timestamp for event in events)
    risk = score_risk(
        RiskInput(
            incident_id=incident.incident_id,
            severity=incident.severity,
            anomaly_score=100.0 if incident.match_count else 0.0,
            sequence_confidence=1.0,
            evidence_count=len(incident.evidence),
        )
    ).model_copy(update={"recorded_at": replay_at})
    assessed = pipeline.aggregator.apply_risk(risk)
    if assessed is None:
        raise ValueError("failed-login incident disappeared before risk assessment")
    evidence = tuple(
        EvidenceReference(
            reference_type="event", reference_id=str(event.event_id), source=event.source
        )
        for event in events
    ) + (
        EvidenceReference(
            reference_type="sequence_match",
            reference_id=incident.fingerprint,
            source="sequence-matcher",
        ),
    )
    investigation = (
        InvestigationWorkflow()
        .investigate(
            InvestigationRequest(
                incident_id=assessed.incident_id,
                question="What evidence supports this suspicious login sequence?",
                evidence=evidence,
            )
        )
        .model_copy(update={"generated_at": max(event.timestamp for event in events)})
    )
    return {
        "input": [event.model_dump(mode="json") for event in events],
        "normalized_events": [event.model_dump(mode="json") for event in events],
        "incident": assessed.model_dump(mode="json"),
        "risk_explanation": risk.model_dump(mode="json"),
        "investigation_response": investigation.model_dump(mode="json"),
        "deterministic": True,
        "generated_at": replay_at.isoformat(),
    }


def replay_json(fixture: Path) -> str:
    return json.dumps(replay_failed_login(fixture), sort_keys=True, indent=2)
