import pickle
import pyproj
import networkx as nx
from ml.routing.risk_aware_router import shortest_path_dijkstra

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

comps = sorted(nx.connected_components(G), key=len, reverse=True)
c0 = comps[0]

ox, oy = 91.7362, 26.1445
dx, dy = 91.8933, 25.5788

trans_3857 = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
trans_4326 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True)

o_3857 = trans_3857.transform(ox, oy)
d_3857 = trans_3857.transform(dx, dy)

start_c0 = min(c0, key=lambda n: (n[0]-o_3857[0])**2 + (n[1]-o_3857[1])**2)
end_c0 = min(c0, key=lambda n: (n[0]-d_3857[0])**2 + (n[1]-d_3857[1])**2)

print("Start in c0:", trans_4326.transform(start_c0[0], start_c0[1]))
print("End in c0:", trans_4326.transform(end_c0[0], end_c0[1]))
print("Has path in c0:", nx.has_path(G, start_c0, end_c0))

route = shortest_path_dijkstra(G, start_c0, end_c0, weight='travel_cost')
print(f"SHORTEST: distance_km={route['distance_km']}, total_cost={route['total_cost']}, segments={route['segments']}")

route_safe = shortest_path_dijkstra(G, start_c0, end_c0, weight='total_cost')
print(f"SAFE: distance_km={route_safe['distance_km']}, total_cost={route_safe['total_cost']}, segments={route_safe['segments']}")
