import networkx as nx

def build_risk_graph(gdf_edges):
    """ Builds graph with dual weights for Routing. """
    G = nx.Graph()
    for idx, row in gdf_edges.iterrows():
        coords = list(row.geometry.coords)
        if len(coords) < 2: continue
        
        src = coords[0]
        dst = coords[-1]
        
        # Risk penalty is factored heavily: e.g. a CRITICAL logistics risk (1.0) adds 5x distance penalty
        import math
        raw_log_risk = row.get('logistics_risk')
        is_log_missing = raw_log_risk is None or (isinstance(raw_log_risk, float) and math.isnan(raw_log_risk))
        log_risk = 0.0 if is_log_missing else float(raw_log_risk)

        raw_env_risk = row.get('environmental_risk')
        is_env_missing = raw_env_risk is None or (isinstance(raw_env_risk, float) and math.isnan(raw_env_risk))
        env_risk = 0.0 if is_env_missing else float(raw_env_risk)

        covariates_available = not (is_log_missing or is_env_missing)

        length_m = float(row.get('length_m', 0))
        risk_penalty = length_m * (log_risk * 5.0)
        total_cost = length_m + risk_penalty
        
        G.add_edge(src, dst,
                   road_id=idx,
                   length_km=length_m/1000.0,
                   road_type=row.get('highway', 'unknown'),
                   travel_cost=length_m,
                   environmental_risk=env_risk,
                   logistics_risk=log_risk,
                   risk_category=row.get('logistics_category', 'LOW'),
                   risk_penalty=risk_penalty,
                   total_cost=total_cost,
                   covariates_available=covariates_available,
                   geometry=row.geometry)
    return G

def get_nearest_node(G, point):
    """ Snaps projected (x, y) to nearest explicit node. """
    nodes = list(G.nodes)
    if not nodes: return None
    # Calculate euclidean approx fast
    nearest = min(nodes, key=lambda n: (n[0]-point[0])**2 + (n[1]-point[1])**2)
    return nearest

def get_nearest_nodes(G, point, k=10):
    """ Return up to k nearest nodes sorted by Euclidean distance. """
    nodes = list(G.nodes)
    if not nodes: return []
    sorted_nodes = sorted(nodes, key=lambda n: (n[0]-point[0])**2 + (n[1]-point[1])**2)
    return sorted_nodes[:k]

def shortest_path_dijkstra(G, start, end, weight='travel_cost'):
    """ Returns standard shortest path metrics. """
    path = nx.dijkstra_path(G, start, end, weight=weight)
    
    total_dist = 0
    total_cost = 0
    geom_list = []
    
    for i in range(len(path)-1):
        data = G.get_edge_data(path[i], path[i+1])
        total_dist += data['length_km']
        total_cost += data[weight]
        geom_list.append(((path[i][1], path[i][0]), (path[i+1][1], path[i+1][0])))
        
    return {
        "distance_km": round(total_dist, 2),
        "total_cost": round(total_cost, 2),
        "segments": len(path)-1,
        "eta_available": False,
        "coords": geom_list,
        "path_nodes": path
    }
