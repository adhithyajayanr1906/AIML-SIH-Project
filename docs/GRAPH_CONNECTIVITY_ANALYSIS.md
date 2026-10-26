# Graph Connectivity Analysis

## 1. Overview
The current mathematically un-smoothed road network graph contains:
- Nodes: ~528,225
- Edges: ~264,819
- Connected Components: ~264,000+

## 2. Root Cause of Graph Fragmentation
The extreme degree of fragmentation occurs primarily because the raw OpenStreetMap (`osm.pbf`) outputs independent line geometries (`LineStrings`) for every road segment.
**Core Factors:**
1. **Unsnapped OSM LineString Endpoints:** Segments that appear visually connected in GIS tools are mathematically independent nodes if their coordinate strings differ by even 1 micrometer.
2. **Disconnected Service Roads & Topologies:** Roads without connecting intersection nodes. 
3. **Bridges / Tunnels:** Layered intersections that falsely appear disconnected if z-indices are not flattened cleanly.
4. **Legitimate Isolated Roads:** Physical rural gaps isolated by mountainous terrain.

## 3. Impact on Routing
Algorithms like Dijkstra and A* fail (return `NetworkXNoPath`) if the Origin coordinates snap to a disconnected island cluster rather than the mainland continuous graph.

## 4. Remediation (Optional Topology Snapping)
To cleanly bind disjoint networks, a topological union algorithm (such as `osmnx.consolidate_intersections` or `shapely.ops.linemerge`) must be executed. Since modifying genuine OSM geometry without validation exceeds standard indexing scope, it is documented here as an **Optional Preprocessing Enhancement** for future implementation.
