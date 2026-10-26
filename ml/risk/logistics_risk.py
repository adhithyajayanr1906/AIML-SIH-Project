def calculate_logistics_risk(env_risk_score, length_m, road_type):
    """
    Calculates deterministic Logistics Risk Score.
    """
    # Road vulnerability multipliers based on assumed structural integrity
    # Motorways handle environment better than unclassified tracks
    road_vulnerability = {
        'motorway': 0.5,
        'trunk': 0.6,
        'primary': 0.7,
        'secondary': 0.8,
        'tertiary': 0.9,
        'residential': 1.0,
        'unclassified': 1.2,
        'service': 1.0,
        'unknown': 1.0
    }
    
    vul_factor = road_vulnerability.get(road_type.lower(), 1.0)
    
    # Distance scaling: longer roads have more exposure length
    # Assume base segment length penalty (log scale to prevent extreme inflation)
    import math
    if length_m <= 0: length_m = 1
    dist_exposure = max(1, math.log10(length_m) / 3) 
    
    logistics_risk = min(env_risk_score * vul_factor * dist_exposure, 1.0)
    
    if logistics_risk > 0.75:
        category = "CRITICAL"
    elif logistics_risk > 0.50:
        category = "HIGH"
    elif logistics_risk > 0.25:
        category = "MODERATE"
    else:
        category = "LOW"
        
    factors = {
        "environmental_risk_base": round(env_risk_score, 3),
        "infrastructure_vulnerability": vul_factor,
        "exposure_distance_penalty": round(dist_exposure, 3)
    }
    return logistics_risk, category, factors
