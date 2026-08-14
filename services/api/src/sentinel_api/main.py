"""Sentinel API foundation and ML scoring surface."""

from time import perf_counter

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Field

from sentinel_detection.aggregator import IncidentAggregator
from sentinel_detection.models import Incident
from sentinel_ml.baselines import BaselineRegistry
from sentinel_ml.metrics import AnomalyMetrics
from sentinel_ml.models import AnomalyScore, BehavioralFeatureVector, EntityBaseline
from sentinel_ml.scoring import score_vector
from sentinel_investigation import (
    InvestigationProviderSettings,
    InvestigationRequest,
    InvestigationResponse,
    InvestigationWorkflow,
    ProviderGroundingError,
    ProviderNotConfiguredError,
    ProviderRequestError,
)
from sentinel_sequence.metrics import default_metrics as sequence_metrics


class AnomalyScoreRequest(BaseModel):
    """Request body for baseline-relative anomaly scoring."""

    model_config = ConfigDict(extra="forbid")

    vector: BehavioralFeatureVector
    baseline: EntityBaseline
    threshold: float = Field(default=3.0, gt=0.0)


class IncidentCollection(BaseModel):
    """Read-only incident projection returned by the investigation API."""

    items: tuple[Incident, ...]
    total: int = Field(ge=0)

app = FastAPI(
    title="Sentinel API",
    description="Security telemetry correlation and threat intelligence engine.",
    version="0.1.0",
)

baseline_registry = BaselineRegistry()
ml_metrics = AnomalyMetrics()
incident_store = IncidentAggregator()
investigation_workflow = InvestigationWorkflow(
    provider=InvestigationProviderSettings.from_environment().build_provider()
)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    """Return process health without checking external dependencies."""

    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
async def ready() -> dict[str, str]:
    """Return readiness for the current foundation milestone."""

    return {"status": "ready"}


@app.get("/v1/incidents", response_model=IncidentCollection, tags=["investigation"])
async def list_incidents() -> IncidentCollection:
    """Return the current in-process incident projection."""

    incidents = incident_store.all()
    return IncidentCollection(items=incidents, total=len(incidents))


@app.get("/v1/incidents/{fingerprint}", response_model=Incident, tags=["investigation"])
async def get_incident(fingerprint: str) -> Incident:
    """Return one incident by its deterministic investigation fingerprint."""

    incident = incident_store.get(fingerprint)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"incident not found: {fingerprint}")
    return incident


@app.post("/v1/investigations", response_model=InvestigationResponse, tags=["investigation"])
async def investigate(request: InvestigationRequest) -> InvestigationResponse:
    """Prepare an evidence-grounded investigation without generating unsupported claims."""

    try:
        return investigation_workflow.investigate(request)
    except ProviderNotConfiguredError as error:
        raise HTTPException(status_code=501, detail=str(error)) from error
    except (ProviderGroundingError, ProviderRequestError) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/v1/anomaly/score", response_model=AnomalyScore, tags=["anomaly"])
async def score_anomaly(request: AnomalyScoreRequest) -> AnomalyScore:
    """Score one feature vector against a supplied entity baseline."""

    try:
        started = perf_counter()
        result = score_vector(request.vector, request.baseline, threshold=request.threshold)
        ml_metrics.observe(result, (perf_counter() - started) * 1000)
        return result
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/v1/anomaly/score/{entity_id}", response_model=AnomalyScore, tags=["anomaly"])
async def score_registered_anomaly(
    entity_id: str,
    vector: BehavioralFeatureVector,
    threshold: float = 3.0,
) -> AnomalyScore:
    """Score a vector against a baseline already loaded in the process registry."""

    baseline = baseline_registry.get(entity_id)
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"no baseline registered for entity: {entity_id}",
        )
    try:
        started = perf_counter()
        result = score_vector(vector, baseline, threshold=threshold)
        ml_metrics.observe(result, (perf_counter() - started) * 1000)
        return result
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/metrics", response_class=PlainTextResponse, tags=["operations"])
async def metrics() -> str:
    """Return Prometheus-compatible ML scoring metrics."""

    return ml_metrics.prometheus() + sequence_metrics.prometheus()
