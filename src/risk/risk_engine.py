from typing import Dict, Any, List
from config.config import (
    RISK_THRESHOLD_LOW,
    RISK_THRESHOLD_HIGH,
    LOGISTICS_WEIGHT_ENV,
    LOGISTICS_WEIGHT_ROAD,
    LOGISTICS_WEIGHT_REPORT
)

def categorize_risk(probability: float) -> str:
    """
    Categorize environmental flood risk probability using prototype risk thresholds.
    Thresholds:
    0.00 - 0.34 -> LOW
    0.35 - 0.69 -> MEDIUM
    0.70 - 1.00 -> HIGH
    """
    if probability < RISK_THRESHOLD_LOW:
        return "LOW"
    elif probability < RISK_THRESHOLD_HIGH:
        return "MEDIUM"
    else:
        return "HIGH"

def calculate_logistics_risk_score(
    environmental_flood_risk: float,
    road_accessibility_risk: float = 0.0,
    field_report_risk: float = 0.0
) -> float:
    """
    Logistics Risk Layer: A decision-support calculation combining multiple signals:
    Logistics Risk Score = (0.60 * Environmental Flood Risk) + (0.25 * Road Risk) + (0.15 * Field Report Risk)
    """
    score = (
        LOGISTICS_WEIGHT_ENV * environmental_flood_risk +
        LOGISTICS_WEIGHT_ROAD * road_accessibility_risk +
        LOGISTICS_WEIGHT_REPORT * field_report_risk
    )
    return round(float(min(max(score, 0.0), 1.0)), 4)

def calculate_delay_estimate(
    probability: float,
    rainfall: float = 0.0,
    water_level: float = 0.0,
    river_discharge: float = 0.0
) -> int:
    """
    Calculate estimated travel delay in minutes based on environmental risk probability
    and hydrological parameters.
    """
    base_delay = 5.0
    rain_penalty = min(rainfall * 0.15, 45.0)
    water_penalty = min(water_level * 4.0, 30.0)
    risk_penalty = probability * 75.0
    
    total_delay = base_delay + rain_penalty + water_penalty + risk_penalty
    return int(round(total_delay))

def derive_key_factors(input_dict: Dict[str, Any], probability: float) -> List[str]:
    """
    Extract key environmental contributing factors from sample input data.
    """
    factors = []
    
    rainfall = float(input_dict.get("Rainfall (mm)", input_dict.get("Rainfall", 0)))
    water_level = float(input_dict.get("Water Level (m)", input_dict.get("Water_Level", 0)))
    river_discharge = float(input_dict.get("River Discharge (m³/s)", input_dict.get("River_Discharge", 0)))
    elevation = float(input_dict.get("Elevation (m)", input_dict.get("Elevation", 0)))
    hist_floods = float(input_dict.get("Historical Floods", input_dict.get("Historical_Floods", 0)))
    land_cover = str(input_dict.get("Land Cover", ""))
    soil_type = str(input_dict.get("Soil Type", ""))

    if rainfall > 150:
        factors.append(f"Heavy Rainfall ({rainfall:.1f} mm)")
    elif rainfall > 80:
        factors.append(f"Moderate Rain ({rainfall:.1f} mm)")
        
    if water_level > 6.0:
        factors.append(f"Critical River Water Level ({water_level:.1f} m)")
    elif water_level > 3.5:
        factors.append(f"Elevated Water Level ({water_level:.1f} m)")
        
    if river_discharge > 3000:
        factors.append(f"High River Surge Discharge ({river_discharge:.0f} m³/s)")
        
    if hist_floods > 0:
        factors.append("Historical Flood Vulnerability Zone")
        
    if land_cover in ["Water Body", "Desert"]:
        factors.append(f"Vulnerable Land Cover ({land_cover})")
        
    if soil_type in ["Clay", "Peat"]:
        factors.append(f"Poor Drainage Soil ({soil_type})")
        
    if elevation > 4000:
        factors.append("High Altitude Mountain Terrain")
        
    if not factors:
        if probability >= 0.5:
            factors.append("Combined Hydrological and Geographical Vulnerability")
        else:
            factors.append("Optimal Environmental and Road Conditions")

    return factors
