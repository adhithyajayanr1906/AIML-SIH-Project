import pandas as pd
import json

file_path = "c:\\NER-Smart-Logistics\\data\\your_dataset.csv"
df = pd.read_csv(file_path)

stats = {
    "rows": len(df),
    "cols": len(df.columns),
    "columns": list(df.columns),
    "head": df.head(5).to_dict()
}

with open("c:\\NER-Smart-Logistics\\data_stats.json", "w") as f:
    json.dump(stats, f)
