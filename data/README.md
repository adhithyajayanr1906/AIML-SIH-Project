# Dataset Directory Structure

This directory stores geospatial, climate, and processed route datasets for the NER Smart Logistics platform.

## Required Large Datasets (Not tracked in Git due to file size limits)
Due to GitHub's 100MB file limit, the following raw and processed geospatial binaries must be placed locally:

1. `data/geospatial/raw/India_dataset.gpkg` (~2.33 GB) - Multi-hazard & environmental covariate layers (Elevation, Slope, Lithology, NDVI)
2. `data/geospatial/raw/north-eastern-zone-latest.osm.pbf` (~109 MB) - OpenStreetMap raw road vectors
3. `data/geospatial/processed/ner_roads.gpkg` (~162 MB) - Validated road geometries
4. `data/geospatial/processed/ner_road_risk.gpkg` (~167 MB) - Intersected road risk layers
5. `data/geospatial/processed/ner_graph.pkl` (~170 MB) - Pre-computed NetworkX road network graph

## Included Datasets
- `data/raw/daily-rainfall-at-state-level.csv` - Historical rainfall accumulation records from IMD
- `data/processed/ner_rainfall_features.csv` - Preprocessed rainfall features for the North Eastern Region
- `data/processed/rainfall_features.csv` - Engineered rainfall features

## Local Database
- `data/route_history.db` - SQLite persistence database for calculation history and audit reporting (auto-generated on backend startup).
