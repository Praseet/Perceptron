"""Evaluation suite for the frozen Tier 1 + Tier 2 artifacts."""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score,
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    X_VAL_PKL, X_TEST_PKL, VAL_DF_PKL, TEST_DF_PKL,
    XGB_TIER1_JSON, ISO_FOREST_TIER2_JOBLIB,
    THRESHOLD_CANDIDATES, THRESHOLD_MIN, THRESHOLD_MAX,
    BUSINESS_THRESHOLDS,
)
from models import output as out


def _pr_auc(y_true, proba) -> float:
    return float(average_precision_score(y_true, proba))


def _pick_f1_threshold(y_val, val_proba) -> float:
    """Find the F1-optimal threshold on the validation split (frozen)."""
    candidates = np.linspace(THRESHOLD_MIN, THRESHOLD_MAX, THRESHOLD_CANDIDATES)
    scores = [
        (f1_score(y_val, (val_proba >= t).astype(int), zero_division=0), float(t))
        for t in candidates
    ]
    return max(scores)[1]


def _iso_proba(scores) -> np.ndarray:
    """Normalize Isolation Forest decision scores to [0, 1]."""
    s_min, s_max = scores.min(), scores.max()
    return (scores - s_min) / max(s_max - s_min, 1e-9)


def _business_table(test_proba, y_test, frozen_thr) -> list[list]:
    rows = []
    for thr in [*BUSINESS_THRESHOLDS, frozen_thr]:
        pred = (test_proba >= thr).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = f1_score(y_test, pred, zero_division=0)
        marker = "  <- frozen" if abs(thr - frozen_thr) < 1e-4 else ""
        rows.append([f"{thr:.2f}", f"{precision:.3f}", f"{recall:.3f}",
                     f"{f1:.3f}", int(fp), int(fn), marker])
    return rows


def main() -> None:
    out.banner("Evaluation suite")

    X_val = pd.read_pickle(X_VAL_PKL)
    X_test = pd.read_pickle(X_TEST_PKL)
    val_df = pd.read_pickle(VAL_DF_PKL)
    test_df = pd.read_pickle(TEST_DF_PKL)
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    out.step("Loading Tier 1 (XGBoost)...")
    xgb_model = xgb.XGBClassifier()
    xgb_model.load_model(XGB_TIER1_JSON)
    val_proba_xgb = xgb_model.predict_proba(X_val)[:, 1]
    test_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
    xgb_val_pr = _pr_auc(y_val, val_proba_xgb)
    xgb_test_pr = _pr_auc(y_test, test_proba_xgb)
    out.kv("Tier 1 val PR-AUC",  f"{xgb_val_pr:.4f}")
    out.kv("Tier 1 test PR-AUC", f"{xgb_test_pr:.4f}")

    iso_path = Path(ISO_FOREST_TIER2_JOBLIB)
    iso_proba_test = None
    if iso_path.exists():
        out.step("Loading Tier 2 (Isolation Forest)...")
        iso_forest = joblib.load(iso_path)
        # Use raw numeric columns (26 features) matching anomaly.py training
        X_val_numeric = val_df.select_dtypes("number").to_numpy()
        X_test_numeric = test_df.select_dtypes("number").to_numpy()
        iso_test_pr = _pr_auc(y_test, _iso_proba(-iso_forest.decision_function(X_test_numeric)))
        iso_val_pr = _pr_auc(y_val, _iso_proba(-iso_forest.decision_function(X_val_numeric)))
        out.kv("Tier 2 val PR-AUC",  f"{iso_val_pr:.4f}")
        out.kv("Tier 2 test PR-AUC", f"{iso_test_pr:.4f}")
    else:
        out.warn("Tier 2 Isolation Forest not found -- skipping Tier 2 metrics")

    out.banner("Frozen operating threshold (chosen on val)")
    chosen_threshold = _pick_f1_threshold(y_val, val_proba_xgb)
    out.kv("Chosen threshold", f"{chosen_threshold:.2f}")
    test_pred = (test_proba_xgb >= chosen_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, test_pred).ravel()
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = f1_score(y_test, test_pred, zero_division=0)
    fpr = fp / max(fp + tn, 1)
    out.kv("Precision", f"{precision:.4f}")
    out.kv("Recall",    f"{recall:.4f}")
    out.kv("F1",        f"{f1:.4f}")
    out.kv("False Positive Rate", f"{fpr:.6f}")
    out.kv("Confusion Matrix",    f"TP={tp} FP={fp} TN={tn} FN={fn}")

    out.banner("Business threshold table")
    out.table(
        ["threshold", "precision", "recall", "f1", "FP", "FN", ""],
        _business_table(test_proba_xgb, y_test, chosen_threshold),
        aligns=["r", "r", "r", "r", "r", "r", "l"],
    )

    out.banner("Per-fraud-type test PR-AUC")
    rows = []
    for ft in sorted(test_df["fraud_type"].dropna().unique()):
        if ft == "normal":
            continue
        n_cases = int((test_df.fraud_type == ft).sum())
        mask = test_df["fraud_type"].isin(["normal", ft]).to_numpy()
        ap = _pr_auc(test_df.loc[mask, "is_fraud"], test_proba_xgb[mask])
        flag = "  (low sample)" if n_cases < 10 else ""
        rows.append([ft, n_cases, f"{ap:.4f}", flag])
    out.table(["fraud_type", "count", "PR-AUC", ""], rows, aligns=["l", "r", "r", "l"])

    scored = test_df[["case_id", "is_fraud", "fraud_type"]].copy()
    scored["pred"] = test_pred
    fraud_cases = scored.loc[scored["is_fraud"] == 1].dropna(subset=["case_id"])
    if len(fraud_cases):
        case_detected = fraud_cases.groupby("case_id")["pred"].max()
        case_recall = float(case_detected.mean())
        out.kv("Case-level recall",
               f"{case_recall:.4f} ({int(case_detected.sum())}/{len(case_detected)} campaigns detected)")

    missed = test_df[(y_test == 1) & (test_pred == 0)]
    out.banner("False negatives")
    out.kv("Total FN", len(missed))
    if len(missed):
        out.step("  by fraud_type:")
        for ft, n in missed["fraud_type"].value_counts().items():
            out.step(f"    {ft:<22s} {n}")

    out.banner("Split class counts (val / test)")
    out.step("  val:")
    for ft, n in val_df["fraud_type"].value_counts().items():
        out.step(f"    {ft:<22s} {n}")
    out.step("  test:")
    for ft, n in test_df["fraud_type"].value_counts().items():
        out.step(f"    {ft:<22s} {n}")


if __name__ == "__main__":
    main()
