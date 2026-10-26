import sys
import os

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/geospatial'))
# pyrefly: ignore [missing-import]
from road_risk import build_road_risk

print("--- STEP 1: Building Road Risk Integration ---")
try:
    build_road_risk()
except Exception as e:
    print("FAILED Road Risk Integration:", e)

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/backend/app'))
# pyrefly: ignore [missing-import]
import main

print("--- STEP 2: Loading Graph into API ---")
try:
    main.load_graph()
    nodes = main.G_ROAD.number_of_nodes()
    edges = main.G_ROAD.number_of_edges()
    print(f"Graph Loaded: {nodes} nodes, {edges} edges.")
except Exception as e:
    print("FAILED Graph Load:", e)

print("--- STEP 3: Hitting API Routing Endpoints ---")
try:
    # We pick two coordinate pairs inside NER (e.g. Guwahati area)
    # Guwahati 26.1445, 91.7362 to Shillong 25.5788, 91.8933
    # pyrefly: ignore [missing-import]
    from main import RouteRequest, recommend_route
    req = RouteRequest(origin_lat=26.1445, origin_lon=91.7362, dest_lat=25.5788, dest_lon=91.8933, mode="SHORTEST")
    res1 = recommend_route(req)
    print("SHORTEST ROUTE Response:", res1['distance_km'], "km,", res1['segments'], "segments")
    
    req.mode = "SAFE"
    res2 = recommend_route(req)
    print("SAFE ROUTE Response:", res2['distance_km'], "km,", res2['segments'], "segments")
except Exception as e:
    print("FAILED API Integration:", e)

print("--- VALIDATION COMPLETE ---")
