import streamlit as st
import pandas as pd
from database.database import add_field_report, get_all_reports
from config.config import NER_HUBS, NER_ROUTES
from src.routing.route_optimizer import find_nearest_road

def render_reports_page():
    st.markdown("### Field Feedback and Geo-Tagged Crowdsourced Reporting Center")
    st.caption("Field users submit live disruption reports. Critical severity incidents instantly mark nearest road segments as BLOCKED and trigger graph rerouting.")

    tab1, tab2 = st.tabs(["Submit Field Report", "Live Field Reports Database"])

    with tab1:
        st.subheader("Submit New Geo-Tagged Disruption Incident")

        col1, col2 = st.columns(2)
        with col1:
            hub_preset = st.selectbox("Select Nearest Location / Corridor Hub", list(NER_HUBS.keys()), index=0)
            preset_coords = NER_HUBS[hub_preset]

            latitude = st.number_input("Latitude", value=float(preset_coords["lat"]), format="%.4f")
            longitude = st.number_input("Longitude", value=float(preset_coords["lon"]), format="%.4f")
            location_name = st.text_input("Specific Location / Landmark", value=f"{hub_preset} Highway Section")

        with col2:
            route_options = [f"{r[0]} - {r[1]}" for r in NER_ROUTES]
            route_id = st.selectbox("Affected Highway Route Corridor", route_options, index=0)

            incident_type = st.selectbox("Incident / Disruption Type", [
                "Road Blocked",
                "Landslide",
                "Flood",
                "Bridge Damaged",
                "Heavy Traffic",
                "Road Damage",
                "Other"
            ], index=0)

            severity = st.selectbox("Severity Level", ["Critical", "High", "Medium", "Low"], index=0)
            reporter_name = st.text_input("Reporter Name / Field Agent ID", value="Field Agent 07")

        description = st.text_area("Detailed Disruption Description and Road Conditions", value="Heavy landslide debris blocking both lanes. Clearance equipment dispatched.")

        if st.button("Submit Incident Report and Trigger Recalculation", type="primary", use_container_width=True):
            # Match nearest road segment
            u, v, matched_route, dist_to_road = find_nearest_road(latitude, longitude)
            
            new_report = add_field_report(
                latitude=latitude,
                longitude=longitude,
                location_name=location_name,
                incident_type=incident_type,
                severity=severity,
                description=description,
                route_id=route_id or matched_route,
                reporter_name=reporter_name
            )

            st.success(f"Report successfully filed! ID #{new_report['id']} for '{location_name}'.")
            st.info(f"Nearest Graph Road Segment Matched: {matched_route} ({dist_to_road:.1f} km away). Status updated to BLOCKED. Graph recalculated.")

    with tab2:
        st.subheader("Active Field Reports Table (SQLite Database)")

        reports = get_all_reports()
        if reports:
            df_rep = pd.DataFrame(reports)
            
            st.dataframe(
                df_rep[["id", "timestamp", "location_name", "route_id", "incident_type", "severity", "reporter_name", "description"]],
                use_container_width=True,
                height=400
            )

            st.markdown("#### Disruption Type Breakdown")
            type_counts = df_rep["incident_type"].value_counts()
            st.bar_chart(type_counts)
        else:
            st.info("No field reports currently recorded in SQLite database.")
