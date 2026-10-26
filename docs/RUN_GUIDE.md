# Run Guide: NER Smart Logistics

## 1. Prerequisites
- Python 3.9+
- Windows environment (or adapted for Unix).

## 2. Dependencies
Install the required packages using the virtual environment:
```powershell
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn pydantic pyogrio geopandas networkx
```

## 3. Dataset Requirements
Place the following exact files:
- `data/geospatial/raw/India_dataset.gpkg` (2.17GB Covariates)
- `data/geospatial/processed/ner_roads.gpkg` (Validated Road Geometries)

## 4. Single Server Startup
This platform seamlessly spins up the routing engines and the Static JS frontend via one singular Uvicorn interface natively supporting the whole stack:
```powershell
run_server.bat
```
*(Alternative manual command: `python -m uvicorn backend.app.main:app`)*

## 5. Web Dashboard URL
Once the terminal reads "Application startup complete", open any browser to:
👉 **http://127.0.0.1:8000**

## 6. Interactive Swagger API Docs
If developer testing is required for raw ML hooks:
👉 **http://127.0.0.1:8000/docs**

## 7. Validating Status
Endpoints:
- `GET /health`: Validates graph dimensions loaded in RAM.
- `POST /predict/environmental-risk`: Derives deterministic exposure score against {rainfall, slope, elev}.
- `POST /predict/logistics-risk`: Outputs structural indices.

## 8. Common Errors
- `Graph not initialized`: Verify that you did not delete `ner_graph.pkl` or ensure `ner_road_risk.gpkg` exists to recalculate the caching.
- `Coordinates out of network bounds`: Origin coordinates pushed to the frontend map must explicitly lie within the 8 North-Eastern states. 
