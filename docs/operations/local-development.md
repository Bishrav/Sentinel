# Local development

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop with Docker Compose

## Setup

```powershell
Copy-Item .env.example .env
uv sync --dev
```

Start the local infrastructure:

```powershell
docker compose -f infrastructure/docker/compose.yaml up -d
```

Run the API:

```powershell
uv run uvicorn sentinel_api.main:app --app-dir services/api/src --reload
```

The API is available at `http://localhost:8000`. OpenAPI documentation is available at `/docs`; operational probes are `/health` and `/ready`.

## Quality checks

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Stop local infrastructure with:

```powershell
docker compose -f infrastructure/docker/compose.yaml down
```

Add `-v` only when intentionally discarding local database, cache, graph, or event-broker volumes.
