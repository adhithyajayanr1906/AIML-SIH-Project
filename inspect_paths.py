import pickle
import math
import networkx as nx

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

# Coordinates for Guwahati and Shillong
orig_lon, orig_lat = 91.7362, 26.1445
dest_lon, dest_lat = 91.8933, 25.5788

import pyproj
trans_3857 = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
trans_4326 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True)

ox, oy = trans_3857.transform(orig_lon, orig_lat)
dx, dy = trans_3857.transform(dest_lon, dest_lat)

# Replicate the snapping logic
major_components = [c for c in nx.connected_components(G) if len(c) >= 100]
best_pair = None
best_cost = float('inf')

for comp in major_components:
    cand_s = min(comp, key=lambda n: (n[0]-ox)**2 + (n[1]-oy)**2)
    cand_d = min(comp, key=lambda n: (n[0]-dx)**2 + (n[1]-dy)**2)
    if cand_s == cand_d: continue
    d_s = math.sqrt((cand_s[0]-ox)**2 + (cand_s[1]-oy)**2)
    d_d = math.sqrt((cand_d[0]-dx)**2 + (cand_d[1]-dy)**2)
    total_snap_d = d_s + d_d
    if total_snap_d < best_cost:
        best_cost = total_snap_d
        best_pair = (cand_s, cand_d)

start_node, end_node = best_pair

# Inspect Dijkstra paths for SHORTEST and SAFE
path_shortest = nx.dijkstra_path(G, start_node, end_node, weight='travel_cost')
path_safe = nx.dijkstra_path(G, start_node, end_node, weight='total_cost')

print(f"Path length shortest: {len(path_shortest)} nodes")
print(f"Path length safe: {len(path_safe)} nodes")
print(f"Are paths identical node-for-node? {path_shortest == path_safe}")

# Calculate total distances and costs for both paths
def eval_path(path):
    dist_km = 0.0
    travel_cost = 0.0
    total_cost = 0.0
    risk_penalties = 0.0
    highways = {}
    edges_with_risk = 0
    for i in range(len(path)-1):
        d = G.get_edge_data(path[i], path[i+1])
        dist_km += d['length_km']
        travel_cost += d['travel_cost']
        total_cost += d['total_cost']
        risk_penalties += d['risk_penalty']
        hw = d.get('road_type', 'unknown')
        highways[hw] = highways.get(hw, 0) + 1
        if d.get('logistics_risk', 0) > 0:
            edges_with_risk += 1
    return dist_km, travel_cost, total_cost, risk_penalties, highways, edges_with_risk

d_short, tc_short, totc_short, rp_short, hw_short, ewr_short = eval_path(path_shortest)
print("\n--- SHORTEST Path Evaluation ---")
print(f"Distance: {d_short:.2f} km")
print(f"Travel Cost: {tc_short:.2f}")
print(f"Total Cost: {totc_short:.2f}")
print(f"Risk Penalty Sum: {rp_short:.2f}")
print(f"Edges with risk > 0: {ewr_short} of {len(path_shortest)-1}")
print(f"Road types: {hw_short}")

# Check if there are alternative paths in the component
# Subgraph induced by component 0
c0_sub = G.subgraph(nx.node_connected_component(G, start_node))
print(f"\nComponent size: {len(c0_sub)} nodes, {c0_sub.number_of_edges()} edges")
# Check edge attribute range
tc_weights = [d['travel_cost'] for u, v, d in c0_sub.edges(data=True)]
tot_weights = [d['total_cost'] for u, v, d in c0_sub.edges(data=True)]
print(f"Travel cost min/max: {min(tc_weights)} / {max(tc_weights)}")
print(f"Total cost min/max: {min(tot_weights)} / {max(tot_weights)}")
