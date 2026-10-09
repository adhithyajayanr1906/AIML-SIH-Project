from typing import Dict, Any, Optional, Union, List
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from ml.risk.environmental_risk import predict_environmental_risk
from ml.risk.logistics_risk import calculate_logistics_risk
from ml.geospatial.road_risk import get_road_risk_by_id
from backend.app.services.router import RoutingService

router = APIRouter()

# Request Models
class EnvironmentalRiskRequest(BaseModel):
    rainfall_mm: float = Field(150.0, description="Rainfall in mm")
    water_level_m: float = Field(5.0, description="Water level in meters")
    river_discharge_m3s: float = Field(2500.0, description="River discharge rate in m3/s")
    elevation_m: float = Field(1000.0, description="Elevation in meters")
    land_cover: str = Field("Forest", description="Land cover type")
    soil_type: str = Field("Loam", description="Soil classification type")

class LogisticsRiskRequest(BaseModel):
    environmental_risk: float = Field(0.50, ge=0.0, le=1.0)
    road_accessibility_risk: float = Field(0.20, ge=0.0, le=1.0)
    field_report_risk: float = Field(0.10, ge=0.0, le=1.0)

class RouteRecommendationRequest(BaseModel):
    origin: Union[str, Dict[str, float], List[float]] = Field(..., description="Origin hub name or coordinates dict {lat, lon}")
    destination: Union[str, Dict[str, float], List[float]] = Field(..., description="Destination hub name or coordinates dict {lat, lon}")
    preference: Optional[str] = Field("risk_aware", description="Routing preference: shortest, safest, or risk_aware")

@router.get("/health")
def health_check() -> Dict[str, str]:
    return {
        "status": "healthy",
        "service": "Smart Logistics Intelligence Platform"
    }

@router.post("/predict/environmental-risk")
def predict_environmental_risk_endpoint(request: EnvironmentalRiskRequest) -> Dict[str, Any]:
    try:
        return predict_environmental_risk(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/logistics-risk")
def predict_logistics_risk_endpoint(request: LogisticsRiskRequest) -> Dict[str, Any]:
    try:
        return calculate_logistics_risk(
            environmental_risk=request.environmental_risk,
            road_accessibility_risk=request.road_accessibility_risk,
            field_report_risk=request.field_report_risk
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/route/recommend")
def recommend_route_endpoint(request: RouteRecommendationRequest) -> Dict[str, Any]:
    try:
        res = RoutingService.recommend_route(
            origin=request.origin,
            destination=request.destination,
            preference=request.preference or "risk_aware"
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/road/{road_id}")
def get_road_risk_endpoint(road_id: str = Path(..., description="Road corridor ID or name")) -> Dict[str, Any]:
    try:
        return get_road_risk_by_id(road_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
