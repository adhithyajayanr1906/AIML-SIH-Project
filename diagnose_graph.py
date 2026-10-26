import pickle
import pyproj
import networkx as nx

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

# Coordinates for Guwahati and Shillong
orig_lon, orig_lat = 91.7362, 26.1445
dest_lon, dest_lat = 91.8933, 25.5788

trans_3857 = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
trans_4326 = pyproj.Transformer.from_crs('EPSG:3857', 'EPSG:4326', always_xy=True)

ox, oy = trans_3857.transform(orig_lon, orig_lat)
dx, dy = trans_3857.transform(dest_lon, dest_lat)

nodes = list(G.nodes)
# Find nearest 5 nodes to origin
orig_sorted = sorted(nodes, key=lambda n: (n[0]-ox)**2 + (n[1]-oy)**2)[:5]
dest_sorted = sorted(nodes, key=lambda n: (n[0]-dx)**2 + (n[1]-dy)**2)[:5]

print("--- Origin Snapping (Guwahati) ---")
for i, n in enumerate(orig_sorted):
    dist_m = ((n[0]-ox)**2 + (n[1]-oy)**2)**0.5
    w_lon, w_lat = trans_4326.transform(n[0], n[1])
    # Find component of this node
    comp_size = len(nx.node_connected_component(G, n))
    print(f"Origin Candidate {i}: dist={dist_m:.1f}m, coords=({w_lat:.5f}, {w_lon:.5f}), comp_size={comp_size}")

print("\n--- Destination Snapping (Shillong) ---")
for i, n in enumerate(dest_sorted):
    dist_m = ((n[0]-dx)**2 + (n[1]-dy)**2)**0.5
    w_lon, w_lat = trans_4326.transform(n[0], n[1])
    comp_size = len(nx.node_connected_component(G, n))
    print(f"Dest Candidate {i}: dist={dist_m:.1f}m, coords=({w_lat:.5f}, {w_lon:.5f}), comp_size={comp_size}")

# Check largest components
comps = sorted(nx.connected_components(G), key=len, reverse=True)
print("\n--- Largest Component Sizes ---")
for i in range(10):
    print(f"Component {i}: {len(comps[i])} nodes")

# Check if any node in comp 0 is near Guwahati or Shillong
c0 = comps[0]
c0_orig_nearest = min(c0, key=lambda n: (n[0]-ox)**2 + (n[1]-oy)**2)
c0_dest_nearest = min(c0, key=lambda n: (n[0]-dx)**2 + (n[1]-dy)**2)
dist_c0_o = ((c0_orig_nearest[0]-ox)**2 + (c0_orig_nearest[1]-oy)**2)**0.5
dist_c0_d = ((c0_dest_nearest[0]-dx)**2 + (c0_dest_nearest[1]-dy)**2)**0.5
w_lon_c0_o, w_lat_c0_o = trans_4326.transform(c0_orig_nearest[0], c0_orig_nearest[1])
w_lon_c0_d, w_lat_c0_d = trans_4326.transform(c0_dest_nearest[0], c0_dest_nearest[1])

print(f"\nNearest in Largest Component (size={len(c0)}):")
print(f"To Guwahati: dist={dist_c0_o/1000:.1f}km, coords=({w_lat_c0_o:.5f}, {w_lon_c0_o:.5f})")
print(f"To Shillong: dist={dist_c0_d/1000:.1f}km, coords=({w_lat_c0_d:.5f}, {w_lon_c0_d:.5f})")
