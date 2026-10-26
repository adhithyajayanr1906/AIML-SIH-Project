"""
tests/test_api_smoke.py
=======================
Integration smoke tests — require the FastAPI server to be running on
http://127.0.0.1:8000

Run with (server must be started first):
    python tests/test_api_smoke.py

These are NOT unit tests and do NOT substitute for the unit tests in
tests/test_routing.py. They verify that the live endpoints respond correctly.
"""

import requests

BASE_URL = "http://127.0.0.1:8000"


def run_tests():
    passed = 0
    failed = 0

    def ok(name):
        nonlocal passed
        passed += 1
        print(f"  PASS  {name}")

    def fail(name, reason):
        nonlocal failed
        failed += 1
        print(f"  FAIL  {name}: {reason}")

    # ------------------------------------------------------------------
    # TEST 1 — Health check
    # ------------------------------------------------------------------
    print("\nTEST 1: Health Check")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}"
        body = r.json()
        assert "status" in body, "Missing 'status' key"
        print("        Response:", body)
        ok("Health endpoint returns 200 with status field")
    except Exception as e:
        fail("Health endpoint", str(e))

    # ------------------------------------------------------------------
    # TEST 2 — Environmental risk endpoint
    # ------------------------------------------------------------------
    print("\nTEST 2: Environmental Risk Endpoint")
    env_risk_score = None
    try:
        r = requests.post(f"{BASE_URL}/predict/environmental-risk", json={
            "rainfall_anomaly": 40.0,
            "extreme_indicator": 0,
            "slope": 15.0,
            "elev": 750.0,
            "ndvi": 0.4,
        }, timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}"
        body = r.json()
        assert "risk_score" in body, "Missing 'risk_score'"
        env_risk_score = body["risk_score"]
        print("        Response:", body)
        ok("Environmental risk returns 200 with risk_score")
    except Exception as e:
        fail("Environmental risk endpoint", str(e))

    # ------------------------------------------------------------------
    # TEST 3 — Logistics risk endpoint
    # ------------------------------------------------------------------
    print("\nTEST 3: Logistics Risk Endpoint")
    try:
        payload = {
            "env_risk_score": env_risk_score if env_risk_score is not None else 0.3,
            "length_m": 5000.0,
            "road_type": "primary",
        }
        r = requests.post(f"{BASE_URL}/predict/logistics-risk", json=payload, timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}"
        body = r.json()
        assert "logistics_risk_score" in body, "Missing 'logistics_risk_score'"
        print("        Response:", body)
        ok("Logistics risk returns 200 with logistics_risk_score")
    except Exception as e:
        fail("Logistics risk endpoint", str(e))

    # ------------------------------------------------------------------
    # TEST 4 — Airway route endpoint (valid coordinates)
    # ------------------------------------------------------------------
    print("\nTEST 4: Airway Route Endpoint — valid coordinates")
    try:
        r = requests.post(f"{BASE_URL}/route/airway", json={
            "origin_lat":  26.1445,
            "origin_lon":  91.7362,
            "dest_lat":    25.5788,
            "dest_lon":    91.8933,
        }, timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        body = r.json()
        assert body.get("transport_mode") == "AIRWAY", f"Expected transport_mode=AIRWAY, got {body.get('transport_mode')}"
        assert body.get("route_type") == "DIRECT_AIR_DISTANCE"
        assert isinstance(body.get("distance_km"), (int, float)), "distance_km must be numeric"
        assert body["distance_km"] > 0, "distance_km must be positive"
        assert "disclaimer" in body, "Disclaimer must be present"
        assert "not a verified flight route" in body["disclaimer"]
        assert body.get("eta_available") is False, "eta_available must be False"
        print(f"        Distance: {body['distance_km']} km")
        ok("Airway endpoint returns correct structure and distance")
    except Exception as e:
        fail("Airway route endpoint", str(e))

    # ------------------------------------------------------------------
    # TEST 5 — Airway route: identical endpoints → HTTP 422
    # ------------------------------------------------------------------
    print("\nTEST 5: Airway Route — identical origin and destination")
    try:
        r = requests.post(f"{BASE_URL}/route/airway", json={
            "origin_lat": 26.1445,
            "origin_lon": 91.7362,
            "dest_lat":   26.1445,
            "dest_lon":   91.7362,
        }, timeout=5)
        assert r.status_code in (400, 422), (
            f"Expected 400 or 422 for identical endpoints, got {r.status_code}"
        )
        print(f"        Server returned {r.status_code} as expected")
        ok("Identical airway endpoints rejected with 400/422")
    except Exception as e:
        fail("Identical airway endpoints", str(e))

    # ------------------------------------------------------------------
    # TEST 6 — /route/recommend with unsupported transport_mode → HTTP 422
    # ------------------------------------------------------------------
    print("\nTEST 6: Roadway /route/recommend — unsupported transport_mode")
    try:
        r = requests.post(f"{BASE_URL}/route/recommend", json={
            "origin_lat":     26.1445,
            "origin_lon":     91.7362,
            "dest_lat":       25.5788,
            "dest_lon":       91.8933,
            "mode":           "SHORTEST",
            "transport_mode": "AIRWAY",    # Must be rejected
        }, timeout=5)
        assert r.status_code == 422, (
            f"Expected 422 for unsupported transport_mode, got {r.status_code}: {r.text}"
        )
        print(f"        Server returned 422 as expected")
        ok("Unsupported transport_mode rejected with HTTP 422")
    except Exception as e:
        fail("Unsupported transport_mode", str(e))

    # ------------------------------------------------------------------
    # TEST 7 — /route/recommend with unsupported mode sub-type → HTTP 422
    # ------------------------------------------------------------------
    print("\nTEST 7: Roadway /route/recommend — unsupported mode sub-type AIRWAY")
    try:
        r = requests.post(f"{BASE_URL}/route/recommend", json={
            "origin_lat": 26.1445,
            "origin_lon": 91.7362,
            "dest_lat":   25.5788,
            "dest_lon":   91.8933,
            "mode":       "AIRWAY",        # Not a valid road sub-mode
        }, timeout=5)
        assert r.status_code == 422, (
            f"Expected 422 for invalid mode, got {r.status_code}: {r.text}"
        )
        print(f"        Server returned 422 as expected")
        ok("Invalid road sub-mode rejected with HTTP 422")
    except Exception as e:
        fail("Invalid road sub-mode", str(e))

    # ------------------------------------------------------------------
    # TEST 8 — /route/recommend SHORTEST route (Guwahati -> Shillong)
    # ------------------------------------------------------------------
    print("\nTEST 8: Roadway /route/recommend — SHORTEST route (Guwahati -> Shillong)")
    try:
        r = requests.post(f"{BASE_URL}/route/recommend", json={
            "origin_lat":     26.1445,
            "origin_lon":     91.7362,
            "dest_lat":       25.5788,
            "dest_lon":       91.8933,
            "mode":           "SHORTEST",
            "transport_mode": "ROADWAY",
        }, timeout=10)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        body = r.json()
        assert body.get("transport_mode") == "ROADWAY"
        assert body.get("route_type") == "SHORTEST"
        assert body.get("distance_km") > 0
        assert len(body.get("coords", [])) > 0
        # Check coordinate format: [[lat, lon], [lat, lon]]
        first_seg = body["coords"][0]
        assert len(first_seg) == 2
        assert 20.0 <= first_seg[0][0] <= 30.0, f"Invalid latitude: {first_seg[0][0]}"
        assert 88.0 <= first_seg[0][1] <= 98.0, f"Invalid longitude: {first_seg[0][1]}"
        print(f"        Distance: {body['distance_km']} km, Segments: {body['segments']}")
        ok("Roadway SHORTEST route calculated successfully")
    except Exception as e:
        fail("Roadway SHORTEST route", str(e))

    # ------------------------------------------------------------------
    # TEST 9 — /route/recommend SAFE route (Guwahati -> Shillong)
    # ------------------------------------------------------------------
    print("\nTEST 9: Roadway /route/recommend — SAFE route (Guwahati -> Shillong)")
    try:
        r = requests.post(f"{BASE_URL}/route/recommend", json={
            "origin_lat":     26.1445,
            "origin_lon":     91.7362,
            "dest_lat":       25.5788,
            "dest_lon":       91.8933,
            "mode":           "SAFE",
            "transport_mode": "ROADWAY",
        }, timeout=10)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        body = r.json()
        assert body.get("transport_mode") == "ROADWAY"
        assert body.get("route_type") == "LOWEST_RISK"
        assert body.get("distance_km") > 0
        assert body.get("total_cost") > 0
        print(f"        Distance: {body['distance_km']} km, Total Cost: {body['total_cost']}")
        ok("Roadway SAFE route calculated successfully")
    except Exception as e:
        fail("Roadway SAFE route", str(e))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed (of {passed+failed} tests)")
    if failed == 0:
        print("ALL API SMOKE TESTS PASSED!")
    else:
        print("SOME TESTS FAILED — see details above.")
    print(f"{'='*50}\n")

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
