# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
from streamlit_folium import st_folium
from config.config import NER_HUBS
from src.routing.route_optimizer import find_optimal_route
from src.gis.map_engine import create_ner_gis_map
from database.database import get_blocked_routes

def render_routing_page():
    st.markdown("### Intelligent Graph Route Optimization & Rerouting")
    st.caption("NetworkX graph-based shortest and safest path optimization with dynamic blockage avoidance.")

    hubs_list = list(NER_HUBS.keys())

    col_in1, col_in2, col_in3 = st.columns(3)
    with col_in1:
        origin = st.selectbox("Origin Logistics Hub", hubs_list, index=0)
    with col_in2:
        destination = st.selectbox("Destination Hub", hubs_list, index=1 if len(hubs_list) > 1 else 0)
    with col_in3:
        preference = st.selectbox("Routing Optimization Preference", ["Balanced", "Fastest", "Safest"], index=0)

    if origin == destination:
        st.warning("Origin and Destination hubs must be different for route optimization.")
        return

    # Calculate optimal route
    blocked_routes = get_blocked_routes()
    route_res = find_optimal_route(origin, destination, preference=preference, active_blockages=blocked_routes)

    if "error" in route_res:
        st.error(f"Routing Error: {route_res['error']}")
        return

    path = route_res["path"]
    dist_km = route_res["total_distance_km"]
    time_min = route_res["total_time_min"]
    overall_risk = route_res["overall_risk_level"]
    risky_segs = route_res["risky_segments"]
    blocked_segs = route_res["blocked_segments"]
    is_rerouted = route_res["is_rerouted"]
    alternate_path = route_res["alternate_path"]

    # Metrics Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Distance", f"{dist_km} km")
    with m2:
        st.metric("Est. Travel Time", f"{time_min // 60}h {time_min % 60}m")
    with m3:
        st.metric("Corridor Risk Level", overall_risk)
    with m4:
        st.metric("Risky Segments", f"{len(risky_segs)}")
    with m5:
        st.metric("Road Blockages", f"{len(blocked_segs)}", delta_color="inverse")

    if is_rerouted or blocked_segs:
        st.warning("Dynamic Reroute Active: Primary road segment is BLOCKED. Rerouted via alternate corridor.")

    st.markdown("---")

    col_map, col_details = st.columns([3, 1])

    with col_map:
        st.subheader("Optimized Navigation Map Path")
        route_map = create_ner_gis_map(highlight_path=path, active_blockages=blocked_routes)
        st_folium(route_map, width=None, height=480, use_container_width=True)

    with col_details:
        st.subheader("Itinerary Path Sequence")
        st.markdown(f"**Preference**: `{preference}`")
        st.markdown(f"**Hops**: `{len(path) - 1}`")

        st.markdown("**Route Hub Sequence:**")
        for idx, node in enumerate(path):
            st.write(f"{idx + 1}. **{node}** ({NER_HUBS[node]['state']})")

        if alternate_path:
            st.markdown("---")
            st.subheader("Alternate Route Available")
            st.info(f"Alternate Sequence: {' -> '.join(alternate_path)}")
