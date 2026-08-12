"""Minimal API foundation for Sentinel services."""

from fastapi import FastAPI

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
