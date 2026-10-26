import pandas as pd
import numpy as np

def create_seasons(month):
    if month in [1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Pre-Monsoon'
    elif month in [6, 7, 8, 9]:
        return 'Monsoon'
    else:
        return 'Post-Monsoon'

def engineer_features(input_path, output_path, ner_output_path):
    print(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    initial_rows = len(df)
    
    # 1. Parse date and sort
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values(by=['state_name', 'date']).reset_index(drop=True)
    
    # 2. Handle missing values
    # For rainfall, filling missing with 0 to prevent downstream errors in rolling
    df['actual'] = pd.to_numeric(df['actual'], errors='coerce').fillna(0)
    df['normal'] = pd.to_numeric(df['normal'], errors='coerce').fillna(0)
    
    # 3. Temporal features
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['day_of_year'] = df['date'].dt.dayofyear
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['quarter'] = df['date'].dt.quarter
    df['season'] = df['month'].apply(create_seasons)
    
    # 4. Rolling cumulative features per state
    # Leakage check: .rolling(min_periods=1) includes current day and X past days. No future data.
    grouped = df.groupby('state_name')['actual']
    df['rainfall_1d'] = df['actual']
    df['rainfall_3d'] = grouped.rolling(window=3, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainfall_7d'] = grouped.rolling(window=7, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainfall_14d'] = grouped.rolling(window=14, min_periods=1).sum().reset_index(level=0, drop=True)
    df['rainfall_30d'] = grouped.rolling(window=30, min_periods=1).sum().reset_index(level=0, drop=True)
    
    # 5. Rainfall Anomaly
    df['rainfall_anomaly'] = df['actual'] - df['normal']
    df['rainfall_anomaly_ratio'] = np.where(df['normal'] > 0, df['actual'] / df['normal'], 0)
    
    # 6. Extreme Rainfall
    # Using the 95th percentile per state as a dynamic threshold for extreme rainfall indicator
    thresholds = df.groupby('state_name')['actual'].transform(lambda x: x.quantile(0.95))
    df['extreme_rainfall_indicator'] = (df['actual'] > thresholds).astype(int)
    
    # Consec rainy days (actual > 2.5 mm)
    # create a mask, use cumsum to isolate blocks of continuous rainy days, then cumcount
    df['is_rainy'] = (df['actual'] > 2.5)
    
    def count_consecutive(s):
        return s.groupby((~s).cumsum()).cumcount() + s
        
    df['consecutive_rainy_days'] = df.groupby('state_name')['is_rainy'].apply(count_consecutive).reset_index(level=0, drop=True)
    
    df.drop('is_rainy', axis=1, inplace=True)
    
    # 7. NER Subset
    ner_states = ['Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura']
    ner_df = df[df['state_name'].isin(ner_states)].copy()
    
    df.to_csv(output_path, index=False)
    ner_df.to_csv(ner_output_path, index=False)
    
    print(f"Data processed successfully.")
    print(f"Original rows: {initial_rows}")
    print(f"Processed rows: {len(df)}")
    print(f"NER rows: {len(ner_df)}")
    print(f"Total features created: {len(df.columns) - 8}") # Subtracting base 8 columns
    print("Files saved to data/processed/")

if __name__ == "__main__":
    input_csv = "c:/NER-Smart-Logistics/data/raw/daily-rainfall-at-state-level.csv"
    output_csv = "c:/NER-Smart-Logistics/data/processed/rainfall_features.csv"
    ner_csv = "c:/NER-Smart-Logistics/data/processed/ner_rainfall_features.csv"
    engineer_features(input_csv, output_csv, ner_csv)
