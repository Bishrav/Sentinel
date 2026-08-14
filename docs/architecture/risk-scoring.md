# Evidence-weighted risk scoring

Sentinel uses a deterministic risk engine so an incident score remains explainable and replayable. The engine accepts normalized evidence signals and stores every weighted component in a `RiskAuditRecord`.

## Formula version 1.0

```text
score = severity * 0.30
      + anomaly * 0.25
      + sequence_confidence * 100 * 0.20
      + graph_risk * 0.20
      + min(evidence_count * 10, 100) * 0.05
```

The result is bounded to 0–100 and mapped to low, medium, high, or critical bands. Risk assessments can be attached to incidents through `POST /v1/incidents/{fingerprint}/risk`; the incident retains the score, band, and full audit record.
