import sys
import os
from fastapi.testclient import TestClient
from backend.app.main import app

def run_all_validations():
    print("=== STARTING FULL VALIDATION SUITE ===")
    client = TestClient(app)
    failures = 0

    # Test 1: Health Check
    try:
        res = client.get("/health")
        if res.status_code == 200 and res.json().get("status") == "healthy":
            print("[PASS] GET /health check succeeded.")
        else:
            print("[FAIL] GET /health check failed.")
            failures += 1
    except Exception as e:
        print(f"[FAIL] GET /health exception: {e}")
        failures += 1

    # Test 2: Root Dashboard HTML
    try:
        res = client.get("/")
        if res.status_code == 200 and "<html" in res.text.lower():
            print("[PASS] GET / dashboard HTML served successfully.")
        else:
            print("[FAIL] GET / dashboard HTML serving failed.")
            failures += 1
    except Exception as e:
        print(f"[FAIL] GET / exception: {e}")
        failures += 1

    # Test 3: Environmental Risk Prediction API
    try:
        res = client.post("/predict/environmental-risk", json={
            "rainfall_mm": 180.0,
            "water_level_m": 6.2,
            "river_discharge_m3s": 3200.0,
            "elevation_m": 1200.0,
            "land_cover": "Water Body",
            "soil_type": "Clay"
        })
        if res.status_code == 200 and "probability" in res.json():
            print(f"[PASS] POST /predict/environmental-risk succeeded. Probability: {res.json()['probability']}")
        else:
            print("[FAIL] POST /predict/environmental-risk failed.")
            failures += 1
    except Exception as e:
        print(f"[FAIL] Environmental risk API exception: {e}")
        failures += 1

    # Test 4: Logistics Risk API
    try:
        res = client.post("/predict/logistics-risk", json={
            "environmental_risk": 0.60,
            "road_accessibility_risk": 0.30,
            "field_report_risk": 0.20
        })
        if res.status_code == 200 and "logistics_risk_score" in res.json():
            print(f"[PASS] POST /predict/logistics-risk succeeded. Score: {res.json()['logistics_risk_score']}")
        else:
            print("[FAIL] POST /predict/logistics-risk failed.")
            failures += 1
    except Exception as e:
        print(f"[FAIL] Logistics risk API exception: {e}")
        failures += 1

    # Test 5: Route Recommendation API
    try:
        res = client.post("/route/recommend", json={
            "origin": "Guwahati",
            "destination": "Shillong",
            "preference": "risk_aware"
        })
        if res.status_code == 200 and res.json().get("status") == "success":
            print(f"[PASS] POST /route/recommend succeeded. Shortest: {res.json()['shortest_route']['distance_km']} km, Risk-Aware: {res.json()['risk_aware_route']['distance_km']} km")
        else:
            print("[FAIL] POST /route/recommend failed.")
            failures += 1
    except Exception as e:
        print(f"[FAIL] Route recommend API exception: {e}")
        failures += 1

    # Test 6: Road Risk API
    try:
        res = client.get("/risk/road/NH_6")
        if res.status_code == 200 and "road_id" in res.json():
            print(f"[PASS] GET /risk/road/NH_6 succeeded. Highway: {res.json()['highway']}")
        else:
            print("[FAIL] GET /risk/road/NH_6 failed.")
            failures += 1
    except Exception as e:
        print(f"[FAIL] Road risk API exception: {e}")
        failures += 1

    print("=======================================")
    if failures == 0:
        print("ALL VALIDATION CHECKS PASSED (0 failures).")
        sys.exit(0)
    else:
        print(f"VALIDATION FAILED ({failures} failures).")
        sys.exit(1)

if __name__ == "__main__":
    run_all_validations()
