# Data Limitations & Methodology

## Derived Risk Engine Constraints
The current system operates purely on a heuristically derived Environmental and Logistics Risk Engine rather than empirical historic modeling.

**The current system does not perform supervised historical flood or landslide event prediction because no verified historical event labels are available in the selected datasets.**

The platform calculates mathematical exposure rather than classifying imminent disasters.

## What it DOES perform:
* **Rainfall Intelligence**: Tracks daily/rolling rainfall accumulations per state.
* **Environmental Risk Assessment**: Maps topographic extremes (steep slopes, low elevations, low vegetation).
* **Geospatial Environmental Exposure Analysis**: Links OpenStreetMap roads to underlying geographic vulnerabilities.
* **Road Risk Assessment**: Factors road infrastructure class against spatial vulnerabilities.
* **Risk-Aware Route Optimization**: Dynamically routes traffic around structurally perilous combinations of terrain and precipitation using `NetworkX` algorithms.

## What it DOES NOT perform:
* **Real-time Traffic**: We do not possess satellite live traffic APIs.
* **Real-time ETA**: Unless a reliable speed mapping configuration per Road Type exists on an active sensor, travel times are theoretical block distances (`distance_km`) lacking true congestion factors.
* **Supervised Disaster Accuracies**: There are no Precision/Recall/F1 scores to report since there is no `is_flooded = 1` target column.
