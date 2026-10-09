# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
from src.routing.route_optimizer import build_logistics_graph
from database.database import get_blocked_routes

def render_network_page():
    st.markdown("### Regional Road Network Accessibility Telemetry")
    st.caption("State and district corridor status tracking across the North Eastern Region.")

    G, edge_details = build_logistics_graph()
    blocked_routes = get_blocked_routes()

    rows = []
    for route_id, info in edge_details.items():
        rows.append({
            "Highway": info["highway"],
            "From": info["origin"],
            "To": info["destination"],
            "Distance (km)": info["distance_km"],
            "Base Time (min)": info["base_time"],
            "Delay (min)": f"+{info['delay_min']}",
            "Risk Probability": f"{info['risk_prob']*100:.1f}%",
            "Risk Level": info["risk_level"],
            "Status": "BLOCKED" if info["is_blocked"] else info["status"]
        })

    df_network = pd.DataFrame(rows)

    c1, c2 = st.columns(2)
    with c1:
        status_filter = st.multiselect("Filter by Corridor Status", ["OPEN", "MEDIUM_RISK", "HIGH_RISK", "BLOCKED"], default=["OPEN", "MEDIUM_RISK", "HIGH_RISK", "BLOCKED"])
    with c2:
        search_query = st.text_input("Search Highway / Hub Name", value="")

    filtered_df = df_network[df_network["Status"].isin(status_filter)]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["Highway"].str.contains(search_query, case=False) |
            filtered_df["From"].str.contains(search_query, case=False) |
            filtered_df["To"].str.contains(search_query, case=False)
        ]

    st.subheader(f"Monitored Highway Corridors ({len(filtered_df)} of {len(df_network)})")
    st.dataframe(filtered_df, use_container_width=True, height=450)
