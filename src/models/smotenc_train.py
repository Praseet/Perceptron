"""
Tier 2 -- trains a NEW XGBoost model on SMOTENC-augmented data and evaluates
it head-to-head against the FROZEN Tier 1 baseline (and the CTGAN-augmented
model where that artifact exists) on the SAME real, untouched val/test sets.
Never overwrites models_artifacts/xgboost_tier1.json.

DEVIATION (flagged per project convention): feature-engineering steps are
duplicated from train.py rather than imported, so this script has no runtime
dependency on the frozen baseline's build script.

scale_pos_weight is RECOMPUTED from the augmented class counts instead of
reusing the frozen baseline's value: resampling and loss-reweighting push
the same lever (minority-class gradient signal), so turning both up at full
strength double-compensates. Letting the weight fall as synthetic rows are
added keeps the total correction bounded.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score

SEED = 42
FEATURE_COLS = ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                "count_30d", "amount_zscore_30d", "new_device", "new_merchant",
                "merchant_cat_freq_user", "time_since_last_s", "dist_from_prev_km",
                "geo_velocity_kmh", "hour_of_day", "three_ds_failures_before_result"]
CAT_COLS = ["merchant_category", "channel", "three_ds_result"]
MODEL_COLS = FEATURE_COLS + CAT_COLS


def build_features(train_df, val_df, test_df):
    X_train_raw = train_df[MODEL_COLS].copy()
    X_val_raw = val_df[MODEL_COLS].copy()
    X_test_raw = test_df[MODEL_COLS].copy()

    train_medians = X_train_raw[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).median()
    for frame in (X_train_raw, X_val_raw, X_test_raw):
        frame[FEATURE_COLS] = frame[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).fillna(train_medians)

    X_train = pd.get_dummies(X_train_raw, columns=CAT_COLS).fillna(-1)
    X_val = pd.get_dummies(X_val_raw, columns=CAT_COLS).reindex(columns=X_train.columns, fill_value=0).fillna(-1)
    X_test = pd.get_dummies(X_test_raw, columns=CAT_COLS).reindex(columns=X_train.columns, fill_value=0).fillna(-1)
    return X_train, X_val, X_test


def evaluate_model(model, X_val, X_test, y_val, y_test, test_df, label):
    val_proba = model.predict_proba(X_val)[:, 1]
    test_proba = model.predict_proba(X_test)[:, 1]

    candidate_thresholds = np.linspace(0.01, 0.99, 99)
    _, chosen_threshold = max(
        (f1_score(y_val, (val_proba >= t).astype(int), zero_division=0), float(t))
        for t in candidate_thresholds
    )
    test_pred = (test_proba >= chosen_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, test_pred).ravel()
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = f1_score(y_test, test_pred, zero_division=0)
    test_pr_auc = average_precision_score(y_test, test_proba)

    print(f"\n--- {label} @ frozen threshold {chosen_threshold:.2f} ---")
    print(f"Test PR-AUC: {test_pr_auc:.4f} | Precision: {precision:.4f} | Recall: {recall:.4f} | "
          f"F1: {f1:.4f} | FP: {fp} | FN: {fn}")

    print(f"\n{label} -- per-fraud-type PR-AUC:")
    for ft in sorted(test_df["fraud_type"].dropna().unique()):
        if ft == "normal":
            continue
        n_cases = (test_df.fraud_type == ft).sum()
        mask = test_df["fraud_type"].isin(["normal", ft]).to_numpy()
        ap = average_precision_score(test_df.loc[mask, "is_fraud"], test_proba[mask])
        flag = "  <-- LOW SAMPLE" if n_cases < 10 else ""
        print(f"  {ft:22s} count={n_cases:4d} | PR-AUC={ap:.4f}{flag}")

    return {"pr_auc": test_pr_auc, "precision": precision, "recall": recall,
            "f1": f1, "fn": int(fn),
            "imp_pr_auc": _per_type_pr_auc(test_df, test_proba, "ai_impersonation"),
            "abp_pr_auc": _per_type_pr_auc(test_df, test_proba, "auth_bypass")}


def _per_type_pr_auc(test_df, test_proba, fraud_type):
    mask = test_df["fraud_type"].isin(["normal", fraud_type]).to_numpy()
    return float(average_precision_score(test_df.loc[mask, "is_fraud"], test_proba[mask]))


if __name__ == "__main__":
    print("=" * 80)
    print("TIER 2: XGBOOST ON SMOTENC-AUGMENTED DATA vs FROZEN TIER 1 BASELINE")
    print("=" * 80)

    # Real, untouched val/test -- identical to what the frozen baseline was scored on.
    val_df = pd.read_pickle("data/processed/val_df.pkl")
    test_df = pd.read_pickle("data/processed/test_df.pkl")
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    # --- Baseline: reload the FROZEN model, do not retrain it ---
    baseline_model = xgb.XGBClassifier()
    baseline_model.load_model("models_artifacts/xgboost_tier1.json")
    _, X_val_baseline, X_test_baseline = build_features(
        pd.read_pickle("data/processed/train_df.pkl"), val_df, test_df
    )

    # --- New model: same hyperparameters, trained on SMOTENC-augmented train ---
    train_df_smotenc = pd.read_pickle("data/processed/train_df_smotenc.pkl")
    X_train_smc, X_val_smc, X_test_smc = build_features(train_df_smotenc, val_df, test_df)
    y_train_smc = train_df_smotenc["is_fraud"].to_numpy()

    scale_pos_weight = (y_train_smc == 0).sum() / max((y_train_smc == 1).sum(), 1)
    print(f"\nSMOTENC-augmented train: {len(train_df_smotenc):,} rows, "
          f"scale_pos_weight={scale_pos_weight:.2f} "
          f"(recomputed post-resampling; frozen baseline was 199.26)")

    new_model = xgb.XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.08,
        scale_pos_weight=float(scale_pos_weight), eval_metric="aucpr",
        subsample=0.8, colsample_bytree=0.8, random_state=SEED, tree_method="hist",
    )
    new_model.fit(X_train_smc, y_train_smc)

    Path("models_artifacts").mkdir(parents=True, exist_ok=True)
    new_model.save_model("models_artifacts/xgboost_tier1_smotenc.json")  # NEW path

    baseline_metrics = evaluate_model(baseline_model, X_val_baseline, X_test_baseline,
                                      y_val, y_test, test_df,
                                      "FROZEN BASELINE (real data only)")
    smotenc_metrics = evaluate_model(new_model, X_val_smc, X_test_smc,
                                     y_val, y_test, test_df,
                                     "SMOTENC-AUGMENTED MODEL")

    # --- CTGAN model, if its artifacts exist -- the head-to-head third column ---
    # Both the trained artifact AND its augmented pickle must be present;
    # the pickle can legitimately be cleaned up separately since the CTGAN
    # experiment is closed (see CHANGELOG).
    ctgan_model_path = Path("models_artifacts/xgboost_tier1_ctgan_augmented.json")
    ctgan_pickle_path = Path("data/processed/train_df_ctgan.pkl")
    ctgan_metrics = None
    if ctgan_model_path.exists() and ctgan_pickle_path.exists():
        ctgan_model = xgb.XGBClassifier()
        ctgan_model.load_model(str(ctgan_model_path))
        train_df_ctgan = pd.read_pickle(str(ctgan_pickle_path))
        X_train_ct, X_val_ct, X_test_ct = build_features(train_df_ctgan, val_df, test_df)
        ctgan_metrics = evaluate_model(ctgan_model, X_val_ct, X_test_ct,
                                       y_val, y_test, test_df,
                                       "CTGAN-AUGMENTED MODEL (for reference)")
    elif ctgan_model_path.exists():
        print("\nCTGAN model artifact found but train_df_ctgan.pkl is missing "
              "-- skipping the CTGAN comparison column.")

    rows = [("FROZEN BASELINE", baseline_metrics), ("SMOTENC-AUG", smotenc_metrics)]
    if ctgan_metrics is not None:
        rows.append(("CTGAN-AUG", ctgan_metrics))

    print("\n" + "=" * 80)
    print("HEAD-TO-HEAD SUMMARY")
    print("=" * 80)
    header = f"{'Metric':<16}" + "".join(f"{name:>18}" for name, _ in rows)
    print(header)
    for key in ("pr_auc", "precision", "recall", "f1", "imp_pr_auc", "abp_pr_auc"):
        line = f"{key:<16}" + "".join(f"{m[key]:>18.4f}" for _, m in rows)
        print(line)
    print(f"{'fn (count)':<16}" + "".join(f"{m['fn']:>18d}" for _, m in rows))
    delta = smotenc_metrics["pr_auc"] - baseline_metrics["pr_auc"]
    print(f"\nSMOTENC vs baseline overall PR-AUC delta: {delta:+.4f}")
    print("\nSaved new model to: models_artifacts/xgboost_tier1_smotenc.json")
    print("Frozen baseline (models_artifacts/xgboost_tier1.json) was not modified.")
