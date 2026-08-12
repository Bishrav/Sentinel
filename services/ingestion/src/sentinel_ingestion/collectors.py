"""Source collectors used by live ingestion and deterministic replay."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, Protocol


class Collector(Protocol):
    """Minimal source collector contract."""

    def collect(self) -> Iterator[Mapping[str, Any]]:
        """Yield raw source records in arrival order."""


class JsonLinesCollector:
    """Read one JSON object per line from a local replay or export file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def collect(self) -> Iterator[Mapping[str, Any]]:
        with self.path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid JSON at {self.path}:{line_number}") from error
                if not isinstance(record, dict):
                    raise ValueError(f"expected an object at {self.path}:{line_number}")
                yield record
