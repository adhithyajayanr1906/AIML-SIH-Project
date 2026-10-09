import os
import joblib
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from config.config import PREPROCESSOR_PATH

class DataPreprocessor:
    def __init__(self, target_column: str, latitude_column: str = None, longitude_column: str = None):
        self.target_column = target_column
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
        self.preprocessor = None
        self.feature_names = []
        self.num_cols = []
        self.cat_cols = []

    def fit_transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, pd.Series, pd.Series]:
        """
        Clean missing values, fit transformer pipeline, encode categoricals,
        scale numericals, split train/test sets, and save preprocessor state.
        """
        # Separate features and target
        X = df.drop(columns=[self.target_column])
        y = df[self.target_column]

        # Identify feature columns
        self.num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        self.cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

        # Numeric pipeline
        num_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])

        # Categorical pipeline
        cat_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        # Combined preprocessor
        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", num_pipeline, self.num_cols),
                ("cat", cat_pipeline, self.cat_cols)
            ]
        )

        X_processed = self.preprocessor.fit_transform(X)

        # Retrieve feature names after one-hot encoding
        cat_feature_names = []
        if self.cat_cols:
            onehot_encoder = self.preprocessor.named_transformers_["cat"].named_steps["onehot"]
            cat_feature_names = onehot_encoder.get_feature_names_out(self.cat_cols).tolist()
        self.feature_names = self.num_cols + cat_feature_names

        # Train / Test Split
        X_train, X_test, y_train, y_test = train_test_split(
            X_processed, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) <= 5 else None
        )

        # Save preprocessor state
        self.save_preprocessor()

        return X_train, X_test, y_train, y_test

    def transform_input(self, input_data: Dict[str, Any]) -> np.ndarray:
        """
        Transform raw input dict or DataFrame for model inference.
        """
        if self.preprocessor is None:
            self.load_preprocessor()

        if isinstance(input_data, dict):
            df_single = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.DataFrame):
            df_single = input_data.copy()
        else:
            raise ValueError("input_data must be dict or DataFrame")

        # Ensure all required features are present
        for col in self.num_cols:
            if col not in df_single.columns:
                df_single[col] = 0.0
        for col in self.cat_cols:
            if col not in df_single.columns:
                df_single[col] = "Unknown"

        X_single = df_single[self.num_cols + self.cat_cols]
        return self.preprocessor.transform(X_single)

    def save_preprocessor(self, path: str = PREPROCESSOR_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self, path)
        print(f"Preprocessor saved to: {path}")

    @classmethod
    def load_preprocessor(cls, path: str = PREPROCESSOR_PATH) -> "DataPreprocessor":
        if not os.path.exists(path):
            raise FileNotFoundError(f"No preprocessor file found at {path}. Run training pipeline first.")
        obj = joblib.load(path)
        print(f"Preprocessor loaded from: {path}")
        return obj

if __name__ == "__main__":
    from src.data.load_dataset import load_dataset
    df, info = load_dataset()
    dp = DataPreprocessor(
        target_column=info["target_column"],
        latitude_column=info["latitude_column"],
        longitude_column=info["longitude_column"]
    )
    X_train, X_test, y_train, y_test = dp.fit_transform(df)
    print(f"X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")
