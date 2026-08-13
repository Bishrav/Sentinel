"""Temporal sequence-correlation contracts and matching for Sentinel."""

from .loader import load_sequences
from .matcher import FiniteStateSequenceMatcher
from .metrics import SequenceMetrics, default_metrics

__all__ = ["FiniteStateSequenceMatcher", "SequenceMetrics", "default_metrics", "load_sequences"]

__version__ = "0.1.0"
