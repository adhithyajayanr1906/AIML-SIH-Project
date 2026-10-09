from typing import Dict, Any
from ml.routing.risk_aware_router import compute_routes, find_node_by_name_or_coords

class RoutingService:
    @staticmethod
    def recommend_route(origin: Any, destination: Any, preference: str = "risk_aware") -> Dict[str, Any]:
        """
        Process route recommendation request between origin and destination.
        """
        return compute_routes(origin, destination, preference=preference)

    @staticmethod
    def map_coords_to_node(param: Any) -> Any:
        return find_node_by_name_or_coords(param)
