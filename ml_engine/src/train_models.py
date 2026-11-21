import os
import sys
import json
import joblib

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score, confusion_matrix
)
from ml_engine.src.data_preprocessor import KYCDataPreprocessor

def train_and_evaluate_all():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_path = os.path.join(base_dir, "data", "synthetic_kyc_dataset.csv")
    models_dir = os.path.join(base_dir, "saved_models")
    os.makedirs(models_dir, exist_ok=True)

    print(f"Loading synthetic dataset from {data_path}...")
    df = pd.read_csv(data_path)

    # Train / Test split (80/20) with stratification
    train_df, test_df = train_test_split(df, test_size=0.20, random_state=42, stratify=df["is_fraud"])
    print(f"Training samples: {len(train_df)}, Testing samples: {len(test_df)}")

    # Fit preprocessor strictly on training data
    preprocessor = KYCDataPreprocessor()
    X_train, y_train = preprocessor.fit_transform(train_df)
    X_test, y_test = preprocessor.transform(test_df), test_df["is_fraud"]

    # Save fitted preprocessor
    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    preprocessor.save(preprocessor_path)
    print(f"Saved preprocessor to: {preprocessor_path}")

    # Compute positive class scale weight for XGBoost
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    scale_pos = neg_count / pos_count

    # Define candidate models
    models = {
        "Logistic_Regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        ),
        "Random_Forest": RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.08,
            scale_pos_weight=scale_pos,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1
        )
    }

    metrics_summary = {}

    for name, model in models.items():
        print(f"\n--- Training {name} ---")
        model.fit(X_train, y_train)

        # Predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred))
        roc_auc = float(roc_auc_score(y_test, y_prob))
        pr_auc = float(average_precision_score(y_test, y_prob))
        cm = confusion_matrix(y_test, y_pred).tolist()

        metrics_summary[name] = {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": cm
        }

        print(f"Results for {name}:")
        print(f"  ROC-AUC:   {roc_auc:.4f}")
        print(f"  PR-AUC:    {pr_auc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall:    {rec:.4f}")
        print(f"  F1-Score:  {f1:.4f}")

        # Save model artifact
        save_path = os.path.join(models_dir, f"{name.lower()}_model.joblib")
        joblib.dump(model, save_path)
        print(f"  Artifact saved -> {save_path}")

    # Determine best model based on ROC-AUC & F1 combination
    best_model_name = max(metrics_summary, key=lambda k: metrics_summary[k]["roc_auc"] + metrics_summary[k]["f1_score"])
    print(f"\nSelected Best Model: {best_model_name}")

    metrics_payload = {
        "best_model": best_model_name,
        "feature_names": preprocessor.feature_names,
        "models": metrics_summary
    }

    metrics_file = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_file, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved model metrics comparison to {metrics_file}")

    return metrics_payload

if __name__ == "__main__":
    train_and_evaluate_all()
