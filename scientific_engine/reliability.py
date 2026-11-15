"""Statistical reliability: multiple testing (FDR) and quality flags.

Cells without finite/testable p-values are excluded from the tested family and
must not be marked significant.
"""

from __future__ import annotations

import numpy as np
from statsmodels.stats.multitest import multipletests


def fdr_significance_mask(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Benjamini–Hochberg FDR over finite p-values.

    Returns boolean mask of same shape where True indicates FDR-significant.
    Non-finite p-values remain False.
    """
    p = np.asarray(p_values, dtype=float)
    valid = np.isfinite(p)
    sig = np.zeros(p.shape, dtype=bool)
    if valid.any():
        reject, _, _, _ = multipletests(p[valid], alpha=float(alpha), method="fdr_bh")
        sig[valid] = np.asarray(reject, dtype=bool)
    return sig


def classify_cell(
    *,
    sufficient: bool,
    fdr_significant: bool,
    direction: str | None,
    flags: list[str] | None = None,
    completeness: float | None = None,
    min_completeness: float = 0.0,
) -> str:
    """Map statistical outputs to API classification semantics."""
    flags = flags or []
    if not sufficient:
        return "insufficient_data"
    if completeness is not None and completeness < float(min_completeness):
        return "insufficient_data"
    if "inconclusive" in flags or "mann_kendall_failed" in flags or "slope_estimation_failed" in flags:
        return "inconclusive"
    if fdr_significant and direction == "increasing":
        return "significant_increase"
    if fdr_significant and direction == "decreasing":
        return "significant_decrease"
    if not fdr_significant:
        # Evidence does not establish a significant trend (not "stable")
        return "no_significant_trend"
    return "inconclusive"


def low_confidence_flag(n_years: int, ok_years: int = 15) -> bool:
    return int(n_years) < int(ok_years)
