import pickle
import networkx as nx

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

comps = sorted(nx.connected_components(G), key=len, reverse=True)
c0 = comps[0]
sub_c0 = G.subgraph(c0)

print(f"Component 0: {sub_c0.number_of_nodes()} nodes, {sub_c0.number_of_edges()} edges")
# Find cyclomatic complexity / number of cycles
# In a connected graph, independent cycles = E - V + 1
cycles = sub_c0.number_of_edges() - sub_c0.number_of_nodes() + 1
print(f"Independent cycles in Component 0: {cycles}")

# Test multiple origin-destination pairs within Component 0 to see if any differ
nodes_list = list(c0)
diff_count = 0
tested = 0

import random
random.seed(42)
sample_nodes = random.sample(nodes_list, min(100, len(nodes_list)))

for i in range(len(sample_nodes)):
    for j in range(i+1, min(i+10, len(sample_nodes))):
        s = sample_nodes[i]
        t = sample_nodes[j]
        tested += 1
        p1 = nx.dijkstra_path(sub_c0, s, t, weight='travel_cost')
        p2 = nx.dijkstra_path(sub_c0, s, t, weight='total_cost')
        if p1 != p2:
            diff_count += 1
            l1 = sum(sub_c0[p1[k]][p1[k+1]]['length_km'] for k in range(len(p1)-1))
            l2 = sum(sub_c0[p2[k]][p2[k+1]]['length_km'] for k in range(len(p2)-1))
            c1 = sum(sub_c0[p1[k]][p1[k+1]]['total_cost'] for k in range(len(p1)-1))
            c2 = sum(sub_c0[p2[k]][p2[k+1]]['total_cost'] for k in range(len(p2)-1))
            print(f"Found diverging route! Tested #{tested}")
            print(f"  SHORTEST: dist={l1:.2f}km, cost={c1:.2f}, segs={len(p1)-1}")
            print(f"  SAFE:     dist={l2:.2f}km, cost={c2:.2f}, segs={len(p2)-1}")
            break
    if diff_count > 0:
        break

print(f"Tested {tested} node pairs in Component 0. Divergent paths found: {diff_count}")
