import pickle
import math

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

nan_log_risk = 0
nan_env_risk = 0
nan_total_cost = 0

sample_bad_edges = []
for u, v, d in G.edges(data=True):
    lr = d.get('logistics_risk')
    tc = d.get('total_cost')
    if lr is None or (isinstance(lr, float) and math.isnan(lr)):
        nan_log_risk += 1
        if len(sample_bad_edges) < 3:
            sample_bad_edges.append(d)
    if tc is None or (isinstance(tc, float) and math.isnan(tc)):
        nan_total_cost += 1

print(f"Total edges: {G.number_of_edges()}")
print(f"NaN logistics_risk: {nan_log_risk}")
print(f"NaN total_cost: {nan_total_cost}")
if sample_bad_edges:
    print("Sample edge with NaN:", sample_bad_edges[0])
