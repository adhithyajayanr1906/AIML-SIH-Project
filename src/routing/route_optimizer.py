import math
import networkx as nx
from typing import Dict, Any, List, Tuple, Optional
from config.config import NER_HUBS, NER_ROUTES
from database.database import get_blocked_routes
from src.ml.predict import predict_risk

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth in kilometers.
    """
    R = 6371.0 # Radius of earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearest_road(latitude: float, longitude: float) -> Tuple[str, str, str, float]:
    """
    Find the nearest road edge segment in the graph for a given GPS coordinate.
    Returns (u, v, route_id, distance_km).
    """
    min_dist = float("inf")
    nearest_segment = (None, None, "", float("inf"))

    for u, v, dist_km, time_min, highway in NER_ROUTES:
        u_coords = NER_HUBS[u]
        v_coords = NER_HUBS[v]

        # Calculate midpoint of road segment
        mid_lat = (u_coords["lat"] + v_coords["lat"]) / 2.0
        mid_lon = (u_coords["lon"] + v_coords["lon"]) / 2.0

        d_u = haversine_distance(latitude, longitude, u_coords["lat"], u_coords["lon"])
        d_v = haversine_distance(latitude, longitude, v_coords["lat"], v_coords["lon"])
        d_mid = haversine_distance(latitude, longitude, mid_lat, mid_lon)

        seg_dist = min(d_u, d_v, d_mid)
        route_id_1 = f"{u} - {v}"
        route_id_2 = f"{v} - {u}"

        if seg_dist < min_dist:
            min_dist = seg_dist
            nearest_segment = (u, v, route_id_1, min_dist)

    return nearest_segment

def build_logistics_graph(active_blockages: Optional[List[str]] = None) -> Tuple[nx.Graph, Dict[str, Dict[str, Any]]]:
    """
    Construct NetworkX graph representing the Prototype Demonstration Network.
    Incorporates real environmental predictions and dynamic field report blockages.
    """
    if active_blockages is None:
        active_blockages = get_blocked_routes()

    G = nx.Graph()

    # Add Hub Nodes
    for name, data in NER_HUBS.items():
        G.add_node(name, lat=data["lat"], lon=data["lon"], state=data["state"], district=data["district"])

    edge_details = {}

    for u, v, dist_km, base_time, highway in NER_ROUTES:
        route_id_1 = f"{u} - {v}"
        route_id_2 = f"{v} - {u}"

        is_blocked = (route_id_1 in active_blockages or route_id_2 in active_blockages)

        # Baseline sample environmental features for edge risk inference
        sample_input = {
            "Latitude": (NER_HUBS[u]["lat"] + NER_HUBS[v]["lat"]) / 2.0,
            "Longitude": (NER_HUBS[u]["lon"] + NER_HUBS[v]["lon"]) / 2.0,
            "Rainfall (mm)": 140.0 if "Shillong" in (u, v) or "Silchar" in (u, v) else 80.0,
            "Temperature (°C)": 24.0,
            "Humidity (%)": 82.0,
            "River Discharge (m³/s)": 2800.0 if "Guwahati" in (u, v) or "Tezpur" in (u, v) else 1200.0,
            "Water Level (m)": 5.5 if "Guwahati" in (u, v) else 3.0,
            "Elevation (m)": 1500.0 if "Shillong" in (u, v) or "Kohima" in (u, v) else 200.0,
            "Land Cover": "Forest",
            "Soil Type": "Clay",
            "Population Density": 3000.0,
            "Infrastructure": 1,
            "Historical Floods": 1 if "Guwahati" in (u, v) or "Silchar" in (u, v) else 0
        }

        risk_res = predict_risk(sample_input)
        risk_prob = risk_res["probability"]
        risk_level = risk_res["risk_level"]
        delay_min = risk_res["estimated_delay_minutes"]

        # Cost Functions
        # Fastest: travel_time
        cost_fastest = base_time + delay_min
        # Safest: travel_time * (1.0 + 5.0 * risk_prob)
        cost_safest = (base_time + delay_min) * (1.0 + 5.0 * risk_prob)
        # Balanced: 0.6 * travel_time + 0.4 * risk_penalty
        cost_balanced = 0.6 * (base_time + delay_min) + 0.4 * (risk_prob * 300.0)

        if is_blocked:
            cost_fastest = float("inf")
            cost_safest = float("inf")
            cost_balanced = float("inf")
            status = "BLOCKED"
        elif risk_level == "HIGH":
            status = "HIGH_RISK"
        elif risk_level == "MEDIUM":
            status = "MEDIUM_RISK"
        else:
            status = "OPEN"

        G.add_edge(
            u, v,
            distance_km=dist_km,
            base_time_min=base_time,
            delay_min=delay_min,
            highway=highway,
            risk_prob=risk_prob,
            risk_level=risk_level,
            status=status,
            is_blocked=is_blocked,
            cost_fastest=cost_fastest,
            cost_safest=cost_safest,
            cost_balanced=cost_balanced
        )

        edge_details[route_id_1] = {
            "origin": u,
            "destination": v,
            "distance_km": dist_km,
            "base_time": base_time,
            "delay_min": delay_min,
            "highway": highway,
            "risk_prob": risk_prob,
            "risk_level": risk_level,
            "status": status,
            "is_blocked": is_blocked
        }

    return G, edge_details

def find_optimal_route(
    origin: str,
    destination: str,
    preference: str = "Balanced",
    active_blockages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Calculate optimal route using Dijkstra algorithm over NetworkX graph.
    Returns path, distance, estimated travel time, risk summary, and alternate route.
    """
    if origin not in NER_HUBS or destination not in NER_HUBS:
        raise ValueError(f"Origin '{origin}' or Destination '{destination}' not in NER Hubs network.")

    if origin == destination:
        return {
            "path": [origin],
            "total_distance_km": 0,
            "total_time_min": 0,
            "overall_risk_prob": 0.0,
            "overall_risk_level": "LOW",
            "risky_segments": [],
            "blocked_segments": [],
            "is_rerouted": False,
            "alternate_path": None,
            "preference": preference
        }

    G, edge_details = build_logistics_graph(active_blockages=active_blockages)

    weight_attr = "cost_balanced"
    if preference == "Fastest":
        weight_attr = "cost_fastest"
    elif preference == "Safest":
        weight_attr = "cost_safest"

    try:
        path = nx.dijkstra_path(G, origin, destination, weight=weight_attr)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        # No path available due to road blockages
        return {
            "path": [],
            "total_distance_km": 0,
            "total_time_min": 0,
            "overall_risk_prob": 1.0,
            "overall_risk_level": "HIGH",
            "risky_segments": [],
            "blocked_segments": [f"{origin} - {destination}"],
            "is_rerouted": False,
            "alternate_path": None,
            "preference": preference,
            "error": "No accessible route found due to critical road blockages."
        }

    total_dist = 0
    total_time = 0
    risk_probs = []
    risky_segs = []
    blocked_segs = []

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G[u][v]
        total_dist += edge_data["distance_km"]
        total_time += edge_data["base_time_min"] + edge_data["delay_min"]
        risk_probs.append(edge_data["risk_prob"])

        if edge_data["is_blocked"]:
            blocked_segs.append(f"{u} - {v}")
        elif edge_data["risk_level"] in ["HIGH", "MEDIUM"]:
            risky_segs.append(f"{u} - {v}")

    avg_risk = sum(risk_probs) / max(len(risk_probs), 1)
    
    if avg_risk < 0.35:
        overall_level = "LOW"
    elif avg_risk < 0.70:
        overall_level = "MEDIUM"
    else:
        overall_level = "HIGH"

    # Compute Alternate Path (by removing the highest risk / first edge of primary path)
    alternate_path = None
    if len(path) > 1:
        G_alt = G.copy()
        first_u, first_v = path[0], path[1]
        if G_alt.has_edge(first_u, first_v):
            G_alt.remove_edge(first_u, first_v)
        try:
            alt_p = nx.dijkstra_path(G_alt, origin, destination, weight=weight_attr)
            if alt_p != path:
                alternate_path = alt_p
        except Exception:
            alternate_path = None

    return {
        "path": path,
        "total_distance_km": round(total_dist, 1),
        "total_time_min": int(total_time),
        "overall_risk_prob": round(avg_risk, 4),
        "overall_risk_level": overall_level,
        "risky_segments": risky_segs,
        "blocked_segments": blocked_segs,
        "is_rerouted": len(blocked_segs) > 0,
        "alternate_path": alternate_path,
        "preference": preference
    }
