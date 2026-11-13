# Method notes

## Pipeline
1. Monthly cube `x(t, lat, lon)`.
2. Climatology `c(m)` = mean over all years for calendar month `m`; anomaly `a = x - c(month(t))`.
3. Annual mean anomaly `A(y)` = mean of `a` within year `y` if at least `min_months` months are valid.
4. Per cell, with at least `min_years` valid years: Theil-Sen slope (median of pairwise slopes) and Mann-Kendall S statistic with the Hamed-Rao variance correction for autocorrelation.
5. Benjamini-Hochberg across all valid cells at level `alpha` (default 0.05).
6. Standardized trend = (slope * 10) / std(A over years).

## Why annual means
Monthly anomalies remain autocorrelated and 12x more numerous. Annual means are simple, fast, and defensible. For monthly resolution use `pymannkendall.seasonal_test` or `hamed_rao_modification_test` on monthly anomalies per cell (slower).

## Field significance
FDR controls false discoveries across cells but not spatial autocorrelation. For claims about regions rather than cells, aggregate first (area-weighted mean over the region with weights cos(lat)) and test the regional series.

## Synthetic validation recipe
1. Build a cube with a known trend (for example +0.05 units/year) in one half and pure noise in the other, plus a seasonal cycle and some NaN cells.
2. Run the pipeline.
3. Expect recovered slope near the true value, most trended cells significant, and only a small share of noise cells significant (FDR controls the false share among the cells flagged, not per cell).

## Validation against Giovanni
Pick 2 or 3 points, download the Giovanni time series for the same dataset and dates, compare with the cube at the nearest cell. Compare the sign of the trend too.

## Known limits
- Grid cells are not independent; neighboring cells share signal.
- Records under 10 years give unreliable trends; 15 or more is better.
- Coarse sensors (GRACE) cannot resolve small areas even on a finer grid.
- Reanalysis (MERRA-2) trends can reflect changes in assimilated observations.
