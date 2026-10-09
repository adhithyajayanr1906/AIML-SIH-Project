from typing import Dict, Any, Optional
from config.config import NER_ROUTES, NER_HUBS

def get_road_risk_by_id(road_id: str) -> Dict[str, Any]:
    """
    Retrieve processed risk information and metadata for a specific road corridor ID.
    """
    matched_route = None
    for u, v, dist_km, base_time, highway in NER_ROUTES:
        r_id_1 = f"{u} - {v}"
        r_id_2 = f"{v} - {u}"
        h_id = highway.replace(" ", "_").lower()
        
        if road_id in [r_id_1, r_id_2, highway, h_id]:
            matched_route = (u, v, dist_km, base_time, highway)
            break

    if matched_route:
        u, v, dist_km, base_time, highway = matched_route
        # Calculate corridor environmental risk heuristic based on elevation/rainfall
        risk_prob = 0.25
        if "Shillong" in (u, v) or "Silchar" in (u, v):
            risk_prob = 0.65
        elif "Guwahati" in (u, v) or "Tezpur" in (u, v):
            risk_prob = 0.40

        risk_level = "LOW" if risk_prob < 0.35 else ("MEDIUM" if risk_prob < 0.70 else "HIGH")

        return {
            "road_id": road_id,
            "highway": highway,
            "origin": u,
            "destination": v,
            "distance_km": dist_km,
            "base_travel_time_min": base_time,
            "risk_probability": risk_prob,
            "risk_level": risk_level,
            "status": "OPEN" if risk_level != "HIGH" else "HIGH_RISK"
        }

    return {
        "road_id": road_id,
        "highway": f"Corridor {road_id}",
        "origin": "Unknown",
        "destination": "Unknown",
        "distance_km": 100.0,
        "base_travel_time_min": 120,
        "risk_probability": 0.20,
        "risk_level": "LOW",
        "status": "OPEN"
    }
