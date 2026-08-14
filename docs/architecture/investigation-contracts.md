# Evidence-grounded investigation contracts

Sentinel investigations use typed request and response contracts so downstream model providers cannot silently turn unsupported context into an incident explanation.

## Request boundary

`InvestigationRequest` contains an incident ID, a bounded question, an explicit evidence set, and an execution mode. The evidence set is assembled by Sentinel services; an investigation provider receives references rather than unrestricted telemetry access.

## Response boundary

`InvestigationResponse` contains a summary, optional hypotheses, and the evidence references that were made available to the answer. Every hypothesis must cite at least one reference ID present in `cited_evidence`. Pydantic validation rejects unresolved citations before the response can cross a service boundary.

Supported evidence types are events, incidents, sequence matches, graph paths, baselines, and detection rules. The contract is versioned as `1.0` and mirrored in `schemas/investigation-response.schema.json`.

This milestone defines the boundary only. Provider orchestration, runbook retrieval, and an HTTP investigation endpoint remain separate implementation milestones.
