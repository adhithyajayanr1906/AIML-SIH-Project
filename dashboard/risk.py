import streamlit as st
import pandas as pd
from src.ml.predict import predict_risk
from config.config import NER_HUBS

def render_risk_page():
    st.markdown("### Risk Intelligence & Environmental Flood Risk Prediction")
    st.caption("Predict environmental flood occurrence probability from historical dataset features and calculate decision-support logistics route risk scores.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Environmental & Hydrological Feature Sandbox")

        preset_location = st.selectbox("Select Logistics Corridor Hub Preset", list(NER_HUBS.keys()), index=0)
        coords = NER_HUBS[preset_location]

        lat = st.number_input("Latitude", value=float(coords["lat"]), format="%.4f")
        lon = st.number_input("Longitude", value=float(coords["lon"]), format="%.4f")

        rainfall = st.slider("Rainfall (mm)", min_value=0.0, max_value=500.0, value=185.0, step=5.0)
        water_level = st.slider("Water Level (m)", min_value=0.5, max_value=10.0, value=6.5, step=0.1)
        river_discharge = st.slider("River Discharge (m³/s)", min_value=50.0, max_value=5000.0, value=3200.0, step=50.0)
        elevation = st.slider("Elevation (m)", min_value=10.0, max_value=5000.0, value=1200.0, step=50.0)

        c_a, c_b = st.columns(2)
        with c_a:
            land_cover = st.selectbox("Land Cover", ["Water Body", "Forest", "Agricultural", "Urban", "Desert"], index=0)
            soil_type = st.selectbox("Soil Type", ["Clay", "Peat", "Loam", "Sandy", "Silt"], index=0)
            temp = st.number_input("Temperature (°C)", value=25.0, min_value=5.0, max_value=50.0)
        with c_b:
            humidity = st.number_input("Humidity (%)", value=85.0, min_value=10.0, max_value=100.0)
            pop_density = st.number_input("Population Density", value=4500.0, min_value=50.0, max_value=10000.0)
            hist_floods = st.selectbox("Historical Floods", [0, 1], index=1)
            infra = st.selectbox("Infrastructure Flag", [0, 1], index=1)

        input_sample = {
            "Latitude": lat,
            "Longitude": lon,
            "Rainfall (mm)": rainfall,
            "Temperature (°C)": temp,
            "Humidity (%)": humidity,
            "River Discharge (m³/s)": river_discharge,
            "Water Level (m)": water_level,
            "Elevation (m)": elevation,
            "Land Cover": land_cover,
            "Soil Type": soil_type,
            "Population Density": pop_density,
            "Infrastructure": infra,
            "Historical Floods": hist_floods
        }

        run_predict = st.button("Predict Risk", type="primary", use_container_width=True)

    with col2:
        st.subheader("Model Risk Prediction Output")

        if run_predict or True:
            res = predict_risk(input_sample)

            prob = res["probability"]
            level = res["risk_level"]
            logistics_score = res["logistics_risk_score"]
            delay = res["estimated_delay_minutes"]
            factors = res["key_factors"]
            model_used = res["model_used"]

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Flood Probability", f"{prob*100:.1f}%")
            with m2:
                st.metric("Environmental Risk", level)
            with m3:
                st.metric("Logistics Risk Score", f"{logistics_score:.2f}")

            st.markdown("---")
            st.markdown(f"**Trained Model Executed**: `{model_used}`")
            st.markdown(f"**Estimated Travel Delay Penalty**: `+{delay} minutes`")

            st.markdown("#### Primary Environmental Risk Factors")
            for f in factors:
                st.write(f"- {f}")

            st.info(
                "Academic Disclaimer: Machine learning model predicts environmental flood risk probability "
                "from historical dataset features. Prototype risk thresholds: 0.00-0.34 Low, 0.35-0.69 Medium, 0.70-1.00 High."
            )
