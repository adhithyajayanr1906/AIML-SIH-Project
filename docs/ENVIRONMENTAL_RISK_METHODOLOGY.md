# Environmental Risk & Validation Methodology

## 1. Goal and Methodological Distinction
This system calculates deterministic heuristic indices representing relative environmental and infrastructure vulnerability for routing in the North Eastern Region of India.

CRITICAL DISTINCTION:
1. Route Calculation Validation: Demonstrates internal mathematical and topological consistency of the route with the underlying OpenStreetMap road graph and Haversine reference formula.
2. Disaster Predictive Accuracy: Strictly NOT ESTABLISHED because verified historical disaster occurrence event logs (ground truth labels) do not exist in the dataset.
Passing route validation demonstrates internal software consistency, NOT real-world route passability, slope stability, or flood immunity.

## 2. Environmental Hazard Input Covariates
* `rainfall_anomaly`: Raw deviation from climatological normal rainfall bounds (mm).
* `extreme_rainfall_indicator`: Binary flag (1 if precip exceeds 95th percentile, else 0).
* `slope`: Mean terrain slope in degrees from digital elevation model.
* `elev`: Mean elevation in meters above sea level.
* `ndvi`: Normalized Difference Vegetation Index (NDVI) vegetation cover metric [-1 to 1].

## 3. Normalization Strategies
All continuous variables are capped and normalized to [0.0, 1.0]:
* `Rainfall Factor`: `min(max(anomaly / 100, 0), 1)`
* `Slope Factor`: `min(max(slope / 45, 0), 1)`
* `Elevation Exposure`: `max(0, 1 - (elev / 2000))` (Inverted; lower elevations represent higher alluvial flood accumulation risk).
* `Vegetation Exposure`: `max(0, 1 - ndvi)` (Inverted; degraded vegetation increases landslide and surface erosion risk).

## 4. Deterministic Environmental Risk Heuristic
`Raw Risk = (0.40 * Rainfall) + (0.30 * Slope) + (0.15 * Elevation) + (0.15 * Vegetation)`

If `extreme_rainfall_indicator == 1`, the score is boosted by 50% and bounded to [0.0, 1.0]:
`Final Environmental Risk = min(1.0, Raw Risk * 1.5)`

Category Thresholds:
* `CRITICAL`: > 0.75
* `HIGH`: 0.51 - 0.75
* `MODERATE`: 0.26 - 0.50
* `LOW`: 0.00 - 0.25

## 5. Missing Covariates & Environmental Coverage Policy
In `ner_road_risk.gpkg`, 190,532 of 264,554 road edges lack spatial overlap with the raster hazard datasets.
Rule:
* Valid risk values of 0.0 are NOT treated as missing data.
* Missing raster covariates are explicitly tracked via edge flag `covariates_available: bool`.
* Edges missing covariates receive a neutral baseline penalty rather than being misrepresented as proven zero risk.
* Every calculated route explicitly outputs an `environmental_coverage` report detailing:
  - `status`: "Available" or "Not Assessed"
  - `total_segments`: Total route segments
  - `segments_with_covariates`: Segments with genuine raster data
  - `segments_missing_covariates`: Segments with neutral fallback
  - `coverage_ratio`: Ratio of segments with covariates
  - `coverage_percentage`: Percentage coverage

## 6. Evidence-Weighted Confidence Index
The confidence score is an evidence-weighted index bounded in [0.0, 100.0] (NOT a statistically calibrated probability):
* Endpoint Snapping Proximity (Weight: 35%):
  - Average snapping <= 1.0 km: 35 pts
  - Average snapping <= 5.0 km: 28 pts
  - Average snapping <= 15.0 km: 18 pts
  - Average snapping <= 50.0 km: 10 pts
  - Average snapping > 50.0 km: 0 pts (requests rejected)
* Road Graph Component Scale (Weight: 30%):
  - Connected component >= 1,000 nodes: 30 pts
  - Connected component >= 100 nodes: 22 pts
  - Connected component >= 10 nodes: 12 pts
  - Connected component >= 2 nodes: 5 pts
  - Connected component < 2 nodes: 0 pts
* Environmental Covariate Completeness (Weight: 20%):
  - `(coverage_percentage / 100.0) * 20.0` pts
* Mathematical Route Validation (Weight: 15%):
  - PASSED: 15 pts
  - FAILED: 0 pts

Qualitative Ratings:
* `High`: >= 80.0%
* `Moderate`: 60.0% - 79.9%
* `Low`: 40.0% - 59.9%
* `Not Assessed`: < 40.0%
