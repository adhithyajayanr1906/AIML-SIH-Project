import os
import json
import streamlit as st
import pandas as pd
from config.config import METADATA_PATH

def render_insights_page():
    st.markdown("### Machine Learning Model Evaluation and Performance Insights")
    st.caption("Empirical metrics, baseline comparisons, confusion matrices, and feature importance derived dynamically from model training artifacts.")

    if not os.path.exists(METADATA_PATH):
        st.warning("Model metadata artifact not found. Run model training pipeline first: `python -m src.ml.train_model`.")
        return

    with open(METADATA_PATH, "r") as f:
        meta = json.load(f)

    best_model_name = meta.get("selected_model", "Selected Model")
    target_col = meta.get("target_column", "Flood Occurred")
    timestamp = meta.get("training_timestamp", "Unknown")
    metrics = meta.get("metrics", {})
    models_eval = meta.get("models_evaluated", {})
    importances = meta.get("feature_importances", [])

    st.markdown(f"#### Selected Model: `{best_model_name}`")
    st.caption(f"Target Column: `{target_col}` | Training Timestamp: `{timestamp}`")

    # Primary Metrics KPI
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Accuracy", f"{metrics.get('accuracy', 0.0)*100:.2f}%")
    with c2:
        st.metric("Precision", f"{metrics.get('precision', 0.0)*100:.2f}%")
    with c3:
        st.metric("Recall", f"{metrics.get('recall', 0.0)*100:.2f}%")
    with c4:
        st.metric("F1 Score", f"{metrics.get('f1_score', 0.0):.4f}")
    with c5:
        st.metric("ROC-AUC", f"{metrics.get('roc_auc', 0.0):.4f}")

    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Model Comparison Table")
        comp_rows = []
        for key, m in models_eval.items():
            comp_rows.append({
                "Model": m.get("model_name", key),
                "Accuracy": f"{m.get('accuracy', 0.0)*100:.2f}%",
                "Precision": f"{m.get('precision', 0.0)*100:.2f}%",
                "Recall": f"{m.get('recall', 0.0)*100:.2f}%",
                "F1 Score": f"{m.get('f1_score', 0.0):.4f}",
                "ROC-AUC": f"{m.get('roc_auc', 0.0):.4f}"
            })
        st.table(pd.DataFrame(comp_rows))

        st.subheader("Confusion Matrix")
        cm = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
        cm_df = pd.DataFrame(
            cm,
            index=["Actual Non-Flood (0)", "Actual Flood (1)"],
            columns=["Predicted Non-Flood (0)", "Predicted Flood (1)"]
        )
        st.table(cm_df)

    with col_right:
        st.subheader("Feature Importances")
        if importances:
            df_imp = pd.DataFrame(importances).head(10)
            df_chart = df_imp.set_index("feature")["importance"]
            st.bar_chart(df_chart)
            st.dataframe(df_imp, use_container_width=True)
        else:
            st.info("Feature importances not available for this model type.")
