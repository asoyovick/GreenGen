"""Data loading and input preparation helpers.

Primary implementation lives in :mod:`scientific_engine.io` and related
modules. This module provides a stable import location matching the planned
engine structure (#034).
"""

from .io import load_observation

__all__ = ["load_observation"]
