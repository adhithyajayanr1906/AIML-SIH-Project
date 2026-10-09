import os

PROJECT_TITLE = "Smart Logistics and Accessibility Intelligence Platform"
PROJECT_DESCRIPTION = "GIS-Based Environmental Risk Assessment and Risk-Aware Route Optimization for Northeast India"
VERSION = "2.0.0"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DATASET_PATH = os.path.join(BASE_DIR, "flood_risk_dataset_india.csv")
