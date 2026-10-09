import os
import pytest
from src.ml.predict import predict_risk
from src.risk.risk_engine import categorize_risk, calculate_logistics_risk_score
from config.config import MODEL_PATH, METADATA_PATH

def test_saved_model_exists():
    assert os.path.exists(MODEL_PATH)
    assert os.path.exists(METADATA_PATH)

def test_predict_risk_valid_output():
    sample = {
        "Latitude": 26.1445,
        "Longitude": 91.7362,
        "Rainfall (mm)": 210.0,
        "Temperature (°C)": 26.0,
        "Humidity (%)": 85.0,
        "River Discharge (m³/s)": 3800.0,
        "Water Level (m)": 7.2,
        "Elevation (m)": 1200.0,
        "Land Cover": "Water Body",
        "Soil Type": "Clay",
        "Population Density": 5000.0,
        "Infrastructure": 1,
        "Historical Floods": 1
    }
    res = predict_risk(sample)
    assert "probability" in res
    assert 0.0 <= res["probability"] <= 1.0
    assert res["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert res["estimated_delay_minutes"] >= 0
    assert isinstance(res["key_factors"], list)

def test_risk_threshold_categorization():
    assert categorize_risk(0.10) == "LOW"
    assert categorize_risk(0.50) == "MEDIUM"
    assert categorize_risk(0.85) == "HIGH"

def test_logistics_risk_score_calculation():
    score = calculate_logistics_risk_score(0.80, 0.50, 1.00)
    assert 0.0 <= score <= 1.0
