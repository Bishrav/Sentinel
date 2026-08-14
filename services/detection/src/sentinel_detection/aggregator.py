"""Replay-safe in-memory incident aggregation."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import NAMESPACE_URL, UUID, uuid5

from sentinel_ingestion.models import SecurityEvent
from sentinel_risk.models import RiskAuditRecord
from sentinel_sequence.models import SequenceMatch

from .models import Incident, RuleMatch, Severity

_SEVERITY_RANK: dict[Severity, int] = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _max_severity(left: Severity, right: Severity) -> Severity:
    return left if _SEVERITY_RANK[left] >= _SEVERITY_RANK[right] else right


class IncidentAggregator:
    """Group rule matches by fingerprint while deduplicating event replays."""

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}
        self._processed_matches: set[tuple[str, UUID]] = set()
        self._processed_sequences: set[tuple[str, int, tuple[UUID, ...]]] = set()

    def add(self, event: SecurityEvent, matches: Iterable[RuleMatch]) -> tuple[Incident, ...]:
        changed: list[Incident] = []
        for match in matches:
            match_key = (match.rule_id, match.event_id)
            if match_key in self._processed_matches:
                continue
            self._processed_matches.add(match_key)
            incident = self._incidents.get(match.fingerprint)
            if incident is None:
                incident = Incident(
                    incident_id=uuid5(NAMESPACE_URL, f"sentinel:incident:{match.fingerprint}"),
                    fingerprint=match.fingerprint,
                    first_seen=match.matched_at,
                    last_seen=match.matched_at,
                    severity=match.severity,
                    rule_ids=frozenset({match.rule_id}),
                    event_ids=(match.event_id,),
                    actor_ids=frozenset({event.actor_id}),
                    resources=frozenset({event.resource}),
                    match_count=1,
                    evidence=(match.evidence,),
                )
            else:
                event_ids = incident.event_ids + (
                    (match.event_id,) if match.event_id not in incident.event_ids else ()
                )
                evidence = incident.evidence + (
                    (match.evidence,) if match.evidence not in incident.evidence else ()
                )
                incident = incident.model_copy(
                    update={
                        "last_seen": max(incident.last_seen, match.matched_at),
                        "severity": _max_severity(incident.severity, match.severity),
                        "rule_ids": incident.rule_ids | {match.rule_id},
                        "event_ids": event_ids,
                        "actor_ids": incident.actor_ids | {event.actor_id},
                        "resources": incident.resources | {event.resource},
                        "match_count": incident.match_count + 1,
                        "evidence": evidence,
                    }
                )
            self._incidents[match.fingerprint] = incident
            changed.append(incident)
        return tuple(changed)

    def add_sequences(self, matches: Iterable[SequenceMatch]) -> tuple[Incident, ...]:
        """Add completed sequence matches as replay-safe incident projections."""

        changed: list[Incident] = []
        for match in matches:
            match_key = (match.signature_id, match.signature_version, match.event_ids)
            if match_key in self._processed_sequences:
                continue
            self._processed_sequences.add(match_key)

            fingerprint = f"sequence:{match.signature_id}:{match.actor_id}"
            rule_id = f"sequence:{match.signature_id}:v{match.signature_version}"
            resources = frozenset(
                str(item["resource"])
                for item in match.evidence
                if isinstance(item.get("resource"), str)
            )
            incident = self._incidents.get(fingerprint)
            if incident is None:
                incident = Incident(
                    incident_id=uuid5(NAMESPACE_URL, f"sentinel:incident:{fingerprint}"),
                    fingerprint=fingerprint,
                    first_seen=match.started_at,
                    last_seen=match.completed_at,
                    severity=match.severity,
                    rule_ids=frozenset({rule_id}),
                    event_ids=match.event_ids,
                    actor_ids=frozenset({match.actor_id}),
                    resources=resources,
                    match_count=1,
                    evidence=tuple(match.evidence),
                )
            else:
                event_ids = incident.event_ids + tuple(
                    event_id for event_id in match.event_ids if event_id not in incident.event_ids
                )
                evidence = incident.evidence + tuple(
                    item for item in match.evidence if item not in incident.evidence
                )
                incident = incident.model_copy(
                    update={
                        "last_seen": max(incident.last_seen, match.completed_at),
                        "severity": _max_severity(incident.severity, match.severity),
                        "rule_ids": incident.rule_ids | {rule_id},
                        "event_ids": event_ids,
                        "actor_ids": incident.actor_ids | {match.actor_id},
                        "resources": incident.resources | resources,
                        "match_count": incident.match_count + 1,
                        "evidence": evidence,
                    }
                )
            self._incidents[fingerprint] = incident
            changed.append(incident)
        return tuple(changed)

    def get(self, fingerprint: str) -> Incident | None:
        return self._incidents.get(fingerprint)

    def apply_risk(self, audit: RiskAuditRecord) -> Incident | None:
        """Attach a replayable risk audit to its matching incident."""

        incident = next(
            (item for item in self._incidents.values() if item.incident_id == audit.inputs.incident_id),
            None,
        )
        if incident is None:
            return None
        if audit.assessment.incident_id != incident.incident_id:
            raise ValueError("risk assessment incident_id does not match incident")
        updated = incident.model_copy(
            update={
                "risk_score": audit.assessment.score,
                "risk_band": audit.assessment.band,
                "risk_audit": audit,
            }
        )
        self._incidents[incident.fingerprint] = updated
        return updated

    def all(self) -> tuple[Incident, ...]:
        return tuple(self._incidents.values())
