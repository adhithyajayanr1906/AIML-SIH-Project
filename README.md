# AI-Based Smart Logistics and Accessibility Intelligence Platform for the North Eastern Region (NER)

A full-stack, functional AI/ML prototype designed to predict environmental flood risk, calculate decision-support logistics route risk scores, map regional accessibility on interactive GIS maps, and integrate crowdsourced field reports into dynamic graph-based rerouting across the North Eastern Region (NER) of India.

---

## 1. Problem Statement

The North Eastern Region (NER) of India comprising Assam, Meghalaya, Arunachal Pradesh, Manipur, Nagaland, Mizoram, Tripura, and Sikkim faces severe logistical vulnerabilities due to:
- High-altitude, mountainous topography with landslide-prone mountain passes.
- Heavy monsoon precipitation leading to flash floods and river surges (Brahmaputra and Barak basins).
- Limited road redundancy where single route blockages can isolate entire districts.

This platform bridges the gap between historical environmental dataset analytics and real-time field logistics by providing predictive risk scoring, interactive GIS visualization, graph-optimized alternate routing, and crowdsourced disruption feedback loops.

---

## 2. Machine Learning Honesty and Methodology Statement

Academic Clarity Statement: The machine learning model predicts environmental flood risk probability from historical dataset features (`flood_risk_dataset_india.csv`). The logistics disruption score combines this environmental prediction with road accessibility and field report severities to support route decision-making. Machine learning does NOT claim to predict direct future physical road blockages.

### Multi-Layer Architecture

```text
Environmental Dataset (flood_risk_dataset_india.csv)
            |
            v
Data Preprocessing Pipeline (ColumnTransformer)
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

---

## 3. Key Capabilities and Features

1. **Automated Dataset Inspection and Machine Learning**:
   - Evaluates Logistic Regression (Baseline) against Random Forest and XGBoost Classifiers.
   - Evaluates Accuracy, Precision, Recall, F1-Score, Confusion Matrix, and ROC-AUC.
   - Dynamically selects model with highest F1-Score and exports artifacts (`models/risk_model.pkl`, `models/preprocessor.pkl`, `models/model_metadata.json`).

2. **Explainable Risk Intelligence**:
   - Categorizes environmental risk using prototype risk thresholds (Low < 0.35, Medium 0.35-0.69, High >= 0.70).
   - Identifies primary environmental risk factors (Heavy Rainfall, Critical Water Level, Poor Drainage Soil, High Elevation).

3. **Graph-Based Intelligent Route Optimization**:
   - Prototype Demonstration Network connecting 14 NER hubs across 16 primary highway corridors using NetworkX.
   - Dynamic cost functions for Fastest, Safest, and Balanced routing preferences.
   - Nearest Road Matching (`find_nearest_road(lat, lon)`) linking GPS coordinates to graph segments.

4. **Crowdsourced Field Feedback Loop (SQLite DB)**:
   - Field agents submit geo-tagged incident reports (Landslides, Floods, Road Blocked, Bridge Damaged).
   - High/Critical severity reports dynamically update the nearest graph road segment to BLOCKED and trigger instant route recalculation in the Route Planner.

5. **Interactive Streamlit GIS Dashboard**:
   - Custom glassmorphism layout without emojis.
   - 7 Core Tabs: Overview and GIS Map, Risk Intelligence, Route Planner, Field Reports, Network Monitor, Model Insights, About and Viva.

---

## 4. Project Directory Structure

```text
NER-Logistics-AI/
├── app.py                         # Main Streamlit Dashboard Application
├── requirements.txt               # Project Dependencies
├── README.md                      # Comprehensive Project Documentation
├── .env.example                   # Environment Configuration Example
├── .gitignore                     # Git Exclusion Rules
├── flood_risk_dataset_india.csv   # Primary Dataset
├── config/
│   └── config.py                  # Configuration, Constants, & Hub Coordinates
├── models/
│   ├── risk_model.pkl             # Trained Best ML Model
│   ├── preprocessor.pkl           # Sklearn Preprocessor Pipeline State
│   └── model_metadata.json        # Empirical Evaluation Metrics & Features
├── src/
│   ├── data/
│   │   ├── load_dataset.py        # Recursive Dataset Loader & Inspector
│   │   └── preprocess.py          # Sklearn Preprocessing Pipeline
│   ├── ml/
│   │   ├── train_model.py         # ML Model Training & Comparison Pipeline
│   │   ├── predict.py             # Inference API & Explainability Engine
│   │   └── evaluate.py            # Evaluation Metrics Calculator
│   ├── risk/
│   │   └── risk_engine.py         # Risk Categorization & Logistics Formula
│   ├── routing/
│   │   └── route_optimizer.py     # NetworkX Graph Routing & Nearest Road Matching
│   ├── gis/
│   │   └── map_engine.py          # Folium Interactive GIS Map Builder
│   └── services/
│       └── weather_service.py     # Weather Abstraction Service
├── database/
│   ├── database.py                # SQLite Database Manager & Queries
│   ├── models.py                  # SQLAlchemy Database Schema
│   └── field_reports_v2.db        # SQLite Database File
├── dashboard/                     # Streamlit Tab Modules
│   ├── overview.py
│   ├── risk.py
│   ├── routing.py
│   ├── reports.py
│   ├── network.py
│   ├── insights.py
│   └── about.py
├── notebooks/
│   └── NER_Logistics_Training.ipynb # Standalone Google Colab Training Notebook
└── tests/                         # Automated Pytest Suite
    ├── test_data.py
    ├── test_model.py
    ├── test_routing.py
    └── test_reports.py
```

---

## 5. Installation and Setup Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Train Machine Learning Models
```bash
python -m src.ml.train_model
```

### Step 3: Run Automated Test Suite
```bash
python -m pytest
```

### Step 4: Launch Streamlit Interactive Dashboard
```bash
streamlit run app.py
```
Open browser at `http://localhost:8501`.

---

## 6. Demonstration Scenario Walkthrough

1. **Overview and GIS Map**: Inspect the interactive Folium map showing color-coded road risk corridors (Green = Open, Yellow = Medium Risk, Red = High Risk, Black = Blocked).
2. **Model Insights**: Present empirical metrics comparing Logistic Regression, Random Forest, and XGBoost. Show confusion matrix and feature importances loaded from `model_metadata.json`.
3. **Risk Intelligence**: Adjust rainfall, river discharge, and water level sliders to demonstrate live ML probability inference.
4. **Route Planner**: Calculate route from Guwahati to Shillong under Balanced preference.
5. **Field Report Rerouting Loop**: Submit a Critical Road Blocked report. Explain how `find_nearest_road` matches the coordinate, sets the road to BLOCKED, and recalculates an alternate route in the Route Planner.

---

## 7. Known Limitations

- Dataset Limitation: The ML model predicts environmental flood occurrence probability from historical climate data. Physical road blockages are incorporated via field feedback reports and logistics risk calculations.
- Road Network: The graph is configured as a Prototype Demonstration Network connecting 14 key hubs.
