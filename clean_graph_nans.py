import pickle
import math

with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'rb') as f:
    G = pickle.load(f)

fixed_edges = 0
for u, v, d in G.edges(data=True):
    lr = d.get('logistics_risk')
    if lr is None or (isinstance(lr, float) and math.isnan(lr)):
        d['logistics_risk'] = 0.0
    
    er = d.get('environmental_risk')
    if er is None or (isinstance(er, float) and math.isnan(er)):
        d['environmental_risk'] = 0.0

    length_m = d.get('travel_cost', 0.0)
    if length_m is None or (isinstance(length_m, float) and math.isnan(length_m)):
        length_m = 0.0
    d['travel_cost'] = float(length_m)

    rp = d.get('risk_penalty')
    if rp is None or (isinstance(rp, float) and math.isnan(rp)):
        rp = float(length_m) * (float(d['logistics_risk']) * 5.0)
        d['risk_penalty'] = rp

    tc = d.get('total_cost')
    if tc is None or (isinstance(tc, float) and math.isnan(tc)):
        d['total_cost'] = float(length_m) + float(d['risk_penalty'])
        fixed_edges += 1

print(f"Fixed {fixed_edges} edges in ner_graph.pkl")
with open('c:/NER-Smart-Logistics/data/geospatial/processed/ner_graph.pkl', 'wb') as f:
    pickle.dump(G, f)
print("Saved cleaned ner_graph.pkl successfully!")
