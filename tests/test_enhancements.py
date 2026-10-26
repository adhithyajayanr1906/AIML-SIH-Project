"""
tests/test_enhancements.py
==========================
Comprehensive tests for NER Smart Logistics Platform Master Enhancements:
- Feature 1: Calculation Validation, Accuracy Semantics, Evidence Confidence Scoring
- Feature 2: Logistics Overview Dashboard API
- Feature 3: Environmental & Logistics Risk Engine Outputs
- Feature 4: Route Comparison (SHORTEST vs SAFE Corridor Analysis)
- Feature 5: Rainfall Analytics & Climatology Trends
- Feature 6: Route History Persistence & Audit Report Export
- Feature 8: Backend & Data Integrity
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath("c:/NER-Smart-Logistics")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app
import backend.app.history_db as history_db
from ml.evaluation.metrics_engine import validate_road_route, compute_road_confidence, validate_air_route
from ml.analytics.rainfall_analytics import get_rainfall_summary, get_state_rainfall_trends
from ml.analytics.overview_metrics import get_system_overview_metrics

class TestEnhancements(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Ensure graph is loaded
        with cls.client:
            pass

    def test_01_metrics_engine_airway_haversine_validation(self):
        """Feature 1A: Airway Haversine reference validation."""
        # Known Guwahati (26.1445, 91.7362) to Shillong (25.5788, 91.8933)
        res = validate_air_route(26.1445, 91.7362, 25.5788, 91.8933, 64.837)
        self.assertEqual(res["status"], "PASSED")
        self.assertTrue(res["validation_checks"]["mathematical_match"])
        self.assertIn("100% verified", res["accuracy_statement"])
        self.assertEqual(res["confidence"]["rating"], "High")

    def test_02_confidence_score_evidence_weighting(self):
        """Feature 1C: Confidence score calculation across quality tiers."""
        # High quality: near snapping (<1km), large component (>=1000), 100% covariates, passed validation
        high_conf = compute_road_confidence("PASSED", 0.5, 0.8, 5000, 100.0)
        self.assertEqual(high_conf["rating"], "High")
        self.assertGreaterEqual(high_conf["score_percentage"], 80.0)

        # Low quality: distant snapping (>15km), tiny component (<10), 0% covariates, failed validation
        low_conf = compute_road_confidence("FAILED", 25.0, 30.0, 5, 0.0)
        self.assertIn(low_conf["rating"], ["Low", "Not Assessed"])
        self.assertLess(low_conf["score_percentage"], 50.0)

    def test_03_accuracy_statement_semantics(self):
        """Feature 1B: Accuracy statements distinguish graph consistency from flood prediction."""
        with self.client as c:
            resp = c.post("/route/airway", json={
                "origin_lat": 26.1445, "origin_lon": 91.7362,
                "dest_lat": 25.5788, "dest_lon": 91.8933
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["accuracy"]["predictive_accuracy"], "Not established")
            self.assertIn("Mathematical Haversine", data["accuracy"]["topological_consistency"])

    def test_04_logistics_overview_metrics_endpoint(self):
        """Feature 2: Overview endpoint returns actual road network statistics."""
        with self.client as c:
            resp = c.get("/analytics/overview")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            # Verify actual road network metrics
            self.assertEqual(data["road_network"]["total_nodes"], 456137)
            self.assertEqual(data["road_network"]["total_edges"], 264554)
            self.assertEqual(data["road_network"]["total_road_length_km"], 166530.99)
            self.assertEqual(data["road_network"]["connected_components_count"], 192225)
            self.assertEqual(data["road_network"]["largest_connected_component_nodes"], 5778)
            self.assertEqual(data["runtime_health"]["api_status"], "ONLINE")

    def test_05_rainfall_summary_endpoint(self):
        """Feature 5: Rainfall summary returns full 8-state historical metadata."""
        with self.client as c:
            resp = c.get("/analytics/rainfall/summary")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            self.assertEqual(data["status"], "AVAILABLE")
            self.assertEqual(data["data_quality"]["completeness_pct"], 100.0)
            self.assertEqual(data["data_quality"]["missing_actual_values"], 0)
            self.assertEqual(len(data["states"]), 8)

            state_names = [s["state_name"] for s in data["states"]]
            self.assertIn("Meghalaya", state_names)
            self.assertIn("Assam", state_names)

    def test_06_rainfall_trends_endpoint(self):
        """Feature 5: Monthly climatology and annual anomaly trends for Meghalaya."""
        with self.client as c:
            resp = c.get("/analytics/rainfall/trends?state=Meghalaya")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            self.assertEqual(data["state_name"], "Meghalaya")
            self.assertEqual(len(data["monthly_climatology"]), 12)
            self.assertGreater(len(data["annual_trends"]), 10)
            self.assertIn("caveat", data)

    def test_07_route_comparison_identical_corridor(self):
        """Feature 4: Route comparison recognizes single continuous corridor."""
        with self.client as c:
            resp = c.post("/route/compare", json={
                "origin_lat": 26.1445, "origin_lon": 91.7362,
                "dest_lat": 25.5788, "dest_lon": 91.8933,
                "origin_name": "Guwahati", "dest_name": "Shillong"
            })
            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            self.assertTrue(data["comparison"]["identical_corridor"])
            self.assertEqual(data["shortest"]["distance_km"], data["safe"]["distance_km"])
            self.assertIn("NH-6", data["comparison"]["corridor_explanation"])
            self.assertEqual(data["shortest"]["validation"]["status"], "PASSED")
            self.assertIn(data["safe"]["confidence"]["rating"], ["High", "Moderate"])

    def test_08_history_persistence_and_report_export(self):
        """Feature 6: Route calculation persistence and plain text audit report."""
        with self.client as c:
            # 1. Perform route recommendation
            route_resp = c.post("/route/recommend", json={
                "origin_lat": 26.1445, "origin_lon": 91.7362,
                "dest_lat": 25.5788, "dest_lon": 91.8933,
                "origin_name": "Guwahati Test",
                "dest_name": "Shillong Test",
                "mode": "SHORTEST",
                "transport_mode": "ROADWAY",
                "save_to_history": True
            })
            self.assertEqual(route_resp.status_code, 200)
            route_data = route_resp.json()
            calc_id = route_data.get("calculation_id")
            self.assertIsNotNone(calc_id)

            # 2. Query history list
            hist_resp = c.get("/routes/history")
            self.assertEqual(hist_resp.status_code, 200)
            history_list = hist_resp.json()["history"]
            self.assertTrue(any(item["id"] == calc_id for item in history_list))

            # 3. Retrieve calculation details
            item_resp = c.get(f"/routes/history/{calc_id}")
            self.assertEqual(item_resp.status_code, 200)
            saved_item = item_resp.json()
            self.assertEqual(saved_item["origin_name"], "Guwahati Test")
            self.assertEqual(saved_item["validation_status"], "PASSED")

            # 4. Export audit report
            report_resp = c.get(f"/routes/history/{calc_id}/report")
            self.assertEqual(report_resp.status_code, 200)
            report_text = report_resp.text
            self.assertIn("INTELLIGENCE ROUTE & RISK AUDIT REPORT", report_text)
            self.assertIn("Not established", report_text)
            self.assertIn("Guwahati Test", report_text)

    def test_09_environmental_risk_calculator(self):
        """Feature 3: Environmental and logistics risk calculation endpoints."""
        with self.client as c:
            env_resp = c.post("/predict/environmental-risk", json={
                "rainfall_anomaly": 15.0,
                "extreme_indicator": 1,
                "slope": 20.0,
                "elev": 1500.0,
                "ndvi": 0.4
            })
            self.assertEqual(env_resp.status_code, 200)
            env_data = env_resp.json()
            self.assertTrue(0.0 <= env_data["risk_score"] <= 1.0)
            self.assertIn(env_data["risk_category"], ["LOW", "MODERATE", "HIGH", "CRITICAL"])

            log_resp = c.post("/predict/logistics-risk", json={
                "env_risk_score": env_data["risk_score"],
                "length_m": 2500.0,
                "road_type": "primary"
            })
            self.assertEqual(log_resp.status_code, 200)
            log_data = log_resp.json()
            self.assertTrue(0.0 <= log_data["logistics_risk_score"] <= 1.0)

    def test_10_error_handling_disconnected_endpoints(self):
        """Feature 8: Coordinates beyond 50km tolerance return 400."""
        with self.client as c:
            resp = c.post("/route/recommend", json={
                "origin_lat": 10.0, "origin_lon": 70.0, # Far out in Arabian Sea
                "dest_lat": 25.5788, "dest_lon": 91.8933,
                "mode": "SHORTEST",
                "transport_mode": "ROADWAY"
            })
            self.assertEqual(resp.status_code, 400)
            self.assertIn("too far", resp.json()["detail"].lower())

    def test_11_report_loading_failure_handling(self):
        """Regression test: Report loading failure returns 404/422 and structured error detail."""
        with self.client as c:
            # 1. Non-existent calculation ID report returns 404 with structured detail
            resp_404 = c.get("/routes/history/9999999/report")
            self.assertEqual(resp_404.status_code, 404)
            data_404 = resp_404.json()
            self.assertIn("detail", data_404)
            self.assertIn("9999999", data_404["detail"])

            # 2. Non-existent calculation details route returns 404
            resp_detail_404 = c.get("/routes/history/9999999")
            self.assertEqual(resp_detail_404.status_code, 404)
            self.assertIn("9999999", resp_detail_404.json()["detail"])

            # 3. Invalid non-integer ID returns 422 Unprocessable Entity
            resp_422 = c.get("/routes/history/not_an_int/report")
            self.assertEqual(resp_422.status_code, 422)

if __name__ == "__main__":
    unittest.main()
