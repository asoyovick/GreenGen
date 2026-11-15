"""Trend detection and magnitude estimation.

- Mann–Kendall with Hamed–Rao autocorrelation correction
- Theil–Sen slope with confidence interval

Insufficient data must not be assigned a detected trend/significance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pymannkendall as mk
from scipy.stats import theilslopes


@dataclass
class TrendResult:
    n_years: int
    slope_per_year: float | None
    slope_units: str | None
    ci_lower: float | None
    ci_upper: float | None
    p_value: float | None
    mk_tau: float | None
    mk_statistic: float | None
    direction: str | None  # increasing|decreasing|no_trend
    sufficient: bool
    flags: list[str]


def _nan() -> float:
    return float("nan")


def compute_trend(
    years: np.ndarray,
    values: np.ndarray,
    min_years: int = 10,
    slope_units: str | None = None,
    alpha_ci: float = 0.95,
) -> TrendResult:
    """Compute trend statistics for a single annual series.

    years/values are 1D arrays of equal length (may include NaNs in values).
    Missing values are excluded; never treated as zero.
    """
    flags: list[str] = []
    y = np.asarray(values, dtype=float)
    x = np.asarray(years, dtype=float)
    if y.shape != x.shape:
        raise ValueError("years and values must have the same shape")
    ok = np.isfinite(y) & np.isfinite(x)
    yy = y[ok]
    xx = x[ok].astype(float)
    n = int(yy.size)

    if n < int(min_years):
        flags.append("insufficient_data")
        return TrendResult(
            n_years=n,
            slope_per_year=None,
            slope_units=slope_units,
            ci_lower=None,
            ci_upper=None,
            p_value=None,
            mk_tau=None,
            mk_statistic=None,
            direction=None,
            sufficient=False,
            flags=flags,
        )

    # Constant series: no monotonic trend; slope 0
    if np.ptp(yy) == 0:
        return TrendResult(
            n_years=n,
            slope_per_year=0.0,
            slope_units=slope_units,
            ci_lower=0.0,
            ci_upper=0.0,
            p_value=1.0,
            mk_tau=0.0,
            mk_statistic=0.0,
            direction="no_trend",
            sufficient=True,
            flags=flags,
        )

    try:
        ts = theilslopes(yy, xx, alpha=float(alpha_ci))
        slope = float(ts.slope)
        ci_lower = float(ts.low_slope)
        ci_upper = float(ts.high_slope)
    except Exception:
        flags.append("slope_estimation_failed")
        slope = None
        ci_lower = None
        ci_upper = None

    try:
        mk_res = mk.hamed_rao_modification_test(yy)
        p_value = float(mk_res.p)
        tau = float(getattr(mk_res, "Tau", np.nan))
        stat = float(getattr(mk_res, "s", getattr(mk_res, "S", np.nan)))
    except Exception:
        flags.append("mann_kendall_failed")
        p_value = None
        tau = None
        stat = None

    direction = None
    if slope is not None:
        if slope > 0:
            direction = "increasing"
        elif slope < 0:
            direction = "decreasing"
        else:
            direction = "no_trend"

    if slope is None or p_value is None:
        flags.append("inconclusive")

    return TrendResult(
        n_years=n,
        slope_per_year=slope,
        slope_units=slope_units,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        p_value=p_value,
        mk_tau=None if tau is None or not np.isfinite(tau) else tau,
        mk_statistic=None if stat is None or not np.isfinite(stat) else stat,
        direction=direction,
        sufficient=True,
        flags=flags,
    )
