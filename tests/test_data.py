import os
import pytest
import pandas as pd
from src.data.load_dataset import load_dataset, inspect_dataset
from src.data.preprocess import DataPreprocessor

def test_dataset_file_exists():
    df, info = load_dataset()
    assert os.path.exists(info["file_path"])

def test_load_dataset():
    df, info = load_dataset()
    assert isinstance(df, pd.DataFrame)
    assert info["num_records"] > 0
    assert info["target_column"] == "Flood Occurred"
    assert info["total_missing"] == 0

def test_data_preprocessor():
    df, info = load_dataset()
    dp = DataPreprocessor(
        target_column=info["target_column"],
        latitude_column=info["latitude_column"],
        longitude_column=info["longitude_column"]
    )
    X_train, X_test, y_train, y_test = dp.fit_transform(df)
    assert X_train.shape[0] > 0
    assert X_test.shape[0] > 0
    assert len(dp.feature_names) > 0
