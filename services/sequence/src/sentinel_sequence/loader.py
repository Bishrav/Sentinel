"""Load and validate versioned sequence signatures from JSON."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import TypeAdapter

from .models import SequenceSignature


def load_sequences(path: str | Path) -> tuple[SequenceSignature, ...]:
    """Load and validate a JSON array of sequence signatures."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple(TypeAdapter(list[SequenceSignature]).validate_python(payload))
