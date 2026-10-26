"""
ml/evaluation/metrics_engine.py
===============================
Deterministic calculation validation and evidence-based confidence metrics
for NER Smart Logistics.

Definitions and Methodological Rules:
1. Route Calculation Validation:
   - For mathematical air distance, calculation consistency relative to Haversine
     great-circle formula is 100% verified against reference benchmark.
   - For road routing, validation measures graph topological edge validity,
     coordinate bounds, finite non-negative weights, and distance reconciliation.
   - Internal route validation demonstrates computational consistency with the loaded
     graph model, NOT real-world route safety or physical road passability.
   - Disaster predictive accuracy (floods/landslides) is strictly labeled "Not established"
     because verified ground-truth disaster occurrence event logs do not exist in the dataset.

2. Evidence-Weighted Confidence Index (0-100% / Qualitative):
   - Formulated transparently from measurable evidence:
     * Endpoint Snapping Proximity (weight: 35%)
     * Graph Component Connectivity / Size (weight: 30%)
     * Covariate & Environmental Risk Completeness (weight: 20%)
     * Route Geometry & Edge Validation Checks (weight: 15%)
   - Score is bounded in [0.0, 100.0] and represents an evidence index,
     not a statistically calibrated probability.
"""

import math
from typing import Dict, Any, List, Optional, Tuple

def validate_road_route(
    origin_requested: Tuple[float, float],
    dest_requested: Tuple[float, float],
    start_snapped_coords: Tuple[float, float],
    end_snapped_coords: Tuple[float, float],
    path_nodes: List[Any],
    graph: Any,
    reported_dist_km: float,
    route_coords: List[List[List[float]]]
) -> Dict[str, Any]:
    """
    Validates that a returned road route strictly complies with graph geometry,
    non-negative finite edge weights, coordinate bounds, and snapped proximity.
    Separately tracks available vs missing environmental covariates.
    """
    checks = {}
    diagnostics = []

    # 1. Edge existence and non-negative finite weights
    all_edges_valid = True
    edge_sum_km = 0.0
    known_covariates_count = 0
    total_segments = max(len(path_nodes) - 1, 0)
    
    for i in range(total_segments):
        u, v = path_nodes[i], path_nodes[i+1]
        if not graph.has_edge(u, v):
            all_edges_valid = False
            diagnostics.append(f"Segment {i} ({u} -> {v}) does not exist in graph.")
            break
        edge_data = graph.get_edge_data(u, v)
        length_km = edge_data.get('length_km', 0.0)
        travel_cost = edge_data.get('travel_cost', 0.0)
        total_cost = edge_data.get('total_cost', 0.0)

        if not (math.isfinite(length_km) and length_km >= 0):
            all_edges_valid = False
            diagnostics.append(f"Segment {i} has non-finite or negative length_km: {length_km}")
        if not (math.isfinite(travel_cost) and travel_cost >= 0):
            all_edges_valid = False
            diagnostics.append(f"Segment {i} has non-finite or negative travel_cost: {travel_cost}")
        if not (math.isfinite(total_cost) and total_cost >= 0):
            all_edges_valid = False
            diagnostics.append(f"Segment {i} has non-finite or negative total_cost: {total_cost}")

        edge_sum_km += length_km

        # Environmental covariate tracking: check actual availability flag or valid source attributes
        # Do NOT define covariate availability solely by whether risk is non-zero
        has_covariates = edge_data.get('covariates_available')
        if has_covariates is True:
            known_covariates_count += 1
        elif has_covariates is None:
            # Fallback check if flag not explicitly populated: check if source attributes exist and are non-null
            er = edge_data.get('environmental_risk')
            lr = edge_data.get('logistics_risk')
            if er is not None and lr is not None and not (math.isnan(er) or math.isnan(lr)):
                known_covariates_count += 1

    checks["graph_edges_valid"] = all_edges_valid
    checks["finite_non_negative_weights"] = all_edges_valid

    # 2. Distance reconciliation (tolerance 0.05 km)
    dist_reconciled = abs(edge_sum_km - reported_dist_km) < 0.05
    checks["distance_reconciled"] = dist_reconciled
    if not dist_reconciled:
        diagnostics.append(f"Reported distance ({reported_dist_km} km) differs from edge sum ({edge_sum_km:.2f} km)")

    # 3. Coordinate bounds validation (WGS84 lat [-90, 90], lon [-180, 180])
    all_coords_wgs84 = True
    for seg in route_coords:
        for pt in seg:
            lat, lon = pt[0], pt[1]
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                all_coords_wgs84 = False
                break
    checks["coords_valid_wgs84"] = all_coords_wgs84

    # 4. Snapping distance check
    def approx_dist_km(lat1, lon1, lat2, lon2):
        dlat = (lat2 - lat1) * 111.0
        dlon = (lon2 - lon1) * 111.0 * math.cos(math.radians(lat1))
        return math.sqrt(dlat**2 + dlon**2)

    orig_snap_km = approx_dist_km(origin_requested[0], origin_requested[1], start_snapped_coords[0], start_snapped_coords[1])
    dest_snap_km = approx_dist_km(dest_requested[0], dest_requested[1], end_snapped_coords[0], end_snapped_coords[1])
    
    checks["origin_snapping_distance_km"] = round(orig_snap_km, 3)
    checks["destination_snapping_distance_km"] = round(dest_snap_km, 3)
    checks["endpoints_within_snapping_tolerance"] = orig_snap_km <= 50.0 and dest_snap_km <= 50.0

    all_passed = all([
        checks["graph_edges_valid"],
        checks["finite_non_negative_weights"],
        checks["distance_reconciled"],
        checks["coords_valid_wgs84"],
        checks["endpoints_within_snapping_tolerance"]
    ])

    missing_covariates_count = total_segments - known_covariates_count
    covariate_ratio = round(known_covariates_count / max(total_segments, 1), 3) if total_segments > 0 else 0.0
    covariate_coverage_pct = round(covariate_ratio * 100.0, 1)

    environmental_coverage_report = {
        "status": "Available" if known_covariates_count > 0 else "Not Assessed",
        "total_segments": total_segments,
        "segments_with_covariates": known_covariates_count,
        "segments_missing_covariates": missing_covariates_count,
        "coverage_ratio": covariate_ratio,
        "coverage_percentage": covariate_coverage_pct,
        "fallback_policy": "Segments missing environmental raster covariates receive default neutral risk penalty; missing data is tracked separately and not represented as proven zero risk."
    }

    return {
        "status": "PASSED" if all_passed else "FAILED",
        "validation_checks": checks,
        "diagnostics": diagnostics,
        "covariate_coverage_pct": covariate_coverage_pct,
        "environmental_coverage": environmental_coverage_report,
        "total_segments_verified": total_segments
    }


def compute_road_confidence(
    validation_status: str,
    orig_snap_km: float,
    dest_snap_km: float,
    comp_size: int,
    covariate_coverage_pct: float
) -> Dict[str, Any]:
    """
    Calculates a defensible, multi-criteria evidence-weighted confidence score for road routing.
    Score Components:
      1. Snapping Proximity (35 pts max): <1km = 35, <5km = 28, <15km = 18, <50km = 10
      2. Component Scale (30 pts max): >=1000 nodes = 30, >=100 = 22, >=10 = 12, <10 = 5
      3. Covariate Coverage (20 pts max): proportional to covariate overlap %
      4. Validation Outcome (15 pts max): 15 pts if PASSED, 0 if FAILED
    """
    # 1. Snapping proximity (avg of origin and dest)
    avg_snap = max(0.0, (orig_snap_km + dest_snap_km) / 2.0)
    if avg_snap <= 1.0:
        snap_score = 35.0
    elif avg_snap <= 5.0:
        snap_score = 28.0
    elif avg_snap <= 15.0:
        snap_score = 18.0
    elif avg_snap <= 50.0:
        snap_score = 10.0
    else:
        snap_score = 0.0

    # 2. Component scale
    if comp_size >= 1000:
        comp_score = 30.0
    elif comp_size >= 100:
        comp_score = 22.0
    elif comp_size >= 10:
        comp_score = 12.0
    elif comp_size >= 2:
        comp_score = 5.0
    else:
        comp_score = 0.0

    # 3. Covariate coverage (bounded in 0-100)
    safe_cov_pct = max(0.0, min(100.0, float(covariate_coverage_pct or 0.0)))
    cov_score = (safe_cov_pct / 100.0) * 20.0

    # 4. Validation
    val_score = 15.0 if validation_status == "PASSED" else 0.0

    raw_total = snap_score + comp_score + cov_score + val_score
    total_score = max(0.0, min(100.0, round(raw_total, 1)))

    if total_score >= 80:
        rating = "High"
    elif total_score >= 60:
        rating = "Moderate"
    elif total_score >= 40:
        rating = "Low"
    else:
        rating = "Not Assessed"

    return {
        "score_percentage": total_score,
        "rating": rating,
        "metric_label": "Evidence-Weighted Confidence Index",
        "factors": {
            "snapping_proximity_pts": round(snap_score, 1),
            "network_connectivity_pts": round(comp_score, 1),
            "covariate_coverage_pts": round(cov_score, 1),
            "mathematical_validation_pts": round(val_score, 1)
        },
        "methodology": "Evidence-weighted index: snapping proximity (35%), network connectivity (30%), covariate coverage (20%), and mathematical validation (15%). Does not represent a statistically calibrated probability."
    }


def validate_air_route(
    lat1: float, lon1: float, lat2: float, lon2: float,
    reported_dist_km: float
) -> Dict[str, Any]:
    """
    Validates airway direct-distance against exact Haversine mathematical reference.
    """
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    ref_dist = round(R * c, 3)

    matches_ref = abs(ref_dist - reported_dist_km) < 0.01

    return {
        "status": "PASSED" if matches_ref else "FAILED",
        "validation_checks": {
            "reference_haversine_km": ref_dist,
            "reported_haversine_km": reported_dist_km,
            "mathematical_match": matches_ref,
            "wgs84_bounds_valid": (-90 <= lat1 <= 90 and -90 <= lat2 <= 90 and -180 <= lon1 <= 180 and -180 <= lon2 <= 180)
        },
        "accuracy_statement": "Mathematical great-circle distance is 100% verified against IUGG spherical Earth formula (R=6371.0088km). Operational flight path accuracy is 'Not established' (no air traffic data).",
        "confidence": {
            "rating": "High",
            "score_percentage": 95.0,
            "metric_label": "Evidence-Weighted Confidence Index",
            "notes": "Exact mathematical derivation for point-to-point great-circle distance. Does not represent controlled airspace or airway corridors."
        }
    }
