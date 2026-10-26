import pickle
import math

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

print(f"Total edges: {G.number_of_edges()}")

bad_travel_cost = 0
bad_total_cost = 0
negative_weights = 0
inf_weights = 0
nan_weights = 0

for u, v, d in G.edges(data=True):
    tc = d.get('travel_cost')
    totc = d.get('total_cost')
    
    for val in (tc, totc):
        if val is None or math.isnan(val):
            nan_weights += 1
        elif math.isinf(val):
            inf_weights += 1
        elif val < 0:
            negative_weights += 1

print(f"NaN weights: {nan_weights}")
print(f"Inf weights: {inf_weights}")
print(f"Negative weights: {negative_weights}")
