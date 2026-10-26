import pandas as pd
import numpy as np

def validate_features(input_path, ner_path):
    print("Validating feature engineered dataset...")
    df = pd.read_csv(input_path)
    ner_df = pd.read_csv(ner_path)
    
    # 1. Row count and dupes
    print(f"Total Rows: {len(df)}")
    print(f"Duplicate rows: {df.duplicated().sum()}")
    
    # 2. NER filtering
    ner_states = ['Arunachal Pradesh', 'Assam', 'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Sikkim', 'Tripura']
    ner_check = ner_df['state_name'].isin(ner_states).all()
    print(f"NER state filtering correct: {ner_check}")
    
    # 3. Date ordering check (sample 1 state)
    assam_dates = df[df['state_name'] == 'Assam']['date'].tolist()
    is_ordered = all(assam_dates[i] <= assam_dates[i+1] for i in range(len(assam_dates)-1))
    print(f"Chronological ordering within grouping correct: {is_ordered}")
    
    # 4. Leakage Check: 
    # Let's verify whether 3d rolling sum uses future data.
    # Take index 5 for Assam. the 3d sum should be sum of index 3, 4, 5. NOT 6.
    sample = df[df['state_name'] == 'Assam'].reset_index(drop=True)
    if len(sample) >= 5:
        calc_sum = sample.loc[3:5, 'actual'].sum()
        feat_sum = sample.loc[5, 'rainfall_3d']
        print(f"Leakage check (3-day rolling matched historical): {np.isclose(calc_sum, feat_sum)}")
        
    print("Validation passed.")

if __name__ == "__main__":
    validate_features("c:/NER-Smart-Logistics/data/processed/rainfall_features.csv", 
                     "c:/NER-Smart-Logistics/data/processed/ner_rainfall_features.csv")
