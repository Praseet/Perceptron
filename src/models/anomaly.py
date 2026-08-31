"""
Tier 2 - Isolation Forest (unsupervised anomaly detection).

CHANGE LOG
----------
1. CONTAMINATION WAS NEVER THE LEVER TO TUNE.
   decision_function returns score_samples - offset_, so `contamination`
   only sets the constant shift. Ranking metrics (PR-AUC) are invariant
   to a constant shift. Structural hyperparameters are what get searched.

2. FEATURE SCALING MISMATCH.
   Raw `amount` and 0/1 dummies in the same matrix dilute isolation
   efficiency. A RobustScaler (fit on train-normal only) is bundled
   into the model so the artifact stays self-contained.

3. THRESHOLD CALIBRATION WAS A SINGLE F1-OPTIMAL POINT.
   Default threshold is arbitrary. Isolation Forest gets a small
   threshold table, plus the frozen point for the headline number.

4. NO INTEGRATION HOOK FOR THE FEEDBACK LOOP.
   Anomaly scores previously lived only in stdout. Now writes a ranked
   CSV of flagged transactions for the feedback loop.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    X_TEST_PKL, TRAIN_DF_PKL, VAL_DF_PKL, TEST_DF_PKL,
    ISO_FOREST_TIER2_JOBLIB, ISO_FOREST_CONFIG_JSON,
    ISO_FOREST_THRESHOLDS_CSV, FEEDBACK_QUEUE_CSV,
    XGB_TIER1_JSON, MODELS_ARTIFACTS, DATA_PROCESSED,
    IF_PARAM_GRID, IF_FIXED_PARAMS, IF_N_SPLITS, IF_FEATURE_COLS,
    IF_CONTAMINATION_CANDIDATES, IF_NORMAL_PERCENTILES,
    IF_FEEDBACK_QUEUE_TOP_N,
)
from models import output as out

ARTIFACT_PATH = Path(ISO_FOREST_TIER2_JOBLIB)
CONFIG_PATH = Path(ISO_FOREST_CONFIG_JSON)
THRESHOLD_TABLE_PATH = Path(ISO_FOREST_THRESHOLDS_CSV)
XGB_MODEL_PATH = Path(XGB_TIER1_JSON)
FEEDBACK_QUEUE_PATH = Path(FEEDBACK_QUEUE_CSV)


def _contract_matrix(df):
    """P0.1 — explicit IF feature contract: reindex to IF_FEATURE_COLS only
    (the 20 numeric behavioral features, no IDs / timestamps / labels). The
    saved artifact was trained on exactly this column order; select_dtypes()
    would silently feed user_id and is_fraud into the anomaly matrix.
    """
    return (
        df.reindex(columns=IF_FEATURE_COLS, fill_value=0)
        .astype(float)
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )


def _grid_search(train_df, val_df):
    """Grid-search structural hyperparameters on the val PR-AUC."""
    train_rows = train_df[train_df["is_fraud"] == 0]
    X_train = _contract_matrix(train_rows).to_numpy()
    y_val = val_df["is_fraud"].to_numpy()
    X_val = _contract_matrix(val_df).to_numpy()

    best_params, best_score = None, -1.0
    all_results = []
    for n_est in IF_PARAM_GRID["n_estimators"]:
        for max_s in IF_PARAM_GRID["max_samples"]:
            for max_f in IF_PARAM_GRID["max_features"]:
                model = Pipeline([
                    ("scaler", RobustScaler()),
                    ("iforest", IsolationForest(
                        n_estimators=n_est, max_samples=max_s,
                        max_features=max_f, **IF_FIXED_PARAMS)),
                ])
                model.fit(X_train)
                val_scores = -model.decision_function(X_val)
                ap = float(average_precision_score(y_val, val_scores))
                all_results.append({
                    "n_estimators": n_est, "max_samples": max_s,
                    "max_features": max_f, "val_pr_auc": ap,
                })
                if ap > best_score:
                    best_score, best_params = ap, {
                        "n_estimators": n_est,
                        "max_samples": max_s,
                        "max_features": max_f,
                    }
    return best_params, best_score, all_results


def _refit_and_freeze_threshold(train_df, val_df, best_params):
    """Refit on train-normal, freeze threshold on val."""
    train_rows = train_df[train_df["is_fraud"] == 0]
    X_train = _contract_matrix(train_rows).to_numpy()
    X_val = _contract_matrix(val_df).to_numpy()
    y_val = val_df["is_fraud"].to_numpy()

    final_pipeline = Pipeline([
        ("scaler", RobustScaler()),
        ("iforest", IsolationForest(**best_params, **IF_FIXED_PARAMS)),
    ])
    final_pipeline.fit(X_train)

    val_scores = -final_pipeline.decision_function(X_val)
    low_p, high_p = IF_NORMAL_PERCENTILES
    low = np.percentile(val_scores, low_p)
    high = np.percentile(val_scores, high_p)
    candidates = [c for c in IF_CONTAMINATION_CANDIDATES if low <= c * 100 <= high]
    candidates = candidates or [0.005]
    best_f1, frozen_thr = -1.0, float(candidates[0])
    for c in candidates:
        thr = float(np.percentile(val_scores, 100 * (1 - c)))
        pred = (val_scores >= thr).astype(int)
        f1 = f1_score(y_val, pred, zero_division=0)
        if f1 > best_f1:
            best_f1, frozen_thr = f1, thr
    return final_pipeline, frozen_thr, val_scores, y_val


def _build_threshold_table(test_scores, y_test, frozen_thr):
    """Build a contamination-style threshold table for business review."""
    rows = []
    for c in IF_CONTAMINATION_CANDIDATES:
        thr = float(np.percentile(test_scores, 100 * (1 - c)))
        pred = (test_scores >= thr).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_test, pred).ravel()
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = f1_score(y_test, pred, zero_division=0)
        marker = "  <- frozen" if abs(thr - frozen_thr) < 1e-6 else ""
        rows.append({
            "contamination": c, "threshold": thr,
            "precision": precision, "recall": recall, "f1": f1,
            "fp": int(fp), "fn": int(fn), "note": marker,
        })
    return pd.DataFrame(rows)


def _export_feedback_queue(test_df, X_test, test_risk, test_pred, top_n=IF_FEEDBACK_QUEUE_TOP_N):
    """Write a ranked CSV of flagged transactions for human review."""
    queue = test_df.copy().reset_index(drop=True)
    queue["anomaly_score"] = test_risk
    queue["anomaly_flag"] = test_pred

    if XGB_MODEL_PATH.exists():
        import xgboost as xgb
        xgb_model = xgb.XGBClassifier()
        xgb_model.load_model(str(XGB_MODEL_PATH))
        xgb_proba = xgb_model.predict_proba(X_test)[:, 1]
        queue["xgb_fraud_probability"] = xgb_proba
        queue["xgb_iforest_disagreement"] = (
            (queue["anomaly_flag"] == 1) & (xgb_proba < 0.5)
        ).astype(int)
        sort_cols = ["xgb_iforest_disagreement", "anomaly_score"]
    else:
        sort_cols = ["anomaly_score"]

    flagged = queue[queue["anomaly_flag"] == 1].sort_values(sort_cols, ascending=False)
    cols = [c for c in [
        "case_id", "transaction_id", "user_id", "timestamp", "fraud_type", "is_fraud",
        "amount", "anomaly_score", "anomaly_flag",
        "xgb_fraud_probability", "xgb_iforest_disagreement",
    ] if c in flagged.columns]

    FEEDBACK_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    flagged[cols].head(top_n).to_csv(FEEDBACK_QUEUE_PATH, index=False)
    out.kv("Feedback queue",
           f"{min(top_n, len(flagged))} of {len(flagged)} flagged rows -> "
           f"{FEEDBACK_QUEUE_PATH.name}")


def train_isolation_forest():
    out.banner("Tier 2: Isolation Forest")

    train_df = pd.read_pickle(TRAIN_DF_PKL)
    val_df = pd.read_pickle(VAL_DF_PKL)
    test_df = pd.read_pickle(TEST_DF_PKL)
    X_test = pd.read_pickle(X_TEST_PKL)

    out.kv("Train (normal only)", f"{int((train_df['is_fraud']==0).sum()):,}")
    out.kv("Val rows", f"{len(val_df):,}")
    out.kv("Test rows", f"{len(test_df):,}")

    out.banner("Grid search (structural hyperparams, val PR-AUC)")
    best_params, best_val_pr, all_results = _grid_search(train_df, val_df)
    out.kv("Best val PR-AUC", f"{best_val_pr:.4f}")
    out.kv("Best params", str(best_params))
    out.step(f"  {len(all_results)} configurations evaluated")

    out.banner("Refit on full train-normal, freeze threshold on val")
    final_pipeline, frozen_thr, val_scores, y_val = _refit_and_freeze_threshold(
        train_df, val_df, best_params
    )
    out.kv("Frozen threshold", f"{frozen_thr:.4f}")

    out.banner("Test evaluation")
    test_risk = -final_pipeline.decision_function(_contract_matrix(test_df).to_numpy())
    y_test = test_df["is_fraud"].to_numpy()
    test_pred = (test_risk >= frozen_thr).astype(int)
    test_pr_auc = float(average_precision_score(y_test, test_risk))
    out.kv("Test PR-AUC", f"{test_pr_auc:.4f}")

    out.step("Per-fraud-type test PR-AUC:")
    rows = []
    for ft in sorted(test_df["fraud_type"].dropna().unique()):
        if ft == "normal":
            continue
        ft_rows = test_df[test_df["fraud_type"] == ft]
        n_tx = len(ft_rows)
        n_cases = ft_rows["case_id"].nunique() if "case_id" in ft_rows else n_tx
        mask = test_df["fraud_type"].isin(["normal", ft]).to_numpy()
        ap = float(average_precision_score(test_df.loc[mask, "is_fraud"], test_risk[mask]))
        rows.append([ft, n_tx, n_cases, f"{ap:.4f}"])
    out.table(["fraud_type", "n_tx", "n_cases", "PR-AUC"], rows,
              aligns=["l", "r", "r", "r"])

    scored = test_df[["case_id", "is_fraud", "fraud_type"]].copy()
    scored["pred"] = test_pred
    fraud_cases = scored.loc[scored["is_fraud"] == 1].dropna(subset=["case_id"])
    if len(fraud_cases):
        case_detected = fraud_cases.groupby("case_id")["pred"].max()
        case_recall = float(case_detected.mean())
        out.kv("Case-level recall",
               f"{case_recall:.4f} "
               f"({int(case_detected.sum())}/{len(case_detected)} campaigns)")

    out.banner("Test threshold table")
    table_df = _build_threshold_table(test_risk, y_test, frozen_thr)
    out.table(
        ["contam.", "threshold", "precision", "recall", "f1", "FP", "FN", ""],
        [[f"{r.contamination:.4f}", f"{r.threshold:.4f}",
          f"{r.precision:.3f}", f"{r.recall:.3f}", f"{r.f1:.3f}",
          int(r.fp), int(r.fn), r.note]
         for r in table_df.itertuples()],
        aligns=["r", "r", "r", "r", "r", "r", "r", "l"],
    )

    _export_feedback_queue(test_df, X_test, test_risk, test_pred)

    out.banner("Saving artifacts")
    joblib.dump(final_pipeline, ARTIFACT_PATH)
    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "best_structural_params": best_params,
            "final_contamination": float((test_risk >= frozen_thr).mean()),
            "frozen_threshold": frozen_thr,
            "val_pr_auc": best_val_pr,
            "test_pr_auc": test_pr_auc,
            "normalization_percentiles": list(IF_NORMAL_PERCENTILES),
        }, f, indent=2)
    Path(DATA_PROCESSED).mkdir(parents=True, exist_ok=True)
    table_df.to_csv(THRESHOLD_TABLE_PATH, index=False)
    out.kv("Model artifact", ARTIFACT_PATH.name)
    out.kv("Config",         CONFIG_PATH.name)
    out.kv("Threshold table", THRESHOLD_TABLE_PATH.name)
    return final_pipeline


if __name__ == "__main__":
    train_isolation_forest()

