# Geospatial Data Analysis

## 1. NER Geographic Scope
This project focuses on the 8 North-Eastern states: Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, and Tripura. Real topological and boundary definitions will be extracted via verified shapefiles or OpenStreetMap boundaries.

## 2. Required Road-Network Data
A graph-based map for routing algorithms (Dijkstra, A*) requires raw infrastructure data. We expect `.osm.pbf`, `.geojson`, `.gpkg`, or `.shp` containing coordinate geometries and road type/hierarchy tags. OSM extracts are typically preferred.

## 3. Required Hazard Data
In order to assign valid ground-truth logistics risk, we need datasets documenting precise impact events with `latitude`/`longitude` pinpointing road blockages, landslide occurrences, or flood locations.

## 4. Expected Geospatial Schema
Hazard events require: event_id, date, latitude, longitude, state, district, hazard_type, severity, and source.
Road networks require: nodes (id, lat, lon) and edges (source, destination, geometry, length, type).

## 5. CRS Considerations
Imports must transition from standard geographic projection (EPSG:4326 WGS84) to metric projected coordinate systems to properly evaluate distance vectors for travel cost calculations.

## 6. Road Graph Design
Features will decompose into nodes (intersections/joints) and edges (road lengths).
- Base Routing Cost defaults to mathematical geometric length scaled by average road tier speeds.
- Hazard Penalties (`risk_cost`) mathematically overlay true conditions.

## 7. Rainfall-to-Geography Integration Limitations
The current rainfall dataset is state-level and therefore cannot independently provide road-segment-level flood prediction. We can map aggregate state risk scores to regions, but we cannot deduce kilometer accurate impact graphs strictly from this data. 

## 8. Future Hazard-to-Road Matching
When a genuine dataset of real hazards is ingested, we will utilize `nearest-neighbor matching` or buffering to spatial-join points of disaster (landslides/flash floods) onto adjacent road networks, triggering dynamic penalty weightings for the routing engine.

## 9. Data Quality Requirements
- No fake nodes or edges.
- No artificially generated disaster logs.
- Validation of overlapping polygons. 

## 10. What is still missing
We are missing the foundational road extract and the geocoded hazard registry.
