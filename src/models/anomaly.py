"""
Tier 2 — Isolation Forest v2 (unsupervised anomaly detection).

CHANGE LOG vs anomaly.py
-------------------------
Diagnosis of "inadequate anomaly scores" turned up four separate issues,
recorded here so the reasoning is auditable rather than just the fix:

1. CONTAMINATION WAS NEVER THE LEVER TO TUNE.
   sklearn's IsolationForest.decision_function(X) = score_samples(X) - offset_,
   and `contamination` only sets `offset_` (a constant shift used by `.predict()`
   to pick a binary cutoff). It does not change tree structure or the relative
   ranking of scores. Every ranking-based metric this project cares about
   (PR-AUC, the threshold table) is invariant to a constant shift, so cross-
   validating `contamination` for "detection quality" would produce the
   identical PR-AUC at every value tried -- it solves the wrong problem.
   What actually changes ranking quality is the ensemble's structural
   hyperparameters (n_estimators, max_samples, max_features) and the feature
   space it sees. Those are what get grid-searched below. `contamination`
   is now treated purely as a business operating-point choice, exactly like
   the XGBoost threshold table in evaluate.py -- reported as a table, not
   optimized as if it were a quality metric.

2. FEATURE SCALING MISMATCH.
   IsolationForest picks split points uniformly at random within each
   feature's observed [min, max] range. Raw `amount` (up to thousands),
   `geo_velocity_kmh` (occasional four-figure spikes), and 0/1 one-hot
   dummies all sit in the same matrix with wildly different ranges. Heavy-
   tailed columns need many splits to isolate the dense mass near zero from
   rare extreme values, diluting the isolation efficiency of every other
   feature sharing the same tree. A RobustScaler (median/IQR, fit on
   TRAIN-NORMAL ONLY, never on val/test) is bundled into the model as a
   Pipeline so the artifact stays self-contained.

3. THRESHOLD CALIBRATION WAS A SINGLE F1-OPTIMAL POINT.
   Same anti-pattern the hackathon build guide calls out for the supervised
   model: "the default 0.5 threshold is arbitrary... build a small threshold
   table instead of reporting one number." Isolation Forest gets that same
   treatment here now, plus the frozen point is still reported for anyone
   who wants a single number.

4. NO INTEGRATION HOOK FOR THE FEEDBACK LOOP.
   Anomaly scores previously lived only in this script's stdout. This
   version writes a ranked CSV of flagged transactions (highest anomaly
   score first, with XGBoost agreement/disagreement where available) so a
   human-review / retraining feedback loop has something concrete to
   consume. This is groundwork for Checkpoint 4, not the full closed loop.

Deliberately NOT using k-fold cross-validation for hyperparameter search:
this project's discipline is a temporal train/val/test split everywhere
(Phase 6 of the build guide) specifically to avoid future information
leaking into past predictions. Shuffled k-fold CV would violate that on a
fraud timeline, so hyperparameters are selected on the existing temporal
train/val split, with test held out and touched exactly once at the end.

Hygiene: dropped the unused `import os` carried over from anomaly.py.
"""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score

ARTIFACT_PATH = Path("models_artifacts/isolation_forest_tier2.joblib")
CONFIG_PATH = Path("models_artifacts/isolation_forest_tier2_config.json")
THRESHOLD_TABLE_PATH = Path("models_artifacts/isolation_forest_threshold_table.csv")
FEEDBACK_QUEUE_PATH = Path("data/processed/isolation_forest_feedback_queue.csv")
XGB_MODEL_PATH = Path("models_artifacts/xgboost_tier1.json")

# Structural hyperparameters actually move score ranking; grid kept small
# enough to run in seconds on a hackathon laptop.
PARAM_GRID = [
    {"n_estimators": n, "max_samples": ms, "max_features": mf}
    for n in (150, 300)
    for ms in (0.5, 0.8, 1.0)
    for mf in (0.8, 1.0)
]

# Fixed during the structural search since it cannot move PR-AUC (see
# docstring point 1); calibrated separately afterwards as an operating point.
SEARCH_CONTAMINATION = 0.01


def _build_pipeline(params, contamination):
    return Pipeline([
        ("scaler", RobustScaler()),
        ("iforest", IsolationForest(
            n_estimators=params["n_estimators"],
            max_samples=params["max_samples"],
            max_features=params["max_features"],
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )),
    ])


def _anomaly_score(pipeline, X):
    # decision_function: high = normal, low = anomalous. Flip sign so higher
    # score means "more anomalous", matching the XGBoost fraud_probability
    # convention used everywhere else in this project.
    return -pipeline.decision_function(X)


def _robust_normalize(scores, lo_hi=None, lo_pct=1.0, hi_pct=99.0):
    """
    Percentile-clipped min-max instead of true min/max, so a single extreme
    outlier can't compress the rest of the distribution into a sliver near 0.
    `lo_hi`, when provided, is reused as-is (fit on validation, applied to
    test) so the same [0, 1] mapping is applied to both -- never fit on test.
    """
    if lo_hi is None:
        lo, hi = np.percentile(scores, [lo_pct, hi_pct])
        if hi - lo < 1e-9:
            hi = lo + 1e-9
        lo_hi = (float(lo), float(hi))
    lo, hi = lo_hi
    return np.clip((scores - lo) / (hi - lo), 0.0, 1.0), lo_hi


def train_isolation_forest():
    print("=" * 70)
    print("TIER 2: ISOLATION FOREST v2 (UNSUPERVISED ANOMALY DETECTION)")
    print("=" * 70)

    X_train = pd.read_pickle("data/processed/X_train.pkl")
    X_val = pd.read_pickle("data/processed/X_val.pkl")
    X_test = pd.read_pickle("data/processed/X_test.pkl")
    train_df = pd.read_pickle("data/processed/train_df.pkl")
    val_df = pd.read_pickle("data/processed/val_df.pkl")
    test_df = pd.read_pickle("data/processed/test_df.pkl")

    # Feature-alignment integration check (explicitly requested): the
    # generator/feature-engineering contract promises the same column set at
    # every stage. Fail loudly here rather than silently misaligning features
    # the way an unguarded schema drift would.
    if list(X_val.columns) != list(X_train.columns) or list(X_test.columns) != list(X_train.columns):
        raise ValueError(
            "Feature schema mismatch between train/val/test matrices -- "
            "check that val/test were encoded with X_train.columns as the "
            "reference (see train.py's reindex step)."
        )

    y_train = train_df["is_fraud"].to_numpy()
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    normal_mask = (y_train == 0)
    X_train_normal = X_train[normal_mask]
    print(f"Training on {len(X_train_normal):,} strictly legitimate baseline transactions...")

    # ---- structural hyperparameter search on the temporal val split ----
    best_val_pr, best_params = -1.0, None
    print(f"\nSearching {len(PARAM_GRID)} structural configurations "
          f"(contamination held fixed at {SEARCH_CONTAMINATION} -- see module docstring)...")
    for params in PARAM_GRID:
        pipe = _build_pipeline(params, SEARCH_CONTAMINATION)
        pipe.fit(X_train_normal)
        val_scores = _anomaly_score(pipe, X_val)
        val_pr = average_precision_score(y_val, val_scores)
        print(f"  n_estimators={params['n_estimators']:>4} "
              f"max_samples={params['max_samples']:>4} "
              f"max_features={params['max_features']:>4}  -> val PR-AUC={val_pr:.4f}")
        if val_pr > best_val_pr:
            best_val_pr, best_params = val_pr, params

    print(f"\nBest structural config: {best_params}  (val PR-AUC={best_val_pr:.4f})")

    # ---- contamination is calibrated as an operating-point choice, not ----
    # ---- searched as if it were a quality lever (docstring point 1)    ----
    val_fraud_rate = float(y_val.mean())
    final_contamination = float(np.clip(val_fraud_rate, 0.001, 0.05))
    print(f"Calibrating contamination to observed val fraud rate: {final_contamination:.5f}")

    final_pipeline = _build_pipeline(best_params, final_contamination)
    final_pipeline.fit(X_train_normal)

    val_scores_raw = _anomaly_score(final_pipeline, X_val)
    test_scores_raw = _anomaly_score(final_pipeline, X_test)
    val_risk, norm_range = _robust_normalize(val_scores_raw)
    test_risk, _ = _robust_normalize(test_scores_raw, lo_hi=norm_range)

    val_pr_auc = average_precision_score(y_val, val_risk)
    test_pr_auc = average_precision_score(y_test, test_risk)

    print("\n[Unsupervised Benchmark]")
    print(f"Test Prevalence Baseline: {y_test.mean():.5f}")
    print(f"Validation PR-AUC:        {val_pr_auc:.4f}")
    print(f"Test PR-AUC:              {test_pr_auc:.4f}")

    # ---- threshold TABLE, not a single frozen number (Phase 9 pattern) ----
    print("\n--- Business Operating Thresholds (Isolation Forest) ---")
    threshold_rows = []
    candidate_thresholds = list(np.linspace(0.1, 0.9, 17))
    best_f1, frozen_thr = 0.0, 0.5
    for thr in candidate_thresholds:
        pred_v = (val_risk >= thr).astype(int)
        f1_v = f1_score(y_val, pred_v, zero_division=0)
        pred_t = (test_risk >= thr).astype(int)
        tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test, pred_t).ravel()
        p_t = tp_t / max(tp_t + fp_t, 1)
        r_t = tp_t / max(tp_t + fn_t, 1)
        f1_t = f1_score(y_test, pred_t, zero_division=0)
        threshold_rows.append({
            "threshold": round(float(thr), 3), "val_f1": round(float(f1_v), 4),
            "test_precision": round(float(p_t), 4), "test_recall": round(float(r_t), 4),
            "test_f1": round(float(f1_t), 4), "test_fp": int(fp_t), "test_fn": int(fn_t),
        })
        print(f"thr={thr:.2f} | val_F1={f1_v:.3f} | test_P={p_t:.3f} test_R={r_t:.3f} "
              f"test_F1={f1_t:.3f} FP={fp_t} FN={fn_t}")
        if f1_v > best_f1:
            best_f1, frozen_thr = f1_v, float(thr)

    Path("models_artifacts").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(threshold_rows).to_csv(THRESHOLD_TABLE_PATH, index=False)

    test_pred = (test_risk >= frozen_thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, test_pred).ravel()
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = f1_score(y_test, test_pred, zero_division=0)
    print(f"\nFrozen Threshold (Validation-Optimal F1): {frozen_thr:.2f}")
    print(f"Test Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | FP: {fp} | FN: {fn}")

    # ---- per-fraud-family PR-AUC, transaction count AND unique-case ----
    # ---- count reported separately (n_transactions vs n_unique_cases) ----
    print("\n--- Per-Fraud-Type Anomaly Detection PR-AUC ---")
    for ft in sorted(test_df["fraud_type"].dropna().unique()):
        if ft == "normal":
            continue
        mask = test_df["fraud_type"].isin(["normal", ft]).to_numpy()
        ap = average_precision_score(test_df.loc[mask, "is_fraud"], test_risk[mask])
        ft_rows = test_df[test_df.fraud_type == ft]
        n_tx = len(ft_rows)
        n_cases = ft_rows["case_id"].nunique() if "case_id" in ft_rows else n_tx
        print(f"{ft:22s} n_transactions={n_tx:4d}  n_unique_cases={n_cases:4d}  PR-AUC={ap:.4f}")

    # case-level recall, same aggregation pattern as evaluate.py's XGBoost table
    scored = test_df[["case_id", "is_fraud", "fraud_type"]].copy()
    scored["pred"] = test_pred
    fraud_cases = scored.loc[scored["is_fraud"] == 1].dropna(subset=["case_id"])
    if len(fraud_cases):
        case_detected = fraud_cases.groupby("case_id")["pred"].max()
        case_recall = float(case_detected.mean())
        print(f"\nAggregate Case-Level Recall (Isolation Forest): {case_recall:.4f} "
              f"({int(case_detected.sum())}/{len(case_detected)} attack campaigns detected)")

    # ---- feedback-loop integration hook (groundwork for Checkpoint 4) ----
    _export_feedback_queue(test_df, X_test, test_risk, test_pred)

    # ---- persist ----
    joblib.dump(final_pipeline, ARTIFACT_PATH)
    with open(CONFIG_PATH, "w") as f:
        json.dump({
            "best_structural_params": best_params,
            "final_contamination": final_contamination,
            "frozen_threshold": frozen_thr,
            "val_pr_auc": val_pr_auc,
            "test_pr_auc": test_pr_auc,
            "normalization_percentiles": [1.0, 99.0],
        }, f, indent=2)
    print(f"\nModel artifact saved to: {ARTIFACT_PATH}")
    print("  (still a Pipeline exposing .decision_function -- evaluate.py needs no changes)")
    print(f"Config saved to: {CONFIG_PATH}")
    print(f"Threshold table saved to: {THRESHOLD_TABLE_PATH}")
    return final_pipeline


def _export_feedback_queue(test_df, X_test, test_risk, test_pred, top_n=200):
    """
    Writes the highest-priority anomalies to a CSV a human-review /
    retraining feedback loop can consume directly. Where the XGBoost Tier 1
    model is available, flags disagreements (Isolation Forest says
    anomalous, XGBoost says normal) separately -- those are the interesting
    "the supervised model might be missing a pattern it was never shown"
    rows, which is the actual argument for having an unsupervised detector.
    """
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
    print(f"\nFeedback queue ({min(top_n, len(flagged))} of {len(flagged)} flagged "
          f"transactions) saved to: {FEEDBACK_QUEUE_PATH}")


if __name__ == "__main__":
    train_isolation_forest()