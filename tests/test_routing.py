import pytest
from src.routing.route_optimizer import (
    build_logistics_graph,
    find_nearest_road,
    find_optimal_route
)
from config.config import NER_HUBS

def test_build_logistics_graph():
    G, edge_details = build_logistics_graph()
    assert G.number_of_nodes() == len(NER_HUBS)
    assert G.number_of_edges() > 0

def test_find_nearest_road():
    # Guwahati coordinates
    u, v, route_id, dist = find_nearest_road(26.1445, 91.7362)
    assert u is not None
    assert v is not None
    assert dist >= 0.0

def test_find_optimal_route_valid():
    res = find_optimal_route("Guwahati", "Imphal", preference="Safest")
    assert "path" in res
    assert len(res["path"]) > 1
    assert res["path"][0] == "Guwahati"
    assert res["path"][-1] == "Imphal"
    assert res["total_distance_km"] > 0
    assert res["total_time_min"] > 0

def test_blocked_edge_rerouting():
    blocked_corridor = ["Guwahati - Shillong"]
    res = find_optimal_route("Guwahati", "Shillong", preference="Balanced", active_blockages=blocked_corridor)
    assert "path" in res
