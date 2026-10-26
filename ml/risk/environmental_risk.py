def calculate_environmental_risk(rainfall_anomaly, extreme_indicator, slope, elev, ndvi):
    """
    Calculates deterministic Environmental Risk Factor (0.0 to 1.0).
    Based strictly on available covariate datatypes. 
    Not ML.
    """
    # Normalize features bounded [0, 1]
    norm_rain = min(max(rainfall_anomaly / 100.0, 0), 1)
    norm_slope = min(max(slope / 45.0, 0), 1)  # 45+ deg is max risk
    norm_elev = max(0, 1 - (elev / 2000.0))  # lower elevations more flood prone 
    norm_ndvi = max(0, 1 - (min(ndvi, 1))) # lower ndvi means less root strength
    
    # Example heuristic weighting
    w_r = 0.40
    w_s = 0.30
    w_e = 0.15
    w_n = 0.15
    
    risk_score = (w_r * norm_rain) + (w_s * norm_slope) + (w_e * norm_elev) + (w_n * norm_ndvi)
    
    # Boost if extreme rainfall flag is 1
    if extreme_indicator == 1:
        risk_score = min(risk_score * 1.5, 1.0)
        
    factors = {
        "rainfall_risk": round(norm_rain, 3),
        "slope_risk": round(norm_slope, 3),
        "elevation_exposure": round(norm_elev, 3),
        "vegetation_exposure": round(norm_ndvi, 3)
    }
    
    if risk_score > 0.75:
        category = "CRITICAL"
    elif risk_score > 0.50:
        category = "HIGH"
    elif risk_score > 0.25:
        category = "MODERATE"
    else:
        category = "LOW"
        
    return risk_score, category, factors
