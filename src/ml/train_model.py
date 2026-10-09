import os
import json
# pyrefly: ignore [missing-import]
import joblib
from datetime import datetime
# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
# pyrefly: ignore [missing-import]
from xgboost import XGBClassifier

from config.config import MODEL_PATH, METADATA_PATH
from src.data.load_dataset import load_dataset
from src.data.preprocess import DataPreprocessor
from src.ml.evaluate import evaluate_classifier

def train_and_evaluate_models() -> Tuple[Any, DataPreprocessor, Dict[str, Any]]:
    """
    Train machine learning models on flood risk dataset, evaluate performance,
    dynamically select the best model, and export artifacts and metadata.
    """
    df, info = load_dataset()
    target_col = info["target_column"]
    lat_col = info["latitude_column"]
    lon_col = info["longitude_column"]

    print(f"Dataset loaded. Target column: '{target_col}' ({info['task_type']})")

    preprocessor = DataPreprocessor(
        target_column=target_col,
        latitude_column=lat_col,
        longitude_column=lon_col
    )
    X_train, X_test, y_train, y_test = preprocessor.fit_transform(df)

    feature_names = preprocessor.feature_names
    print(f"Total processed features: {len(feature_names)}")

    # Model 1: Logistic Regression
    print("Training Model 1: Logistic Regression...")
    lr_model = LogisticRegression(max_iter=1000, random_state=42)
    lr_model.fit(X_train, y_train)
    lr_metrics = evaluate_classifier(lr_model, X_test, y_test, model_name="Logistic Regression")
    print(f"Logistic Regression - Accuracy: {lr_metrics['accuracy']}, F1: {lr_metrics['f1_score']}")

    # Model 2: Random Forest
    print("Training Model 2: Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_metrics = evaluate_classifier(rf_model, X_test, y_test, model_name="Random Forest Classifier")
    print(f"Random Forest - Accuracy: {rf_metrics['accuracy']}, F1: {rf_metrics['f1_score']}")

    # Model 3: XGBoost
    print("Training Model 3: XGBoost Classifier...")
    xgb_model = XGBClassifier(n_estimators=150, max_depth=6, learning_rate=0.08, random_state=42, eval_metric="logloss")
    xgb_model.fit(X_train, y_train)
    xgb_metrics = evaluate_classifier(xgb_model, X_test, y_test, model_name="XGBoost Classifier")
    print(f"XGBoost - Accuracy: {xgb_metrics['accuracy']}, F1: {xgb_metrics['f1_score']}")

    # Dynamic Model Selection based on F1 Score
    candidate_models = [
        (lr_model, lr_metrics),
        (rf_model, rf_metrics),
        (xgb_model, xgb_metrics)
    ]
    
    best_model, best_metrics = max(candidate_models, key=lambda item: item[1]["f1_score"])
    best_model_name = best_metrics["model_name"]

    print("==========================================")
    print(f"SELECTED BEST MODEL: {best_model_name}")
    print(f"F1 Score: {best_metrics['f1_score']}, Accuracy: {best_metrics['accuracy']}, ROC-AUC: {best_metrics['roc_auc']}")
    print("==========================================")

    # Feature Importance Extraction
    importances = []
    if hasattr(best_model, "feature_importances_"):
        raw_imp = best_model.feature_importances_
        importances = sorted(
            [{"feature": name, "importance": round(float(imp), 4)} for name, imp in zip(feature_names, raw_imp)],
            key=lambda item: item["importance"],
            reverse=True
        )
    elif hasattr(best_model, "coef_"):
        raw_imp = np.abs(best_model.coef_[0])
        importances = sorted(
            [{"feature": name, "importance": round(float(imp), 4)} for name, imp in zip(feature_names, raw_imp)],
            key=lambda item: item["importance"],
            reverse=True
        )

    metadata = {
        "selected_model": best_model_name,
        "target_column": target_col,
        "feature_columns": feature_names,
        "metrics": best_metrics,
        "training_timestamp": datetime.utcnow().isoformat(),
        "models_evaluated": {
            "logistic_regression": lr_metrics,
            "random_forest": rf_metrics,
            "xgboost": xgb_metrics
        },
        "feature_importances": importances,
        "dataset_summary": {
            "records": info["num_records"],
            "features_count": len(feature_names)
        }
    }

    # Save Model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")

    # Save Metadata JSON
    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata saved to: {METADATA_PATH}")

    return best_model, preprocessor, metadata

if __name__ == "__main__":
    train_and_evaluate_models()
