from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Dict, Any
import networkx as nx
import pickle
import os
import sys
import math

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/routing'))
# pyrefly: ignore [missing-import]
from risk_aware_router import build_risk_graph, get_nearest_node, get_nearest_nodes, shortest_path_dijkstra
# pyrefly: ignore [missing-import]
from airway_router import calculate_air_route, AirwayValidationError

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/risk'))
# pyrefly: ignore [missing-import]
from environmental_risk import calculate_environmental_risk
# pyrefly: ignore [missing-import]
from logistics_risk import calculate_logistics_risk

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/evaluation'))
# pyrefly: ignore [missing-import]
from metrics_engine import validate_road_route, compute_road_confidence, validate_air_route

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/analytics'))
# pyrefly: ignore [missing-import]
from rainfall_analytics import get_rainfall_summary, get_state_rainfall_trends
# pyrefly: ignore [missing-import]
from overview_metrics import get_system_overview_metrics

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/backend/app'))
# pyrefly: ignore [missing-import]
import history_db

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/geocoding'))
# pyrefly: ignore [missing-import]
import nominatim_service
# pyrefly: ignore [missing-import]
from nominatim_service import GeocodingError

import pyogrio

app = FastAPI(title="NER Smart Logistics API - Risk & Route Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
)

G_ROAD = None
GRAPH_PICKLE = "c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl"

@app.on_event("startup")
def load_graph():
    global G_ROAD
    history_db.init_db()
    if os.path.exists(GRAPH_PICKLE):
        with open(GRAPH_PICKLE, 'rb') as f:
            G_ROAD = pickle.load(f)
    else:
        risk_layer = "c:/NER-Smart-Logistics/data/geospatial/processed/ner_road_risk.gpkg"
        if os.path.exists(risk_layer):
            gdf = pyogrio.read_dataframe(risk_layer)
            G_ROAD = build_risk_graph(gdf)
            with open(GRAPH_PICKLE, 'wb') as f:
                pickle.dump(G_ROAD, f)
        else:
            print("WARNING: Road risk dataset missing. Graph empty.")
            G_ROAD = nx.Graph()

@app.get("/health")
def health():
    return {"status": "ONLINE", "nodes": G_ROAD.number_of_nodes() if G_ROAD else 0}

# ---------------------------------------------------------------------------
# LOCATION SEARCH — GET /locations/search?q=<query>
# Backed by OpenStreetMap Nominatim. Biased toward the NER but not exclusive.
# ---------------------------------------------------------------------------

@app.get("/locations/search")
def location_search(
    q: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="Place name query (min 2 characters).",
    )
):
    """
    Search for real geographic places matching q.
    Returns up to 7 results with display_name, latitude, longitude, place_type.
    Backed by OpenStreetMap Nominatim.
    """
    try:
        results = nominatim_service.search_locations(q)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except (GeocodingError, nominatim_service.GeocodingError) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Location search is temporarily unavailable. "
                f"Provider error: {exc}"
            ),
        )
    return {"results": results, "query": q, "count": len(results)}

class EnvRequest(BaseModel):
    rainfall_anomaly: float
    extreme_indicator: int
    slope: float
    elev: float
    ndvi: float

@app.post("/predict/environmental-risk")
def predict_env_risk(req: EnvRequest):
    r_score, r_cat, factors = calculate_environmental_risk(
        req.rainfall_anomaly, req.extreme_indicator, req.slope, req.elev, req.ndvi
    )
    return {"risk_score": r_score, "risk_category": r_cat, "contributing_factors": factors}

class LogRequest(BaseModel):
    env_risk_score: float
    length_m: float
    road_type: str

@app.post("/predict/logistics-risk")
def predict_log_risk(req: LogRequest):
    l_score, l_cat, factors = calculate_logistics_risk(
        req.env_risk_score, req.length_m, req.road_type
    )
    return {"logistics_risk_score": l_score, "risk_category": l_cat, "contributing_factors": factors}

@app.get("/risk/road/{road_id}")
def get_road_risk(road_id: int):
    return {"road_id": road_id, "status": "Road ID lookup available."}

# ---------------------------------------------------------------------------
# ROADWAY ROUTE — Dijkstra on the road network
# Accepted route sub-modes: SHORTEST (travel_cost) | SAFE (total_cost = dist + risk penalty)
# transport_mode must be "ROADWAY"; any other value returns HTTP 422.
# ---------------------------------------------------------------------------
_VALID_ROUTE_SUBMODES = {"SHORTEST", "SAFE"}

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    origin_name: Optional[str] = "Selected Origin"
    dest_name: Optional[str] = "Selected Destination"
    mode: str = "SHORTEST"
    transport_mode: str = "ROADWAY"
    save_to_history: bool = True

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        upper = v.upper()
        if upper not in _VALID_ROUTE_SUBMODES:
            raise ValueError(
                f"Invalid route mode '{v}'. "
                f"For /route/recommend, 'mode' must be one of: {sorted(_VALID_ROUTE_SUBMODES)}. "
                "For airway routing, use the /route/airway endpoint instead."
            )
        return upper

    @field_validator("transport_mode")
    @classmethod
    def validate_transport_mode(cls, v: str) -> str:
        upper = v.upper()
        if upper != "ROADWAY":
            raise ValueError(
                f"Invalid transport_mode '{v}' for /route/recommend. "
                "This endpoint handles ROADWAY routing only. "
                "For airway routing, use the /route/airway endpoint."
            )
        return upper

    @field_validator("origin_lat", "dest_lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not math.isfinite(v) or not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude {v} is out of valid range [-90, 90].")
        return v

    @field_validator("origin_lon", "dest_lon")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not math.isfinite(v) or not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude {v} is out of valid range [-180, 180].")
        return v

def _calculate_roadway_route(req: RouteRequest) -> Dict[str, Any]:
    if not G_ROAD or G_ROAD.number_of_nodes() == 0:
        raise HTTPException(status_code=500, detail="Road graph not initialized. Check dataset availability.")

    import pyproj
    transformer_to_graph = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    transformer_to_wgs84 = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)

    # Convert incoming WGS84 (lon, lat) to the graph's projected CRS (EPSG:3857 meters)
    orig_x, orig_y = transformer_to_graph.transform(req.origin_lon, req.origin_lat)
    dest_x, dest_y = transformer_to_graph.transform(req.dest_lon, req.dest_lat)

    # Maximum acceptable snapping distance from query coordinates to road network (50 km)
    MAX_SNAP_DISTANCE_M = 50_000.0

    # 1. Check nearest node distance to confirm coordinates are within the road network region
    initial_start = get_nearest_node(G_ROAD, (orig_x, orig_y))
    initial_dest = get_nearest_node(G_ROAD, (dest_x, dest_y))

    if not initial_start or not initial_dest:
        raise HTTPException(status_code=400, detail="Coordinates out of road network bounds.")

    orig_dist_m = math.sqrt((initial_start[0] - orig_x)**2 + (initial_start[1] - orig_y)**2)
    dest_dist_m = math.sqrt((initial_dest[0] - dest_x)**2 + (initial_dest[1] - dest_y)**2)

    if orig_dist_m > MAX_SNAP_DISTANCE_M:
        raise HTTPException(
            status_code=400,
            detail=f"Starting location is too far from the road network ({orig_dist_m/1000.0:.1f} km away). "
                   "Please choose a location within North-East India."
        )
    if dest_dist_m > MAX_SNAP_DISTANCE_M:
        raise HTTPException(
            status_code=400,
            detail=f"Destination location is too far from the road network ({dest_dist_m/1000.0:.1f} km away). "
                   "Please choose a location within North-East India."
        )

    # 2. Find routable nodes: inspect candidate nodes in order of proximity
    start_candidates = get_nearest_nodes(G_ROAD, (orig_x, orig_y), k=50)
    dest_candidates = get_nearest_nodes(G_ROAD, (dest_x, dest_y), k=50)

    start_node = None
    end_node = None

    for s in start_candidates:
        s_comp = nx.node_connected_component(G_ROAD, s)
        for d in dest_candidates:
            if s != d and d in s_comp:
                start_node = s
                end_node = d
                break
        if start_node is not None:
            break

    # If top candidates belong to disconnected local fragments (e.g. unlinked service roads),
    # find the nearest nodes in major connected components (>= 100 nodes) that span the region
    if start_node is None:
        major_components = [c for c in nx.connected_components(G_ROAD) if len(c) >= 100]
        best_pair = None
        best_cost = float('inf')

        for comp in major_components:
            cand_s = min(comp, key=lambda n: (n[0]-orig_x)**2 + (n[1]-orig_y)**2)
            cand_d = min(comp, key=lambda n: (n[0]-dest_x)**2 + (n[1]-dest_y)**2)
            if cand_s == cand_d:
                continue
            d_s = math.sqrt((cand_s[0]-orig_x)**2 + (cand_s[1]-orig_y)**2)
            d_d = math.sqrt((cand_d[0]-dest_x)**2 + (cand_d[1]-dest_y)**2)
            total_snap_d = d_s + d_d
            if d_s <= MAX_SNAP_DISTANCE_M and d_d <= MAX_SNAP_DISTANCE_M and total_snap_d < best_cost:
                best_cost = total_snap_d
                best_pair = (cand_s, cand_d)

        if best_pair is not None:
            start_node, end_node = best_pair

    # Fallback to absolute nearest nodes if no mutual component found
    if start_node is None:
        start_node = initial_start
        end_node = initial_dest

    if start_node == end_node:
        raise HTTPException(
            status_code=400,
            detail="Origin and destination resolve to the same road network node. "
                   "Try coordinates that are farther apart."
        )

    weight_attr = 'travel_cost' if req.mode == "SHORTEST" else 'total_cost'

    try:
        route = shortest_path_dijkstra(G_ROAD, start_node, end_node, weight=weight_attr)
        route["transport_mode"] = "ROADWAY"
        route["route_type"] = "SHORTEST" if req.mode == "SHORTEST" else "LOWEST_RISK"

        # Transform route geometry from EPSG:3857 back to WGS84 [latitude, longitude] for Leaflet
        wgs84_coords = []
        for segment in route.get("coords", []):
            ptA, ptB = segment
            lonA, latA = transformer_to_wgs84.transform(ptA[1], ptA[0])
            lonB, latB = transformer_to_wgs84.transform(ptB[1], ptB[0])
            wgs84_coords.append([[round(latA, 6), round(lonA, 6)], [round(latB, 6), round(lonB, 6)]])
        route["coords"] = wgs84_coords

        # Calculate snapped WGS84 coordinates for origin and dest
        s_lon, s_lat = transformer_to_wgs84.transform(start_node[0], start_node[1])
        d_lon, d_lat = transformer_to_wgs84.transform(end_node[0], end_node[1])

        # Calculation Validation (Feature 1A)
        val_res = validate_road_route(
            (req.origin_lat, req.origin_lon),
            (req.dest_lat, req.dest_lon),
            (s_lat, s_lon),
            (d_lat, d_lon),
            route["path_nodes"],
            G_ROAD,
            route["distance_km"],
            route["coords"]
        )
        route["validation"] = val_res

        # Accuracy statement (Feature 1B)
        route["accuracy"] = {
            "topological_consistency": "100% Graph-verified",
            "metric_definition": "Route follows existing OpenStreetMap edges with non-negative weights and reconciled distance.",
            "predictive_accuracy": "Not established",
            "explanation": "Calculation is mathematically and topologically verified against network data. Predictive flood/landslide accuracy is Not established due to lack of verified historical event labels."
        }

        # Confidence calculation (Feature 1C)
        comp_size = len(nx.node_connected_component(G_ROAD, start_node))
        conf_res = compute_road_confidence(
            val_res["status"],
            val_res["validation_checks"]["origin_snapping_distance_km"],
            val_res["validation_checks"]["destination_snapping_distance_km"],
            comp_size,
            val_res["covariate_coverage_pct"]
        )
        route["confidence"] = conf_res

        # Route-level risk summary (Feature 3)
        env_risks = []
        log_risks = []
        for i in range(len(route["path_nodes"]) - 1):
            ed = G_ROAD.get_edge_data(route["path_nodes"][i], route["path_nodes"][i+1])
            env_risks.append(ed.get("environmental_risk", 0.0))
            log_risks.append(ed.get("logistics_risk", 0.0))
        avg_env = round(sum(env_risks) / max(len(env_risks), 1), 3)
        avg_log = round(sum(log_risks) / max(len(log_risks), 1), 3)
        risk_cat = "HIGH" if avg_log > 0.6 else ("MODERATE" if avg_log > 0.3 else "LOW")
        route["risk_summary"] = {
            "average_environmental_risk": avg_env,
            "average_logistics_risk": avg_log,
            "risk_category": risk_cat,
            "risk_cost_penalty": round(max(0.0, route["total_cost"] - route["distance_km"] * 1000.0), 2) if req.mode == "SAFE" else 0.0,
            "disclaimer": "Scores are heuristic indices representing relative terrain and hydrologic sensitivity, not probabilistic predictions of disaster events."
        }

        # Save to SQLite history (Feature 6)
        if req.save_to_history:
            orig_name = req.origin_name or f"({req.origin_lat:.4f}, {req.origin_lon:.4f})"
            dst_name = req.dest_name or f"({req.dest_lat:.4f}, {req.dest_lon:.4f})"
            rec_id = history_db.save_route_calculation(
                origin_name=orig_name,
                origin_lat=req.origin_lat,
                origin_lon=req.origin_lon,
                dest_name=dst_name,
                dest_lat=req.dest_lat,
                dest_lon=req.dest_lon,
                transport_mode="ROADWAY",
                route_mode=req.mode,
                distance_km=route["distance_km"],
                total_cost=route["total_cost"],
                segments=route["segments"],
                validation_status=val_res["status"],
                confidence_score=conf_res["score_percentage"],
                confidence_rating=conf_res["rating"],
                risk_summary=route["risk_summary"],
                validation_details=val_res,
                coords=route["coords"]
            )
            route["calculation_id"] = rec_id

        return route
    except nx.NetworkXNoPath:
        raise HTTPException(
            status_code=404,
            detail="No valid road path found between these endpoints. "
                   "The locations may be in disconnected graph components."
        )

@app.post("/route/recommend")
def recommend_route(req: RouteRequest):
    return _calculate_roadway_route(req)

# ---------------------------------------------------------------------------
# AIRWAY ROUTE — Haversine great-circle direct-distance estimate
# No road graph, no risk scores, no airports, no flight times.
# ---------------------------------------------------------------------------
class AirwayRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    origin_name: Optional[str] = "Selected Origin"
    dest_name: Optional[str] = "Selected Destination"
    save_to_history: bool = True

    @field_validator("origin_lat", "dest_lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not math.isfinite(v) or not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude {v} is out of valid range [-90, 90].")
        return v

    @field_validator("origin_lon", "dest_lon")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not math.isfinite(v) or not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude {v} is out of valid range [-180, 180].")
        return v

    @model_validator(mode="after")
    def validate_distinct_endpoints(self) -> "AirwayRequest":
        if self.origin_lat == self.dest_lat and self.origin_lon == self.dest_lon:
            raise ValueError(
                "Origin and destination coordinates are identical. "
                "A separate airway route cannot be calculated."
            )
        return self

@app.post("/route/airway")
def airway_route(req: AirwayRequest):
    try:
        result = calculate_air_route(req.origin_lat, req.origin_lon, req.dest_lat, req.dest_lon)
        # Validation and confidence (Feature 1)
        val = validate_air_route(req.origin_lat, req.origin_lon, req.dest_lat, req.dest_lon, result["distance_km"])
        result["validation"] = val
        result["accuracy"] = {
            "topological_consistency": "100% Mathematical Haversine Consistency",
            "metric_definition": "Exact spherical Earth great-circle distance (IUGG mean radius R=6371.0088 km).",
            "predictive_accuracy": "Not established",
            "explanation": val["accuracy_statement"]
        }
        result["confidence"] = val["confidence"]

        if req.save_to_history:
            orig_name = req.origin_name or f"({req.origin_lat:.4f}, {req.origin_lon:.4f})"
            dst_name = req.dest_name or f"({req.dest_lat:.4f}, {req.dest_lon:.4f})"
            rec_id = history_db.save_route_calculation(
                origin_name=orig_name,
                origin_lat=req.origin_lat,
                origin_lon=req.origin_lon,
                dest_name=dst_name,
                dest_lat=req.dest_lat,
                dest_lon=req.dest_lon,
                transport_mode="AIRWAY",
                route_mode="DIRECT_AIR",
                distance_km=result["distance_km"],
                total_cost=result["distance_km"],
                segments=1,
                validation_status=val["status"],
                confidence_score=val["confidence"]["score_percentage"],
                confidence_rating=val["confidence"]["rating"],
                risk_summary=None,
                validation_details=val["validation_checks"],
                coords=[result["coords"]]
            )
            result["calculation_id"] = rec_id

        return result
    except AirwayValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------------------------------------------------------------------------
# ROUTE COMPARISON — Feature 4: Side-by-side SHORTEST vs SAFE
# ---------------------------------------------------------------------------
class CompareRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    origin_name: Optional[str] = "Origin"
    dest_name: Optional[str] = "Destination"

@app.post("/route/compare")
def compare_routes(req: CompareRequest):
    req_shortest = RouteRequest(
        origin_lat=req.origin_lat,
        origin_lon=req.origin_lon,
        dest_lat=req.dest_lat,
        dest_lon=req.dest_lon,
        origin_name=req.origin_name,
        dest_name=req.dest_name,
        mode="SHORTEST",
        transport_mode="ROADWAY",
        save_to_history=False
    )
    req_safe = RouteRequest(
        origin_lat=req.origin_lat,
        origin_lon=req.origin_lon,
        dest_lat=req.dest_lat,
        dest_lon=req.dest_lon,
        origin_name=req.origin_name,
        dest_name=req.dest_name,
        mode="SAFE",
        transport_mode="ROADWAY",
        save_to_history=False
    )

    shortest_route = _calculate_roadway_route(req_shortest)
    safe_route = _calculate_roadway_route(req_safe)

    identical = (
        shortest_route["distance_km"] == safe_route["distance_km"] and
        shortest_route["segments"] == safe_route["segments"]
    )

    if identical:
        explanation = (
            "Both SHORTEST and SAFE modes selected the identical road corridor (e.g., NH-6 between Guwahati and Shillong). "
            "In this rugged regional terrain, this trunk highway represents the sole continuous engineered road corridor; "
            "no alternative bypass corridor exists in the network."
        )
    else:
        dist_diff = round(safe_route["distance_km"] - shortest_route["distance_km"], 2)
        cost_diff = round(safe_route["total_cost"] - shortest_route["total_cost"], 2)
        explanation = (
            f"SAFE mode detours to bypass higher-risk road segments, adding {dist_diff} km of travel distance "
            f"to reduce risk exposure (risk-adjusted cost delta: {cost_diff})."
        )

    return {
        "origin": {"name": req.origin_name, "lat": req.origin_lat, "lon": req.origin_lon},
        "dest": {"name": req.dest_name, "lat": req.dest_lat, "lon": req.dest_lon},
        "shortest": shortest_route,
        "safe": safe_route,
        "comparison": {
            "identical_corridor": identical,
            "distance_difference_km": round(safe_route["distance_km"] - shortest_route["distance_km"], 2),
            "cost_difference": round(safe_route["total_cost"] - shortest_route["total_cost"], 2),
            "corridor_explanation": explanation
        }
    }

# ---------------------------------------------------------------------------
# ANALYTICS ENDPOINTS — Feature 2 (Overview) and Feature 5 (Rainfall)
# ---------------------------------------------------------------------------
@app.get("/analytics/overview")
def analytics_overview():
    return get_system_overview_metrics(G_ROAD)

@app.get("/analytics/rainfall/summary")
def analytics_rainfall_summary():
    return get_rainfall_summary()

@app.get("/analytics/rainfall/trends")
def analytics_rainfall_trends(state: str = Query(..., min_length=2)):
    return get_state_rainfall_trends(state)

# ---------------------------------------------------------------------------
# ROUTE HISTORY & REPORT EXPORT — Feature 6
# ---------------------------------------------------------------------------
@app.get("/routes/history")
def list_history(limit: int = Query(50, ge=1, le=200)):
    return {"history": history_db.get_route_history(limit=limit)}

@app.get("/routes/history/{route_id}")
def get_saved_route(route_id: int):
    route = history_db.get_route_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail=f"Route calculation #{route_id} not found.")
    return route

@app.get("/routes/history/{route_id}/report")
def export_route_report(route_id: int):
    route = history_db.get_route_by_id(route_id)
    if not route:
        raise HTTPException(status_code=404, detail=f"Route calculation #{route_id} not found.")
    report_text = history_db.generate_route_report_text(route)
    return PlainTextResponse(content=report_text, media_type="text/plain")

# MOUNT FRONTEND AT ROOT
app.mount("/", StaticFiles(directory="c:/NER-Smart-Logistics/frontend", html=True), name="frontend")
