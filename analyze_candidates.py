import pickle
import math

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

# Coordinates for Guwahati and Shillong
orig_lon, orig_lat = 91.7362, 26.1445
dest_lon, dest_lat = 91.8933, 25.5788

import pyproj
trans_3857 = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)
ox, oy = trans_3857.transform(orig_lon, orig_lat)
dx, dy = trans_3857.transform(dest_lon, dest_lat)

# Get top 200 nearest nodes for origin and dest
nodes = list(G.nodes)
o_candidates = sorted(nodes, key=lambda n: (n[0]-ox)**2 + (n[1]-oy)**2)[:200]
d_candidates = sorted(nodes, key=lambda n: (n[0]-dx)**2 + (n[1]-dy)**2)[:200]

# Check components of these candidates
import networkx as nx
o_comps = {}
for i, n in enumerate(o_candidates):
    c = nx.node_connected_component(G, n)
    c_id = id(c) # or frozenset
    size = len(c)
    dist = ((n[0]-ox)**2 + (n[1]-oy)**2)**0.5
    if size not in o_comps:
        o_comps[size] = (i, dist, n)

d_comps = {}
for i, n in enumerate(d_candidates):
    c = nx.node_connected_component(G, n)
    size = len(c)
    dist = ((n[0]-dx)**2 + (n[1]-dy)**2)**0.5
    if size not in d_comps:
        d_comps[size] = (i, dist, n)

print("Origin component sizes found in top 200 candidates:")
for size in sorted(o_comps.keys(), reverse=True):
    rank, dist, _ = o_comps[size]
    print(f"  Size: {size}, rank in candidates: {rank}, dist: {dist:.1f}m")

print("\nDest component sizes found in top 200 candidates:")
for size in sorted(d_comps.keys(), reverse=True):
    rank, dist, _ = d_comps[size]
    print(f"  Size: {size}, rank in candidates: {rank}, dist: {dist:.1f}m")

# Check common component sizes
common_sizes = set(o_comps.keys()) & set(d_comps.keys())
print("\nCommon component sizes in top 200:", common_sizes)
