"""Result/report formatting helpers.

The engine returns structured JSON-compatible results with run metadata and
per-cell findings. Higher-level report presentation/export is handled by
backend/frontend components.
"""

from __future__ import annotations

from typing import Any


def build_analysis_summary(results: dict[str, Any]) -> dict[str, Any]:
    """Return a compact summary payload from a completed analysis result."""
    return {
        "status": results.get("status"),
        "summary": results.get("summary", {}),
        "run_metadata": results.get("run_metadata", {}),
        "cells_count": len(results.get("cells", []) or []),
    }
