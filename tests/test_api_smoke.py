import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_frontend_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Smart Logistics" in response.text

def test_environmental_risk_endpoint():
    payload = {
        "rainfall_mm": 180.0,
        "water_level_m": 6.2,
        "river_discharge_m3s": 3200.0,
        "elevation_m": 1200.0,
        "land_cover": "Water Body",
        "soil_type": "Clay"
    }
    response = client.post("/predict/environmental-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert 0.0 <= data["probability"] <= 1.0
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]

def test_logistics_risk_endpoint():
    payload = {
        "environmental_risk": 0.60,
        "road_accessibility_risk": 0.30,
        "field_report_risk": 0.20
    }
    response = client.post("/predict/logistics-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "logistics_risk_score" in data
    assert 0.0 <= data["logistics_risk_score"] <= 1.0

def test_route_recommend_endpoint_valid():
    payload = {
        "origin": "Guwahati",
        "destination": "Shillong",
        "preference": "risk_aware"
    }
    response = client.post("/route/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "shortest_route" in data
    assert "risk_aware_route" in data

def test_road_risk_endpoint():
    response = client.get("/risk/road/NH_6")
    assert response.status_code == 200
    data = response.json()
    assert "road_id" in data
    assert "risk_level" in data
