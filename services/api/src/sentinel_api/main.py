"""Sentinel API foundation and ML scoring surface."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from sentinel_ml.models import AnomalyScore, BehavioralFeatureVector, EntityBaseline
from sentinel_ml.scoring import score_vector


class AnomalyScoreRequest(BaseModel):
    """Request body for baseline-relative anomaly scoring."""

    model_config = ConfigDict(extra="forbid")

    vector: BehavioralFeatureVector
    baseline: EntityBaseline
    threshold: float = Field(default=3.0, gt=0.0)

app = FastAPI(
    title="Sentinel API",
    description="Security telemetry correlation and threat intelligence engine.",
    version="0.1.0",
)


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    """Return process health without checking external dependencies."""

    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
async def ready() -> dict[str, str]:
    """Return readiness for the current foundation milestone."""

    return {"status": "ready"}


@app.post("/v1/anomaly/score", response_model=AnomalyScore, tags=["anomaly"])
async def score_anomaly(request: AnomalyScoreRequest) -> AnomalyScore:
    """Score one feature vector against a supplied entity baseline."""

    try:
        return score_vector(request.vector, request.baseline, threshold=request.threshold)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
