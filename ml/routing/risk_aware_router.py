import math
import networkx as nx
from typing import Dict, Any, List, Tuple, Optional
from config.config import NER_HUBS, NER_ROUTES
from src.routing.route_optimizer import build_logistics_graph, haversine_distance, find_nearest_road

def find_node_by_name_or_coords(param: Any) -> Optional[str]:
    """
    Map coordinate object {lat, lon} or name string to nearest network graph hub node.
    """
    if isinstance(param, str) and param in NER_HUBS:
        return param

    if isinstance(param, dict) and "lat" in param and "lon" in param:
        lat = float(param["lat"])
        lon = float(param["lon"])
        min_dist = float("inf")
        closest_node = None
        for name, coords in NER_HUBS.items():
            d = haversine_distance(lat, lon, coords["lat"], coords["lon"])
            if d < min_dist:
                min_dist = d
                closest_node = name
        return closest_node

    if isinstance(param, (list, tuple)) and len(param) >= 2:
        lat = float(param[0])
        lon = float(param[1])
        min_dist = float("inf")
        closest_node = None
        for name, coords in NER_HUBS.items():
            d = haversine_distance(lat, lon, coords["lat"], coords["lon"])
            if d < min_dist:
                min_dist = d
                closest_node = name
        return closest_node

    return None

def compute_routes(
    origin_param: Any,
    destination_param: Any,
    preference: str = "risk_aware"
) -> Dict[str, Any]:
    """
    Compute shortest path and risk-aware path between origin and destination hubs.
    """
    origin_node = find_node_by_name_or_coords(origin_param)
    dest_node = find_node_by_name_or_coords(destination_param)

    if not origin_node or not dest_node:
        return {
            "status": "unavailable",
            "message": "Origin or destination could not be mapped to the regional road graph.",
            "shortest_route": None,
            "risk_aware_route": None
        }

    if origin_node == dest_node:
        coords = [NER_HUBS[origin_node]["lat"], NER_HUBS[origin_node]["lon"]]
        single_route = {
            "path": [origin_node],
            "geometry": [coords],
            "distance_km": 0.0,
            "travel_time_min": 0,
            "risk_score": 0.0,
            "risk_level": "LOW",
            "cost": 0.0,
            "algorithm": "Dijkstra"
        }
        return {
            "status": "success",
            "message": "Origin and destination are the same location.",
            "shortest_route": single_route,
            "risk_aware_route": single_route
        }

    G, edge_details = build_logistics_graph()

    # 1. Shortest Route (Dijkstra using base travel time / distance)
    try:
        shortest_path = nx.dijkstra_path(G, origin_node, dest_node, weight="base_time_min")
        shortest_dist = 0.0
        shortest_time = 0.0
        shortest_probs = []
        shortest_geom = []

        for node in shortest_path:
            shortest_geom.append([NER_HUBS[node]["lat"], NER_HUBS[node]["lon"]])

        for i in range(len(shortest_path) - 1):
            u, v = shortest_path[i], shortest_path[i + 1]
            e = G[u][v]
            shortest_dist += e["distance_km"]
            shortest_time += e["base_time_min"]
            shortest_probs.append(e["risk_prob"])

        avg_prob = sum(shortest_probs) / max(len(shortest_probs), 1)
        shortest_route = {
            "path": shortest_path,
            "geometry": shortest_geom,
            "distance_km": round(shortest_dist, 1),
            "travel_time_min": int(shortest_time),
            "risk_score": round(avg_prob, 4),
            "risk_level": "LOW" if avg_prob < 0.35 else ("MEDIUM" if avg_prob < 0.70 else "HIGH"),
            "cost": round(shortest_time, 1),
            "algorithm": "Dijkstra Shortest Path"
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        shortest_route = None

    # 2. Risk-Aware Route (A* / Dijkstra using cost_safest)
    try:
        def heuristic(u, v):
            return haversine_distance(NER_HUBS[u]["lat"], NER_HUBS[u]["lon"], NER_HUBS[v]["lat"], NER_HUBS[v]["lon"])

        risk_path = nx.astype = nx.astar_path(G, origin_node, dest_node, heuristic=heuristic, weight="cost_safest")
        risk_dist = 0.0
        risk_time = 0.0
        risk_probs = []
        risk_geom = []

        for node in risk_path:
            risk_geom.append([NER_HUBS[node]["lat"], NER_HUBS[node]["lon"]])

        for i in range(len(risk_path) - 1):
            u, v = risk_path[i], risk_path[i + 1]
            e = G[u][v]
            risk_dist += e["distance_km"]
            risk_time += e["base_time_min"] + e["delay_min"]
            risk_probs.append(e["risk_prob"])

        avg_risk_prob = sum(risk_probs) / max(len(risk_probs), 1)
        risk_aware_route = {
            "path": risk_path,
            "geometry": risk_geom,
            "distance_km": round(risk_dist, 1),
            "travel_time_min": int(risk_time),
            "risk_score": round(avg_risk_prob, 4),
            "risk_level": "LOW" if avg_risk_prob < 0.35 else ("MEDIUM" if avg_risk_prob < 0.70 else "HIGH"),
            "cost": round(risk_time * (1.0 + avg_risk_prob), 1),
            "algorithm": "A* Risk-Aware Path"
        }
    except Exception:
        risk_aware_route = shortest_route

    if not shortest_route and not risk_aware_route:
        return {
            "status": "unavailable",
            "message": f"No connected road network path found between {origin_node} and {dest_node}.",
            "shortest_route": None,
            "risk_aware_route": None
        }

    return {
        "status": "success",
        "origin": origin_node,
        "destination": dest_node,
        "shortest_route": shortest_route,
        "risk_aware_route": risk_aware_route or shortest_route
    }
