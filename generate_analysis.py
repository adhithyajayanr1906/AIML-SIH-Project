import pandas as pd
import json
import os

try:
    os.rename("c:\\NER-Smart-Logistics\\data\\your_dataset.csv", "c:\\NER-Smart-Logistics\\data\\daily-rainfall-at-state-level.csv")
except Exception:
    pass

file_path = "c:\\NER-Smart-Logistics\\data\\daily-rainfall-at-state-level.csv"
df = pd.read_csv(file_path)

ner_states = ["Arunachal Pradesh", "Assam", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Sikkim", "Tripura"]

# Check NER coverage
state_counts = df['state_name'].value_counts()
ner_coverage_rows = ""
for state in ner_states:
    count = state_counts.get(state, 0)
    present = "Yes" if count > 0 else "No"
    ner_coverage_rows += f"| {state} | {present} | {count} |\n"

# Other stats
total_rows = len(df)
total_cols = len(df.columns)
file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
min_date = df['date'].min() if 'date' in df.columns else "N/A"
max_date = df['date'].max() if 'date' in df.columns else "N/A"

null_counts_str = df.isnull().sum().to_string()

md_content = f"""SUITABLE

# Dataset Analysis Report

## 1. Dataset Overview
This dataset contains daily rainfall data aggregated at the state level across India.

## 2. Dataset Size
* Total Rows: {total_rows}
* Total Columns: {total_cols}
* File Size: {file_size_mb:.2f} MB

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
{null_counts_str}
```

## 5. NER State Coverage
| State | Present? | Number of records |
| ----- | -------- | ----------------- |
{ner_coverage_rows}

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
"""

with open("c:\\NER-Smart-Logistics\\docs\\DATASET_ANALYSIS.md", "w") as f:
    f.write(md_content)

nb_content = '''{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Rainfall Dataset Analysis\\n",
    "Loading and inspecting the state-level rainfall dataset."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\\n",
    "import numpy as np\\n",
    "import matplotlib.pyplot as plt\\n",
    "import seaborn as sns\\n",
    "df = pd.read_csv('../../data/daily-rainfall-at-state-level.csv')"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "df.info()\\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "df.isnull().sum()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "ner_states = ['Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura']\\n",
    "df_ner = df[df['state_name'].isin(ner_states)]\\n",
    "df_ner['state_name'].value_counts()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}'''

with open("c:\\NER-Smart-Logistics\\ml\\notebooks\\01_rainfall_dataset_analysis.ipynb", "w") as f:
    f.write(nb_content)

print(f"ROWS: {total_rows}")
print(f"COLS: {total_cols}")
print(f"NER_COUNT: {sum(state_counts.get(s, 0) for s in ner_states)}")
