import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score

def train_isolation_forest():
    """
    Trains an unsupervised Isolation Forest model strictly on legitimate transactions (y_train == 0).
    Learns the normal distribution manifold to flag zero-day anomalous patterns without labels.
    """
    print("=" * 70)
    print("TIER 2: ISOLATION FOREST (UNSUPERVISED ANOMALY DETECTION)")
    print("=" * 70)

    X_train = pd.read_pickle("data/processed/X_train.pkl")
    X_val = pd.read_pickle("data/processed/X_val.pkl")
    X_test = pd.read_pickle("data/processed/X_test.pkl")

    train_df = pd.read_pickle("data/processed/train_df.pkl")
    val_df = pd.read_pickle("data/processed/val_df.pkl")
    test_df = pd.read_pickle("data/processed/test_df.pkl")

    y_train = train_df["is_fraud"].to_numpy()
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    # Train ONLY on legitimate transactions (unsupervised clean baseline)
    normal_mask = (y_train == 0)
    X_train_normal = X_train[normal_mask]

    print(f"Training on {len(X_train_normal):,} strictly legitimate baseline transactions...")
    iso_forest = IsolationForest(
        n_estimators=250,
        max_samples=0.8,
        contamination=0.015,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train_normal)

    # Invert decision function so higher score = more anomalous
    # IsolationForest.decision_function outputs positive for normal, negative for anomaly
    val_scores = -iso_forest.decision_function(X_val)
    test_scores = -iso_forest.decision_function(X_test)

    # Normalize scores to [0, 1] range for intuitive risk scoring
    s_min, s_max = val_scores.min(), val_scores.max()
    val_risk = (val_scores - s_min) / max(s_max - s_min, 1e-9)
    test_risk = (test_scores - s_min) / max(s_max - s_min, 1e-9)

    val_pr_auc = average_precision_score(y_val, val_risk)
    test_pr_auc = average_precision_score(y_test, test_risk)

    print(f"\n[Unsupervised Benchmark]")
    print(f"Test Prevalence Baseline: {y_test.mean():.5f}")
    print(f"Validation PR-AUC:        {val_pr_auc:.4f}")
    print(f"Test PR-AUC:              {test_pr_auc:.4f}")

    # Freeze threshold on validation set
    thresholds = np.linspace(0.1, 0.9, 81)
    best_f1, frozen_thr = 0.0, 0.5
    for thr in thresholds:
        pred_v = (val_risk >= thr).astype(int)
        f1_v = f1_score(y_val, pred_v, zero_division=0)
        if f1_v > best_f1:
            best_f1 = f1_v
            frozen_thr = float(thr)

    test_pred = (test_risk >= frozen_thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, test_pred).ravel()
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = f1_score(y_test, test_pred, zero_division=0)

    print(f"\nFrozen Threshold (Validation Optimal): {frozen_thr:.2f}")
    print(f"Test Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | FP: {fp} | FN: {fn}")

    # Per-fraud-family breakdown for zero-day efficacy analysis
    print("\n--- Per-Fraud-Type Anomaly Detection PR-AUC ---")
    for ft in sorted(test_df["fraud_type"].dropna().unique()):
        if ft == "normal":
            continue
        mask = test_df["fraud_type"].isin(["normal", ft]).to_numpy()
        ap = average_precision_score(test_df.loc[mask, "is_fraud"], test_risk[mask])
        n_cases = (test_df.fraud_type == ft).sum()
        print(f"{ft:22s} n={n_cases:4d}  PR-AUC={ap:.4f}")

    # Save artifacts
    Path("models_artifacts").mkdir(parents=True, exist_ok=True)
    artifact_path = "models_artifacts/isolation_forest_tier2.joblib"
    joblib.dump(iso_forest, artifact_path)
    print(f"\nModel artifact saved to: {artifact_path}")
    return iso_forest

if __name__ == "__main__":
    train_isolation_forest()
