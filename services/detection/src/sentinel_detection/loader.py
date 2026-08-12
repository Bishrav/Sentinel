"""Load versioned rule configuration from JSON."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from .models import DetectionRule


def load_rules(path: str | Path) -> tuple[DetectionRule, ...]:
    """Load and validate a JSON array of detection rules."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(TypeAdapter(list[DetectionRule]).validate_python(payload))
