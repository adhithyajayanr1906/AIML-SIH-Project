"""
ml/analytics/rainfall_analytics.py
==================================
Analytics engine for real historical rainfall datasets in North Eastern India.
Source: data/processed/ner_rainfall_features.csv
Coverage: 2009-01-01 to 2024-07-31 across all 8 NER states.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional

CSV_PATH = os.path.abspath("c:/NER-Smart-Logistics/data/processed/ner_rainfall_features.csv")

_CACHE: Optional[Dict[str, Any]] = None

def get_rainfall_summary() -> Dict[str, Any]:
    """Returns overall metadata and state comparative summaries."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    if not os.path.exists(CSV_PATH):
        return {
            "status": "UNAVAILABLE",
            "error": "Rainfall dataset not found.",
            "record_count": 0
        }

    df = pd.read_csv(CSV_PATH)
    
    # State-level metrics
    states = sorted(df['state_name'].unique().tolist())
    state_summaries = []

    for state in states:
        sub = df[df['state_name'] == state]
        total_records = len(sub)
        mean_actual_daily = float(sub['actual'].mean())
        mean_normal_daily = float(sub['normal'].mean())
        annual_actual_est = round(mean_actual_daily * 365.25, 1)
        annual_normal_est = round(mean_normal_daily * 365.25, 1)
        extreme_count = int(sub['extreme_rainfall_indicator'].sum())
        max_daily = float(sub['actual'].max())
        mean_anomaly = float(sub['rainfall_anomaly'].mean())

        state_summaries.append({
            "state_name": state,
            "total_records": total_records,
            "estimated_annual_actual_mm": annual_actual_est,
            "estimated_annual_normal_mm": annual_normal_est,
            "mean_daily_actual_mm": round(mean_actual_daily, 2),
            "mean_daily_normal_mm": round(mean_normal_daily, 2),
            "extreme_days_count": extreme_count,
            "max_single_day_rainfall_mm": round(max_daily, 1),
            "mean_rainfall_anomaly_mm": round(mean_anomaly, 2)
        })

    # Overall dataset metadata
    min_date = str(df['date'].min())
    max_date = str(df['date'].max())
    total_records = len(df)
    missing_actual = int(df['actual'].isnull().sum())
    missing_normal = int(df['normal'].isnull().sum())

    _CACHE = {
        "status": "AVAILABLE",
        "spatial_resolution": "State-level aggregates (8 North Eastern States)",
        "temporal_resolution": "Daily time series",
        "date_range": {
            "start": min_date,
            "end": max_date,
            "total_days": total_records // len(states),
            "total_records": total_records
        },
        "data_quality": {
            "missing_actual_values": missing_actual,
            "missing_normal_values": missing_normal,
            "completeness_pct": 100.0 if missing_actual == 0 else round((1 - missing_actual/total_records)*100, 2)
        },
        "states": state_summaries
    }
    return _CACHE


def get_state_rainfall_trends(state_name: str) -> Dict[str, Any]:
    """
    Returns monthly climatology and annual time-series for a specific NER state.
    """
    if not os.path.exists(CSV_PATH):
        return {"error": "Rainfall dataset not found."}

    df = pd.read_csv(CSV_PATH)
    sub = df[df['state_name'].str.lower() == state_name.lower()]
    
    if sub.empty:
        return {"error": f"State '{state_name}' not found. Available states: {sorted(df['state_name'].unique().tolist())}"}

    canonical_name = sub['state_name'].iloc[0]

    # Monthly climatology (Jan-Dec)
    monthly_agg = sub.groupby('month').agg({
        'actual': 'mean',
        'normal': 'mean',
        'rainfall_anomaly': 'mean'
    }).reset_index()

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data = []
    for _, row in monthly_agg.iterrows():
        m_idx = int(row['month']) - 1
        monthly_data.append({
            "month_num": int(row['month']),
            "month_name": months[m_idx] if 0 <= m_idx < 12 else str(row['month']),
            "actual_daily_avg_mm": round(float(row['actual']), 2),
            "normal_daily_avg_mm": round(float(row['normal']), 2),
            "anomaly_mm": round(float(row['rainfall_anomaly']), 2)
        })

    # Annual trends (2009-2024)
    annual_agg = sub.groupby('year').agg({
        'actual': 'sum',
        'normal': 'sum',
        'rainfall_anomaly': 'mean',
        'extreme_rainfall_indicator': 'sum'
    }).reset_index()

    annual_data = []
    for _, row in annual_agg.iterrows():
        annual_data.append({
            "year": int(row['year']),
            "total_actual_mm": round(float(row['actual']), 1),
            "total_normal_mm": round(float(row['normal']), 1),
            "mean_anomaly_mm": round(float(row['rainfall_anomaly']), 2),
            "extreme_days": int(row['extreme_rainfall_indicator'])
        })

    # Seasonal breakdown
    seasonal_agg = sub.groupby('season').agg({
        'actual': 'mean',
        'normal': 'mean'
    }).reset_index()
    seasonal_data = []
    for _, row in seasonal_agg.iterrows():
        seasonal_data.append({
            "season": str(row['season']),
            "daily_avg_actual_mm": round(float(row['actual']), 2),
            "daily_avg_normal_mm": round(float(row['normal']), 2)
        })

    return {
        "state_name": canonical_name,
        "date_range": f"{sub['date'].min()} to {sub['date'].max()}",
        "monthly_climatology": monthly_data,
        "annual_trends": annual_data,
        "seasonal_breakdown": seasonal_data,
        "caveat": "Historical observed state-level data. Does not represent real-time sensor feeds or micro-district hyper-local forecasts."
    }
