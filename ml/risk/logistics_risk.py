from typing import Dict, Any

def calculate_logistics_risk(
    environmental_risk: float,
    road_accessibility_risk: float = 0.0,
    field_report_risk: float = 0.0
) -> Dict[str, Any]:
    """
    Logistics Risk Scoring Decision Support Calculation:
    Logistics Risk Score = (0.60 * Environmental Risk) + (0.25 * Road Risk) + (0.15 * Field Report Risk)
    """
    env_risk = float(min(max(environmental_risk, 0.0), 1.0))
    road_risk = float(min(max(road_accessibility_risk, 0.0), 1.0))
    report_risk = float(min(max(field_report_risk, 0.0), 1.0))

    score = (0.60 * env_risk) + (0.25 * road_risk) + (0.15 * report_risk)
    score = round(min(max(score, 0.0), 1.0), 4)

    if score < 0.35:
        risk_level = "LOW"
    elif score < 0.70:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    estimated_delay_min = int(round(10.0 + (score * 120.0)))

    return {
        "logistics_risk_score": score,
        "risk_level": risk_level,
        "estimated_delay_minutes": estimated_delay_min,
        "weights_used": {
            "environmental_risk_weight": 0.60,
            "road_accessibility_weight": 0.25,
            "field_report_weight": 0.15
        }
    }
