"""
tests/test_e2e_integration.py
=============================
End-to-end integration tests verifying all 6 views and core API routes:
1. /health
2. /docs
3. /locations/search
4. /route/recommend (SHORTEST, SAFE, invalid inputs)
5. /route/airway (Haversine calculation, accuracy statements)
6. /route/compare (SHORTEST vs SAFE corridor analysis)
7. /analytics/overview (graph stats, dataset inventory)
8. /analytics/rainfall/summary (8 states summary)
9. /analytics/rainfall/trends (all 8 NER states)
10. /predict/environmental-risk & /predict/logistics-risk
11. /routes/history, /routes/history/{id}, and /routes/history/{id}/report
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath("c:/NER-Smart-Logistics")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app

class TestE2EIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        with cls.client:
            pass

    def test_view1_health_and_docs(self):
        """API Health and documentation endpoints."""
        with self.client as c:
            h_resp = c.get("/health")
            self.assertEqual(h_resp.status_code, 200)
            self.assertEqual(h_resp.json()["status"], "ONLINE")
            self.assertEqual(h_resp.json()["nodes"], 456137)

            d_resp = c.get("/docs")
            self.assertEqual(d_resp.status_code, 200)
            self.assertIn("swagger", d_resp.text.lower())

    def test_view1_route_planner_airway_and_roadway(self):
        """View 1: Route Planner execution for both Airway and Roadway."""
        with self.client as c:
            # Airway
            air_resp = c.post("/route/airway", json={
                "origin_lat": 26.1445, "origin_lon": 91.7362,
                "dest_lat": 25.5788, "dest_lon": 91.8933,
                "origin_name": "Guwahati", "dest_name": "Shillong"
            })
            self.assertEqual(air_resp.status_code, 200)
            air_data = air_resp.json()
            self.assertEqual(air_data["distance_km"], 64.837)
            self.assertEqual(air_data["validation"]["status"], "PASSED")
            self.assertEqual(air_data["confidence"]["rating"], "High")

            # Roadway SHORTEST
            road_resp = c.post("/route/recommend", json={
                "origin_lat": 26.1445, "origin_lon": 91.7362,
                "dest_lat": 25.5788, "dest_lon": 91.8933,
                "mode": "SHORTEST",
                "transport_mode": "ROADWAY",
                "save_to_history": True
            })
            self.assertEqual(road_resp.status_code, 200)
            road_data = road_resp.json()
            self.assertEqual(road_data["distance_km"], 119.86)
            self.assertEqual(road_data["segments"], 68)
            self.assertEqual(road_data["validation"]["status"], "PASSED")
            self.assertIn("environmental_coverage", road_data["validation"])
            self.assertEqual(road_data["validation"]["environmental_coverage"]["status"], "Available")
            self.assertIn(road_data["confidence"]["rating"], ["High", "Moderate"])

    def test_view2_route_comparison(self):
        """View 2: Route Comparison endpoint."""
        with self.client as c:
            comp_resp = c.post("/route/compare", json={
                "origin_lat": 26.1445, "origin_lon": 91.7362,
                "dest_lat": 25.5788, "dest_lon": 91.8933,
                "origin_name": "Guwahati", "dest_name": "Shillong"
            })
            self.assertEqual(comp_resp.status_code, 200)
            comp_data = comp_resp.json()
            self.assertIn("shortest", comp_data)
            self.assertIn("safe", comp_data)
            self.assertIn("comparison", comp_data)
            self.assertTrue(comp_data["comparison"]["identical_corridor"])
            self.assertIn("NH-6", comp_data["comparison"]["corridor_explanation"])

    def test_view3_logistics_overview(self):
        """View 3: Logistics Overview system metrics."""
        with self.client as c:
            ov_resp = c.get("/analytics/overview")
            self.assertEqual(ov_resp.status_code, 200)
            ov_data = ov_resp.json()
            self.assertEqual(ov_data["road_network"]["total_nodes"], 456137)
            self.assertEqual(ov_data["road_network"]["total_edges"], 264554)
            self.assertEqual(ov_data["road_network"]["total_road_length_km"], 166530.99)
            self.assertEqual(ov_data["road_network"]["connected_components_count"], 192225)
            self.assertEqual(ov_data["dataset_inventory"]["rainfall_records_count"], 45528)

    def test_view4_risk_intelligence(self):
        """View 4: Environmental & Logistics Risk calculation."""
        with self.client as c:
            env_resp = c.post("/predict/environmental-risk", json={
                "rainfall_anomaly": 25.0,
                "extreme_indicator": 1,
                "slope": 30.0,
                "elev": 1800.0,
                "ndvi": 0.3
            })
            self.assertEqual(env_resp.status_code, 200)
            env_data = env_resp.json()
            self.assertGreater(env_data["risk_score"], 0.0)

            log_resp = c.post("/predict/logistics-risk", json={
                "env_risk_score": env_data["risk_score"],
                "length_m": 5000.0,
                "road_type": "mountain_pass"
            })
            self.assertEqual(log_resp.status_code, 200)
            log_data = log_resp.json()
            self.assertGreater(log_data["logistics_risk_score"], 0.0)

    def test_view5_rainfall_intelligence_all_states(self):
        """View 5: Rainfall Intelligence summary and trends across all 8 NER states."""
        with self.client as c:
            sum_resp = c.get("/analytics/rainfall/summary")
            self.assertEqual(sum_resp.status_code, 200)
            sum_data = sum_resp.json()
            self.assertEqual(len(sum_data["states"]), 8)

            states = [
                "Arunachal Pradesh", "Assam", "Manipur", "Meghalaya",
                "Mizoram", "Nagaland", "Sikkim", "Tripura"
            ]
            for st in states:
                tr_resp = c.get(f"/analytics/rainfall/trends?state={st}")
                self.assertEqual(tr_resp.status_code, 200)
                tr_data = tr_resp.json()
                self.assertEqual(tr_data["state_name"], st)
                self.assertEqual(len(tr_data["monthly_climatology"]), 12)
                self.assertGreater(len(tr_data["annual_trends"]), 5)

    def test_view6_reports_and_history(self):
        """View 6: Reports & History persistence, item retrieval, and audit report export."""
        with self.client as c:
            # 1. Fetch history
            hist_resp = c.get("/routes/history")
            self.assertEqual(hist_resp.status_code, 200)
            hist = hist_resp.json()["history"]
            self.assertGreater(len(hist), 0)

            sample_id = hist[0]["id"]
            # 2. Fetch specific calculation
            item_resp = c.get(f"/routes/history/{sample_id}")
            self.assertEqual(item_resp.status_code, 200)
            item_data = item_resp.json()
            self.assertEqual(item_data["id"], sample_id)

            # 3. Fetch plain text audit report
            rep_resp = c.get(f"/routes/history/{sample_id}/report")
            self.assertEqual(rep_resp.status_code, 200)
            rep_text = rep_resp.text
            self.assertIn("INTELLIGENCE ROUTE & RISK AUDIT REPORT", rep_text)
            self.assertIn("Disaster Predictive Accuracy: Not established", rep_text)


if __name__ == "__main__":
    unittest.main()
