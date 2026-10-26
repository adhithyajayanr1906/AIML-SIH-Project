import sys
import os
import networkx as nx

sys.path.append(os.path.abspath('c:/NER-Smart-Logistics/ml/geospatial'))
from osm_importer import OSMImporter
from road_network import build_graph

def main():
    osm_path = 'c:/NER-Smart-Logistics/data/geospatial/raw/north-eastern-zone-latest.osm.pbf'
    importer = OSMImporter(osm_path)
    
    file_size = os.path.getsize(osm_path) / (1024*1024)
    print(f"FILE_SIZE: {file_size:.2f} MB")
    
    gdf_raw = importer.load_data()
    total_features = len(gdf_raw)
    print(f"TOTAL_FEATURES: {total_features}")
    
    gdf_roads = importer.extract_features(gdf_raw)
    gdf_ner = importer.filter_to_ner(gdf_roads)
    gdf_proj = importer.inspect_and_project_crs(gdf_ner)
    
    print(f"NER_FEATURES: {len(gdf_proj)}")
    print(f"ROAD_TYPES: {', '.join(gdf_proj['highway'].dropna().unique())}")
    
    output_gpkg = 'c:/NER-Smart-Logistics/data/geospatial/processed/ner_roads.gpkg'
    # Drop complex object types before saving if any
    try:
        if 'geometry' in gdf_proj.columns:
            gdf_proj.to_file(output_gpkg, driver='GPKG', engine='pyogrio')
    except Exception as e:
        print("Warning: GPKG writing failed", e)
        
    G = build_graph(gdf_proj)
    nodes = G.number_of_nodes()
    edges = G.number_of_edges()
    ccs = nx.number_connected_components(G)
    
    print(f"NODES: {nodes}")
    print(f"EDGES: {edges}")
    print(f"CONNECTED_COMPONENTS: {ccs}")
    
    # Check invalid geometries visually (zero length edges)
    invalid_edges = sum(1 for u, v, d in G.edges(data=True) if d.get('length_m', 0) == 0)
    print(f"INVALID: {invalid_edges}")

    # Write documentation
    with open('c:/NER-Smart-Logistics/docs/ROAD_GRAPH_VALIDATION.md', 'w') as f:
        f.write("# Road Graph Validation\\n")
        f.write(f"- Nodes: {nodes}\\n")
        f.write(f"- Edges: {edges}\\n")
        f.write(f"- Connected Components: {ccs}\\n")
        f.write(f"- Zero Length Edges: {invalid_edges}\\n")

    with open('c:/NER-Smart-Logistics/docs/NER_ROAD_NETWORK_ANALYSIS.md', 'w') as f:
        f.write("# NER Road Network Analysis\\n")
        f.write(f"- Total extract lines: {total_features}\\n")
        f.write(f"- Road segments: {len(gdf_proj)}\\n")
        f.write(f"- PBF Size: {file_size:.2f} MB\\n")
        
if __name__ == '__main__':
    main()
