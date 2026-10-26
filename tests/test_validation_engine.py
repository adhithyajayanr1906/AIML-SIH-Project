"""
tests/test_validation_engine.py
===============================
Unit tests for metrics_engine.py covering:
- Boundary conditions & clamping in compute_road_confidence
- Snapping limit thresholds and scoring
- Component scale thresholds and scoring
- Route validation: edge existence, finite non-negative weights, NaN/Inf handling
- Distance reconciliation tolerance
- Coordinate bounds validation (WGS84)
- Covariate coverage separation (available vs missing segments, fallback policy)
- Airway mathematical Haversine validation
"""

import math
import unittest
import networkx as nx

from ml.evaluation.metrics_engine import (
    validate_road_route,
    compute_road_confidence,
    validate_air_route
)


class TestConfidenceCalculation(unittest.TestCase):
    """Tests for compute_road_confidence."""

    def test_confidence_bounds_clamping_upper_and_lower(self):
        """Confidence score must strictly remain between 0.0 and 100.0."""
        # Extreme upper inputs
        res_high = compute_road_confidence("PASSED", 0.0, 0.0, 10000, 150.0)
        self.assertLessEqual(res_high["score_percentage"], 100.0)
        self.assertGreaterEqual(res_high["score_percentage"], 0.0)

        # Extreme lower inputs
        res_low = compute_road_confidence("FAILED", 100.0, 100.0, 0, -50.0)
        self.assertLessEqual(res_low["score_percentage"], 100.0)
        self.assertGreaterEqual(res_low["score_percentage"], 0.0)
        self.assertEqual(res_low["score_percentage"], 0.0)

    def test_confidence_rating_thresholds(self):
        """Qualitative categories match the documented thresholds."""
        # Score >= 80 -> High
        res80 = compute_road_confidence("PASSED", 0.5, 0.5, 1000, 100.0)  # 35 + 30 + 20 + 15 = 100
        self.assertEqual(res80["rating"], "High")
        self.assertEqual(res80["score_percentage"], 100.0)

        # Score in [60, 79.9] -> Moderate
        # 28 (snap 3km) + 22 (comp 500) + 10 (50% cov) + 0 (FAILED val) = 60
        res60 = compute_road_confidence("FAILED", 3.0, 3.0, 500, 50.0)
        self.assertEqual(res60["rating"], "Moderate")
        self.assertEqual(res60["score_percentage"], 60.0)

        # Score in [40, 59.9] -> Low
        # 18 (snap 10km) + 12 (comp 50) + 10 (50% cov) + 0 (val) = 40
        res40 = compute_road_confidence("FAILED", 10.0, 10.0, 50, 50.0)
        self.assertEqual(res40["rating"], "Low")
        self.assertEqual(res40["score_percentage"], 40.0)

        # Score < 40 -> Not Assessed
        # 10 (snap 40km) + 5 (comp 5) + 0 (cov) + 0 (val) = 15
        res_low = compute_road_confidence("FAILED", 40.0, 40.0, 5, 0.0)
        self.assertEqual(res_low["rating"], "Not Assessed")
        self.assertLess(res_low["score_percentage"], 40.0)

    def test_snapping_distance_brackets(self):
        """Snapping distance scoring matches 35 / 28 / 18 / 10 / 0 points."""
        # <= 1.0 km -> 35
        c1 = compute_road_confidence("FAILED", 0.5, 0.5, 0, 0.0)["factors"]["snapping_proximity_pts"]
        self.assertEqual(c1, 35.0)

        # <= 5.0 km -> 28
        c5 = compute_road_confidence("FAILED", 3.0, 3.0, 0, 0.0)["factors"]["snapping_proximity_pts"]
        self.assertEqual(c5, 28.0)

        # <= 15.0 km -> 18
        c15 = compute_road_confidence("FAILED", 10.0, 10.0, 0, 0.0)["factors"]["snapping_proximity_pts"]
        self.assertEqual(c15, 18.0)

        # <= 50.0 km -> 10
        c50 = compute_road_confidence("FAILED", 30.0, 30.0, 0, 0.0)["factors"]["snapping_proximity_pts"]
        self.assertEqual(c50, 10.0)

        # > 50.0 km -> 0
        c_far = compute_road_confidence("FAILED", 60.0, 60.0, 0, 0.0)["factors"]["snapping_proximity_pts"]
        self.assertEqual(c_far, 0.0)

    def test_component_size_brackets(self):
        """Component scale scoring matches 30 / 22 / 12 / 5 / 0 points."""
        # >= 1000 nodes -> 30
        self.assertEqual(compute_road_confidence("FAILED", 100.0, 100.0, 1500, 0.0)["factors"]["network_connectivity_pts"], 30.0)
        # >= 100 nodes -> 22
        self.assertEqual(compute_road_confidence("FAILED", 100.0, 100.0, 500, 0.0)["factors"]["network_connectivity_pts"], 22.0)
        # >= 10 nodes -> 12
        self.assertEqual(compute_road_confidence("FAILED", 100.0, 100.0, 50, 0.0)["factors"]["network_connectivity_pts"], 12.0)
        # >= 2 nodes -> 5
        self.assertEqual(compute_road_confidence("FAILED", 100.0, 100.0, 5, 0.0)["factors"]["network_connectivity_pts"], 5.0)
        # < 2 nodes -> 0
        self.assertEqual(compute_road_confidence("FAILED", 100.0, 100.0, 1, 0.0)["factors"]["network_connectivity_pts"], 0.0)


class TestRouteValidation(unittest.TestCase):
    """Tests for validate_road_route under valid, boundary, and invalid conditions."""

    def setUp(self):
        # Create a mock graph with 3 nodes and 2 edges
        self.graph = nx.DiGraph()
        self.graph.add_node(1, x=91.73, y=26.14)
        self.graph.add_node(2, x=91.80, y=25.80)
        self.graph.add_node(3, x=91.89, y=25.57)

        self.graph.add_edge(1, 2, length_km=50.0, travel_cost=50.0, total_cost=100.0, covariates_available=True)
        self.graph.add_edge(2, 3, length_km=50.0, travel_cost=50.0, total_cost=100.0, covariates_available=False)

    def test_valid_route_passes_all_checks(self):
        """Happy path route passes validation and computes covariate ratio."""
        res = validate_road_route(
            origin_requested=(26.14, 91.73),
            dest_requested=(25.57, 91.89),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.57, 91.89),
            path_nodes=[1, 2, 3],
            graph=self.graph,
            reported_dist_km=100.0,
            route_coords=[[[26.14, 91.73], [25.80, 91.80]], [[25.80, 91.80], [25.57, 91.89]]]
        )
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["validation_checks"]["graph_edges_valid"])
        self.assertTrue(res["validation_checks"]["finite_non_negative_weights"])
        self.assertTrue(res["validation_checks"]["distance_reconciled"])
        self.assertTrue(res["validation_checks"]["coords_valid_wgs84"])
        self.assertTrue(res["validation_checks"]["endpoints_within_snapping_tolerance"])

        cov = res["environmental_coverage"]
        self.assertEqual(cov["total_segments"], 2)
        self.assertEqual(cov["segments_with_covariates"], 1)
        self.assertEqual(cov["segments_missing_covariates"], 1)
        self.assertEqual(cov["coverage_ratio"], 0.5)
        self.assertEqual(cov["coverage_percentage"], 50.0)
        self.assertEqual(cov["status"], "Available")

    def test_missing_edge_in_graph_fails(self):
        """If path specifies an edge not in graph, validation must fail."""
        res = validate_road_route(
            origin_requested=(26.14, 91.73),
            dest_requested=(25.57, 91.89),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.57, 91.89),
            path_nodes=[1, 3], # No direct edge 1 -> 3
            graph=self.graph,
            reported_dist_km=100.0,
            route_coords=[[[26.14, 91.73], [25.57, 91.89]]]
        )
        self.assertEqual(res["status"], "FAILED")
        self.assertFalse(res["validation_checks"]["graph_edges_valid"])

    def test_nan_or_negative_edge_costs_fail(self):
        """Non-finite or negative weights must cause validation to fail."""
        bad_graph = nx.DiGraph()
        bad_graph.add_edge(1, 2, length_km=float('nan'), travel_cost=10.0, total_cost=20.0)

        res_nan = validate_road_route(
            origin_requested=(26.14, 91.73),
            dest_requested=(25.80, 91.80),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.80, 91.80),
            path_nodes=[1, 2],
            graph=bad_graph,
            reported_dist_km=50.0,
            route_coords=[[[26.14, 91.73], [25.80, 91.80]]]
        )
        self.assertEqual(res_nan["status"], "FAILED")
        self.assertFalse(res_nan["validation_checks"]["finite_non_negative_weights"])

        # Negative cost
        neg_graph = nx.DiGraph()
        neg_graph.add_edge(1, 2, length_km=10.0, travel_cost=-5.0, total_cost=10.0)
        res_neg = validate_road_route(
            origin_requested=(26.14, 91.73),
            dest_requested=(25.80, 91.80),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.80, 91.80),
            path_nodes=[1, 2],
            graph=neg_graph,
            reported_dist_km=10.0,
            route_coords=[[[26.14, 91.73], [25.80, 91.80]]]
        )
        self.assertEqual(res_neg["status"], "FAILED")
        self.assertFalse(res_neg["validation_checks"]["finite_non_negative_weights"])

    def test_distance_reconciliation_tolerance(self):
        """Distance differences > 0.05 km must fail reconciliation check."""
        res_fail = validate_road_route(
            origin_requested=(26.14, 91.73),
            dest_requested=(25.57, 91.89),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.57, 91.89),
            path_nodes=[1, 2, 3],
            graph=self.graph,
            reported_dist_km=90.0, # Underlying sum is 100.0 km
            route_coords=[[[26.14, 91.73], [25.80, 91.80]], [[25.80, 91.80], [25.57, 91.89]]]
        )
        self.assertEqual(res_fail["status"], "FAILED")
        self.assertFalse(res_fail["validation_checks"]["distance_reconciled"])

    def test_invalid_wgs84_coordinates_fail(self):
        """Coordinates outside [-90, 90] lat or [-180, 180] lon must fail."""
        res_lat = validate_road_route(
            origin_requested=(26.14, 91.73),
            dest_requested=(25.57, 91.89),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.57, 91.89),
            path_nodes=[1, 2, 3],
            graph=self.graph,
            reported_dist_km=100.0,
            route_coords=[[[95.0, 91.73], [25.80, 91.80]], [[25.80, 91.80], [25.57, 91.89]]] # 95.0 lat invalid
        )
        self.assertEqual(res_lat["status"], "FAILED")
        self.assertFalse(res_lat["validation_checks"]["coords_valid_wgs84"])

    def test_snapping_tolerance_exceeded_fails(self):
        """Snapping distance exceeding 50.0 km fails tolerance check."""
        res_snap = validate_road_route(
            origin_requested=(26.14, 90.00), # ~180 km away from snapped node (26.14, 91.73)
            dest_requested=(25.57, 91.89),
            start_snapped_coords=(26.14, 91.73),
            end_snapped_coords=(25.57, 91.89),
            path_nodes=[1, 2, 3],
            graph=self.graph,
            reported_dist_km=100.0,
            route_coords=[[[26.14, 91.73], [25.80, 91.80]], [[25.80, 91.80], [25.57, 91.89]]]
        )
        self.assertEqual(res_snap["status"], "FAILED")
        self.assertFalse(res_snap["validation_checks"]["endpoints_within_snapping_tolerance"])


class TestAirwayValidation(unittest.TestCase):
    """Tests for validate_air_route."""

    def test_airway_matches_haversine(self):
        """Known distance Guwahati to Shillong (~64.837 km) passes with exact reference."""
        res = validate_air_route(26.1445, 91.7362, 25.5788, 91.8933, 64.837)
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["validation_checks"]["mathematical_match"])
        self.assertTrue(res["validation_checks"]["wgs84_bounds_valid"])

    def test_airway_distance_mismatch_fails(self):
        """Incorrect distance fails mathematical match."""
        res = validate_air_route(26.1445, 91.7362, 25.5788, 91.8933, 100.0)
        self.assertEqual(res["status"], "FAILED")
        self.assertFalse(res["validation_checks"]["mathematical_match"])


if __name__ == "__main__":
    unittest.main()
