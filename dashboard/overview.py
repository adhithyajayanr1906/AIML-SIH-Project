# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from streamlit_folium import st_folium
from config.config import NER_ROUTES, NER_HUBS, NER_STATES
from src.routing.route_optimizer import build_logistics_graph
from src.gis.map_engine import create_ner_gis_map
from database.database import get_all_reports, get_blocked_routes

def render_overview_page():
    st.markdown("### Network Overview and Live GIS Accessibility Intelligence")
    st.caption("Real-time logistical monitoring and AI environmental risk assessment across the North Eastern Region of India.")

    # Fetch network data
    G, edge_details = build_logistics_graph()
    field_reports = get_all_reports()
    blocked_routes = get_blocked_routes()

    total_routes = len(edge_details)
    blocked_count = len(blocked_routes)
    high_risk_count = sum(1 for e in edge_details.values() if e["risk_level"] == "HIGH" and not e["is_blocked"])
    accessible_count = total_routes - blocked_count
    active_reports_count = len(field_reports)
    avg_delay = sum(e["delay_min"] for e in edge_details.values()) / max(total_routes, 1)

    # KPI Metric Cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Total Routes", f"{total_routes}", "NER Network")
    with c2:
        st.metric("Accessible", f"{accessible_count}", f"{(accessible_count/total_routes)*100:.0f}%", delta_color="normal")
    with c3:
        st.metric("High Risk", f"{high_risk_count}", "Monitor", delta_color="inverse")
    with c4:
        st.metric("Blocked Roads", f"{blocked_count}", "Disrupted", delta_color="inverse")
    with c5:
        st.metric("Field Reports", f"{active_reports_count}", "Crowd Sourced")
    with c6:
        st.metric("Avg Delay", f"{avg_delay:.0f} min", "Traffic/Weather")

    st.markdown("---")

    col_left, col_right = st.columns([3, 1])

    with col_left:
        st.subheader("Interactive NER GIS Logistics Map")
        folium_map = create_ner_gis_map()
        st_folium(folium_map, width=None, height=520, use_container_width=True)

    with col_right:
        st.subheader("Active Critical Alerts")
        high_risk_routes = [v for v in edge_details.values() if v["risk_level"] in ["HIGH"] or v["is_blocked"]]
        
        if high_risk_routes:
            for r in high_risk_routes:
                status_badge = "BLOCKED" if r["is_blocked"] else "HIGH RISK"
                alert_info = f"Alert: {r['active_alert']}" if r.get('active_alert') else ""
                st.error(f"**{r['highway']}** ({r['origin']} <-> {r['destination']})\n\n"
                         f"Status: `{status_badge}`\n\n"
                         f"Est. Delay: `+{r['delay_min']} mins`\n\n"
                         f"{alert_info}")
        else:
            st.success("All primary NER corridors currently operating under normal risk levels.")

        st.subheader("State Coverage")
        for state in NER_STATES:
            st.caption(f"- **{state}**: Active Monitoring")
