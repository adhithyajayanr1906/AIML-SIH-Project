# pyrefly: ignore [missing-import]
import streamlit as st

def render_about_page():
    st.markdown("### System Architecture, Methodology, and Viva Guide")
    st.caption("Technical documentation for the AI-Based Smart Logistics and Accessibility Intelligence Platform for the North Eastern Region (NER).")

    st.markdown("#### 1. Academic Problem Statement")
    st.write(
        "The North Eastern Region (NER) of India comprising Assam, Meghalaya, Arunachal Pradesh, Manipur, Nagaland, Mizoram, Tripura, and Sikkim "
        "faces severe logistical vulnerabilities during annual monsoons. High-altitude mountain passes, intense precipitation, and river surge "
        "frequently trigger landslides and flash floods. Because regional transportation relies on key single-corridor highways, road blockages "
        "can isolate entire districts. This platform provides predictive risk scoring, GIS visualization, graph-based alternate routing, and crowdsourced feedback loops."
    )

    st.markdown("---")

    st.markdown("#### 2. Machine Learning Honesty and Methodology Statement")
    st.info(
        "Academic Clarity Statement: The machine learning model predicts environmental flood risk probability from historical dataset features "
        "(flood_risk_dataset_india.csv). The logistics disruption score combines this environmental prediction with road accessibility and "
        "field report severities to support route decision-making. Machine learning does NOT claim to predict direct future physical road blockages."
    )

    st.markdown("""
    **Multi-Layer Risk Architecture:**

    ```text
    Environmental Dataset (10,000 records)
                |
                v
    ML Flood Risk Model (Random Forest / XGBoost / Logistic Regression)
                |
                v
    Environmental Flood Risk Probability (0.00 - 1.00)
                |
                +-----------------------+-----------------------+
                |                       |                       |
                v                       v                       v
    Logistics Risk Engine     Road Accessibility Status    Field Reports (SQLite)
                |                       |                       |
                +-----------------------+-----------------------+
                                        |
                                        v
                            Logistics Route Risk Score
                                        |
                                        v
                    NetworkX Dijkstra Routing (Fastest / Safest / Balanced)
    ```

    **Logistics Risk Score Formula:**
    `Logistics Risk Score = (0.60 * Environmental Flood Risk) + (0.25 * Road Accessibility Risk) + (0.15 * Field Report Risk)`
    """)

    st.markdown("---")

    st.markdown("#### 3. Prototype Demonstration Network Disclaimer")
    st.write(
        "The road network graph is configured as a Prototype Demonstration Network connecting 14 primary logistics hubs "
        "across 16 strategic highway corridors in the NER. It demonstrates Dijkstra graph optimization and dynamic edge weight updates."
    )

    st.markdown("---")

    st.markdown("#### 4. Viva Presentation Walkthrough Guide")
    st.markdown("""
    1. **Overview and GIS Map**: Show the interactive Folium map with color-coded risk corridors (Green = Open, Yellow = Medium Risk, Red = High Risk, Black = Blocked).
    2. **Model Insights**: Present model performance metrics comparing Logistic Regression, Random Forest, and XGBoost. Show confusion matrix and feature importances loaded from `model_metadata.json`.
    3. **Risk Intelligence**: Adjust rainfall, river discharge, and water level sliders to demonstrate live ML probability inference.
    4. **Route Planner**: Calculate route from Guwahati to Shillong under Balanced preference.
    5. **Field Report Rerouting Loop**: Submit a Critical Road Blocked report. Explain how `find_nearest_road` matches the coordinate, sets the road to BLOCKED, and recalculates an alternate route in the Route Planner.
    """)
