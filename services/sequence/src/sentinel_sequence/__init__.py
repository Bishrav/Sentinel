"""Temporal sequence-correlation contracts and matching for Sentinel."""

from .loader import load_sequences
from .matcher import FiniteStateSequenceMatcher

__all__ = ["FiniteStateSequenceMatcher", "load_sequences"]

__version__ = "0.1.0"
