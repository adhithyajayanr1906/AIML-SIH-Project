import os
# pyrefly: ignore [missing-import]
import joblib
import json
import pandas as pd
from typing import Dict, Any, Union

from config.config import MODEL_PATH, PREPROCESSOR_PATH, METADATA_PATH
from src.data.preprocess import DataPreprocessor
from src.risk.risk_engine import (
    categorize_risk,
    calculate_logistics_risk_score,
    calculate_delay_estimate,
    derive_key_factors
)

def predict_risk(input_data: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
    """
    Predict environmental flood risk probability and calculate logistics route risk
    using the trained ML model and decision-support risk engine.
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at '{MODEL_PATH}'. Run model training first.")

    model = joblib.load(MODEL_PATH)
    preprocessor = DataPreprocessor.load_preprocessor(PREPROCESSOR_PATH)

    # Transform raw input
    X_processed = preprocessor.transform_input(input_data)

    # Perform actual model inference
    if hasattr(model, "predict_proba"):
        prob = float(model.predict_proba(X_processed)[0][1])
    else:
        prob = float(model.predict(X_processed)[0])

    prob = round(min(max(prob, 0.0), 1.0), 4)

    # Categorize Risk
    risk_level = categorize_risk(prob)

    # Extract input values for delay and explainability
    if isinstance(input_data, dict):
        sample_dict = input_data
    elif isinstance(input_data, pd.DataFrame):
        sample_dict = input_data.iloc[0].to_dict()
    else:
        sample_dict = {}

    rainfall = float(sample_dict.get("Rainfall (mm)", sample_dict.get("Rainfall", 0.0)))
    water_level = float(sample_dict.get("Water Level (m)", sample_dict.get("Water_Level", 0.0)))
    river_discharge = float(sample_dict.get("River Discharge (m³/s)", sample_dict.get("River_Discharge", 0.0)))

    # Logistics Risk Score calculation
    logistics_score = calculate_logistics_risk_score(
        environmental_flood_risk=prob,
        road_accessibility_risk=0.0,
        field_report_risk=0.0
    )

    delay_min = calculate_delay_estimate(prob, rainfall, water_level, river_discharge)
    key_factors = derive_key_factors(sample_dict, prob)

    model_name = "Trained ML Model"
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r") as f:
                meta = json.load(f)
                model_name = meta.get("selected_model", model_name)
        except Exception:
            pass

    return {
        "probability": prob,
        "risk_probability": prob,
        "risk_level": risk_level,
        "logistics_risk_score": logistics_score,
        "estimated_delay_minutes": delay_min,
        "key_factors": key_factors,
        "model_used": model_name
    }

# Alias for backward compatibility
predict_disruption = predict_risk

if __name__ == "__main__":
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
    result = predict_risk(sample)
    print("Inference Result:", result)
