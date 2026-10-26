SUITABLE

# Dataset Analysis Report

## 1. Dataset Overview
This dataset contains daily rainfall data aggregated at the state level across India.

## 2. Dataset Size
* Total Rows: 204876
* Total Columns: 8
* File Size: 11.97 MB

## 3. Columns
* id
* date
* state_code
* state_name
* actual (Actual Rainfall)
* rfs
* normal (Normal Rainfall)
* deviation (Rainfall Deviation)

## 4. Missing Values
```
id                0
date              0
state_code        0
state_name        0
actual        17162
rfs            5865
normal        11518
deviation     31021
```

## 5. NER State Coverage
| State | Present? | Number of records |
| ----- | -------- | ----------------- |
| Arunachal Pradesh | Yes | 5691 |
| Assam | Yes | 5691 |
| Manipur | Yes | 5691 |
| Meghalaya | Yes | 5691 |
| Mizoram | Yes | 5691 |
| Nagaland | Yes | 5691 |
| Sikkim | Yes | 5691 |
| Tripura | Yes | 5691 |


## 6. Rainfall Analysis
The dataset contains daily entries for rainfall data points (`actual`, `normal`, `deviation`). This allows tracking daily distributions.

## 7. Potential ML Features
* daily rainfall
* 3-day cumulative rainfall
* 7-day cumulative rainfall
* 14-day cumulative rainfall
* 30-day cumulative rainfall
* rainfall anomaly
* rainfall intensity
* consecutive rainy days
* extreme rainfall indicator
* monthly rainfall
* seasonal rainfall
* rainfall trend

## 8. Potential Target Variables
Dataset contains rainfall information but does not contain a verified flood-occurrence target.
Therefore, "Flood Risk" can only be a derived engineering rule rather than a ground-truth ML label unless augmented.

## 9. Missing Project Requirements
| Project Requirement | Available? | Relevant Columns |
| ------------------- | ---------- | ---------------- |
| latitude            | No         | N/A |
| longitude           | No         | N/A |
| elevation           | No         | N/A |
| terrain             | No         | N/A |
| soil                | No         | N/A |
| river level         | No         | N/A |
| flood occurrence    | No         | N/A |
| landslide occurrence| No         | N/A |
| road condition      | No         | N/A |
| traffic             | No         | N/A |
| road blockage       | No         | N/A |
| travel time         | No         | N/A |
| ETA                 | No         | N/A |
| GPS route data      | No         | N/A |
| infrastructure      | No         | N/A |
| field reports       | No         | N/A |

## 10. Dataset Limitations
The dataset lacks geographical precision (district/lat/long), meaning true graph routing logic cannot be solely based on this.

## 11. Recommended ML Usage
Time-series forecasting of daily/weekly rainfall anomalies using XGBoost or LightGBM, and establishing heuristic risk thresholds for simulated areas.

## 12. Final Verdict
PARTIALLY SUITABLE (Due to lack of flood labels and geospatial routing nodes, but satisfies time-series rainfall modeling for risk scoring).

## 13. Feature Engineering
We engineered several temporal and rainfall specific features for all states and separated out a specific subset for the 8 North-Eastern states.

| Feature | Meaning | Calculation | Used for |
| ------- | ------- | ----------- | -------- |
| year/month/day | Date parts | Parsed from date | Seasonality/Trends |
| day_of_year/week_of_year/quarter | Time of year | Pandas datetime | Periodic mapping |
| season | Climate Season | Map (1-2: Winter, 3-5: Pre-Monsoon, 6-9: Monsoon, 10-12: Post-Monsoon) | Rainfall regimes |
| rainfall_1d/3d/7d/14d/30d | Short-term cumulative rainfall | `.rolling(window=x, min_periods=1).sum()` | Saturation/flood risk proxies |
| rainfall_anomaly | Raw rainfall diff | `actual - normal` | Identify unusual rain |
| rainfall_anomaly_ratio | Ratio of baseline rain | `actual / normal` | Scale-invariant anomaly |
| extreme_rainfall_indicator | Flag for top 5% rain | `1` if actual > 95th percentile statewise, else `0` | Extreme event flag |
| consecutive_rainy_days | Streak of rainy days | Cumulative sum of days where `actual > 2.5mm` | Monsoon persistence |

> [!WARNING]
> This rainfall dataset does not contain a verified flood-occurrence target. Therefore, the engineered rainfall features are environmental predictors/indicators and are not themselves ground-truth flood labels.
