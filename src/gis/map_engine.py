import folium
from typing import Dict, Any, List, Optional
from config.config import NER_HUBS, NER_ROUTES
from src.routing.route_optimizer import build_logistics_graph
from database.database import get_all_reports, get_blocked_routes

def create_ner_gis_map(
    highlight_path: Optional[List[str]] = None,
    active_blockages: Optional[List[str]] = None
) -> folium.Map:
    """
    Build Folium GIS interactive map displaying North Eastern Region logistics hubs,
    color-coded road risk polylines (Green/Yellow/Red/Black), recommended route overlay,
    and crowdsourced field report pin markers.
    """
    if active_blockages is None:
        active_blockages = get_blocked_routes()

    # Center map on Guwahati / NER central coordinates
    center_lat = 26.1445
    center_lon = 91.7362

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles="cartodbpositron",
        control_scale=True
    )

    G, edge_details = build_logistics_graph(active_blockages=active_blockages)

    # 1. Draw Road Risk Corridors
    for u, v, dist_km, base_time, highway in NER_ROUTES:
        u_coords = NER_HUBS[u]
        v_coords = NER_HUBS[v]
        
        route_id_1 = f"{u} - {v}"
        route_id_2 = f"{v} - {u}"

        edge_info = G[u][v] if G.has_edge(u, v) else {}
        is_blocked = edge_info.get("is_blocked", False) or (route_id_1 in active_blockages or route_id_2 in active_blockages)
        risk_level = edge_info.get("risk_level", "LOW")

        # Color mapping:
        # Green: OPEN / LOW RISK
        # Yellow: MEDIUM RISK
        # Red: HIGH RISK
        # Black: BLOCKED
        if is_blocked:
            color = "#000000" # Black
            weight = 5
            dash_array = "5, 5"
            status_text = "STATUS: BLOCKED (NO ACCESS)"
        elif risk_level == "HIGH":
            color = "#d9534f" # Red
            weight = 4
            dash_array = None
            status_text = "STATUS: HIGH RISK"
        elif risk_level == "MEDIUM":
            color = "#f0ad4e" # Yellow / Amber
            weight = 4
            dash_array = None
            status_text = "STATUS: MEDIUM RISK"
        else:
            color = "#5cb85c" # Green
            weight = 3
            dash_array = None
            status_text = "STATUS: OPEN / LOW RISK"

        popup_content = (
            f"<div style='font-family: Arial, sans-serif; font-size: 12px; min-width: 180px;'>"
            f"<b>Highway:</b> {highway}<br/>"
            f"<b>Corridor:</b> {u} to {v}<br/>"
            f"<b>Distance:</b> {dist_km} km<br/>"
            f"<b>Risk Level:</b> {risk_level}<br/>"
            f"<b>{status_text}</b>"
            f"</div>"
        )

        folium.PolyLine(
            locations=[[u_coords["lat"], u_coords["lon"]], [v_coords["lat"], v_coords["lon"]]],
            color=color,
            weight=weight,
            dash_array=dash_array,
            opacity=0.85,
            tooltip=f"{highway}: {u} - {v} ({risk_level})",
            popup=folium.Popup(popup_content, max_width=300)
        ).add_to(m)

    # 2. Draw Highlighted Path (Recommended Navigation Path in Blue)
    if highlight_path and len(highlight_path) > 1:
        path_coords = [[NER_HUBS[node]["lat"], NER_HUBS[node]["lon"]] for node in highlight_path if node in NER_HUBS]
        folium.PolyLine(
            locations=path_coords,
            color="#0275d8", # Blue
            weight=7,
            opacity=0.9,
            tooltip="Recommended Navigation Path",
            popup="Recommended Path"
        ).add_to(m)

    # 3. Add Logistics Hub Markers
    for name, data in NER_HUBS.items():
        popup_html = (
            f"<div style='font-family: Arial, sans-serif; font-size: 12px;'>"
            f"<b>Hub:</b> {name}<br/>"
            f"<b>State:</b> {data['state']}<br/>"
            f"<b>District:</b> {data['district']}<br/>"
            f"<b>Coordinates:</b> {data['lat']:.4f}, {data['lon']:.4f}"
            f"</div>"
        )

        is_in_path = highlight_path and name in highlight_path

        folium.CircleMarker(
            location=[data["lat"], data["lon"]],
            radius=8 if is_in_path else 6,
            color="#0275d8" if is_in_path else "#333333",
            fill=True,
            fill_color="#5bc0de" if is_in_path else "#ffffff",
            fill_opacity=1.0,
            tooltip=f"Logistics Hub: {name} ({data['state']})",
            popup=folium.Popup(popup_html, max_width=250)
        ).add_to(m)

    # 4. Add Crowdsourced Field Report Markers (Blue Markers)
    field_reports = get_all_reports()
    for report in field_reports:
        if report.get("status") == "Active":
            lat = report["latitude"]
            lon = report["longitude"]
            loc_name = report["location_name"]
            problem = report.get("problem_type") or report.get("incident_type", "Disruption")
            severity = report["severity"]
            desc = report.get("description", "")
            time_str = report.get("timestamp") or report.get("created_at", "")

            popup_rep = (
                f"<div style='font-family: Arial, sans-serif; font-size: 12px; min-width: 200px;'>"
                f"<b>Field Incident Report #{report['id']}</b><br/>"
                f"<b>Location:</b> {loc_name}<br/>"
                f"<b>Incident:</b> {problem}<br/>"
                f"<b>Severity:</b> {severity}<br/>"
                f"<b>Details:</b> {desc}<br/>"
                f"<b>Reported At:</b> {time_str}"
                f"</div>"
            )

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_rep, max_width=280),
                tooltip=f"Report #{report['id']}: {problem} ({severity})",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

    return m
