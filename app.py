import streamlit as st

st.set_page_config(
    page_title="NER Smart Logistics Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphism Styling without emojis
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stAppHeader {
        background-color: transparent;
    }
    .css-1r650q1 {
        background-color: rgba(22, 27, 34, 0.7) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
    }
    .header-banner {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    .header-title {
        color: #60a5fa;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #9ca3af;
        font-size: 14px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Main Banner
st.markdown("""
<div class="header-banner">
    <div class="header-title">NER Logistics Intelligence Platform</div>
    <div class="header-subtitle">AI-Powered Environmental Risk & Disruption Accessibility Intelligence for the North Eastern Region of India</div>
</div>
""", unsafe_allow_html=True)

# Lazy import dashboard pages
from dashboard.overview import render_overview_page
from dashboard.risk import render_risk_page
from dashboard.routing import render_routing_page
from dashboard.reports import render_reports_page
from dashboard.network import render_network_page
from dashboard.insights import render_insights_page
from dashboard.about import render_about_page

# 7 Dashboard Tabs (No Emojis)
tab_overview, tab_risk, tab_routing, tab_reports, tab_network, tab_insights, tab_about = st.tabs([
    "Overview and GIS Map",
    "Risk Intelligence",
    "Route Planner",
    "Field Reports",
    "Network Monitor",
    "Model Insights",
    "About and Viva"
])

with tab_overview:
    render_overview_page()

with tab_risk:
    render_risk_page()

with tab_routing:
    render_routing_page()

with tab_reports:
    render_reports_page()

with tab_network:
    render_network_page()

with tab_insights:
    render_insights_page()

with tab_about:
    render_about_page()
