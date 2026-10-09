import os
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, Optional
from config.config import (
    LOCAL_DATASET_PATH,
    TARGET_COLUMN_CANDIDATES,
    LATITUDE_CANDIDATES,
    LONGITUDE_CANDIDATES
)

def discover_datasets(base_search_paths: Optional[list] = None) -> list:
    """
    Recursively search for dataset files (CSV, XLSX) in local project folder or Google Drive MyDrive.
    """
    if base_search_paths is None:
        base_search_paths = [
            os.path.dirname(LOCAL_DATASET_PATH),
            "/content/drive/MyDrive",
            "/content/"
        ]
    
    discovered = []
    for base_dir in base_search_paths:
        if os.path.exists(base_dir):
            for root, _, files in os.walk(base_dir):
                for file_name in files:
                    if file_name.endswith((".csv", ".xlsx", ".xls")) and not file_name.startswith("~$"):
                        full_path = os.path.join(root, file_name)
                        discovered.append(full_path)
    return discovered

def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspect dataset schema, missing values, column types, lat/lon candidates,
    target variable, and feature split.
    """
    cols = df.columns.tolist()
    missing_dict = df.isnull().sum().to_dict()
    dtypes_dict = {col: str(df[col].dtype) for col in cols}
    unique_dict = {col: int(df[col].nunique()) for col in cols}
    
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    
    lat_col = next((c for c in cols if c in LATITUDE_CANDIDATES or c.lower() == "lat"), None)
    lon_col = next((c for c in cols if c in LONGITUDE_CANDIDATES or c.lower() in ["lon", "lng"]), None)
    
    # Priority 1: Exact candidate match for target
    target_col = next((c for c in cols if c in TARGET_COLUMN_CANDIDATES), None)
    # Priority 2: Keyword match
    if not target_col:
        target_col = next((c for c in cols if "target" in c.lower() or "disruption" in c.lower()), None)
    if not target_col and num_cols:
        target_col = num_cols[-1]
        
    task_type = "classification"
    if target_col and df[target_col].nunique() > 10 and np.issubdtype(df[target_col].dtype, np.number):
        task_type = "regression"
        
    return {
        "num_records": len(df),
        "num_columns": len(cols),
        "columns": cols,
        "dtypes": dtypes_dict,
        "missing_values": missing_dict,
        "unique_values": unique_dict,
        "total_missing": int(df.isnull().sum().sum()),
        "numerical_columns": num_cols,
        "categorical_columns": cat_cols,
        "latitude_column": lat_col,
        "longitude_column": lon_col,
        "target_column": target_col,
        "task_type": task_type,
        "sample_head": df.head(5).to_dict(orient="records")
    }

def load_dataset(dataset_path: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load dataset from specified path, local fallback, or discovered Drive path.
    Returns (DataFrame, DatasetInfo).
    """
    target_path = dataset_path or LOCAL_DATASET_PATH
    
    if not os.path.exists(target_path):
        discovered = discover_datasets()
        if discovered:
            target_path = discovered[0]
        else:
            raise FileNotFoundError(
                f"Dataset not found at '{target_path}'. Upload CSV/XLSX file to workspace or Google Drive MyDrive."
            )
            
    print(f"Loading dataset from: {target_path}")
    if target_path.endswith(".csv"):
        df = pd.read_csv(target_path)
    elif target_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(target_path)
    else:
        raise ValueError(f"Unsupported file format for dataset: {target_path}")
        
    info = inspect_dataset(df)
    info["file_path"] = target_path
    return df, info

if __name__ == "__main__":
    df, info = load_dataset()
    print("--- DATASET INSPECTION SUMMARY ---")
    print(f"Records: {info['num_records']}, Columns: {info['num_columns']}")
    print(f"Target Column: {info['target_column']} ({info['task_type']})")
    print(f"Latitude Column: {info['latitude_column']}, Longitude Column: {info['longitude_column']}")
    print(f"Categorical Features: {info['categorical_columns']}")
    print(f"Numerical Features: {info['numerical_columns']}")
