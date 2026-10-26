# Hazard Dataset Analysis

## 1. Dataset Source
`India_dataset.gpkg` at `data/geospatial/raw/`

## 2. File Size
~2.17 GB

## 3. Layer Inventory
- `fit lr`
- `fit woe`
- `lr crossvalidation`
- `SUcovariate3857lr_final`
- `SUcovariate3857woe_final`
- `woe crossvalidation`
- `layer_styles`

## 4. NER Coverage
Pending exact bbox spatial join, but is assumed to be India-wide bounds due to naming and scale.

## 5. Geometry Types
`Polygon` and `MultiPolygon` representing Slope Units (SUs) or grid cells. No point-event geometries.

## 6. CRS
`EPSG:3857` (WGS 84 / Pseudo-Mercator).

## 7. Available Hazard Features
Covariates available across mappings:
- Elevation (Elev_mean, Elev_std)
- Slope (Slope_mean, Slope_std)
- Aspect (Asp_mean, Asp_std)
- Vegetation/NDVI (NDVI_mean, NDVI_std)
- Rainfall Sum (RnSum_mean, RnSum_std)
- Peak Ground Acceleration (pga_mean)
- Lithology (litho_*)
- Land Cover (lcover_*)

## 8. Historical Event Availability
**None detected.** The `y` column represents a target state utilized during their modelling stages (likely aggregated presence/absence for a mapping unit), but lacks raw historical logs (dates, severity, precise coordinates) necessary for a verifiable event inventory.

## 9. Spatial Resolution
Based on Slope Units / Polygons rather than points or raw raster pixels. Resolution defines generalized topographic bounds.

## 10. Road Integration Possibilities
Polygons can be spatially joined to `ner_roads.gpkg` edges (e.g., matching a road segment to the `Elev_mean` and `Slope_mean` of the polygon it intersects).

## 11. ML Suitability
PREDICTOR DATA AVAILABLE, BUT NO VERIFIED EVENT TARGET. Supervised modelling onto road networks requires genuine event labels which are absent.

## 12. Limitations
Cannot forecast exact hazard dates or locations because history is not recorded in the dataset.

## 13. Recommended Next Dataset/Action
Source a precise Landslide/Disaster Event Inventory (e.g., points containing Date and coordinates) to act as the dependent variable for training against these excellent covariates.
