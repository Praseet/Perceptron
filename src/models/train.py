from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import xgboost as xgb

# Import centralized configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    TRANSACTIONS_FEATURES_PKL, TRAIN_DF_PKL, VAL_DF_PKL, TEST_DF_PKL,
    X_TRAIN_PKL, X_VAL_PKL, X_TEST_PKL, XGB_TIER1_JSON,
    FEATURE_COLS, CAT_COLS, MODEL_COLS, XGB_PARAMS,
    TRAIN_QUANTILE, VAL_QUANTILE, ensure_directories
)

def train_model(generate_only=False):
    """Train the XGBoost Tier 1 model."""
    ensure_directories()
    
    if generate_only:
        # Just generate the train/val/test splits and feature matrices, don't train
        print("--generate-only mode: generating splits and features without training")
    
    df = pd.read_pickle(TRANSACTIONS_FEATURES_PKL)
    order = np.argsort(df["timestamp"].to_numpy())
    df = df.iloc[order].reset_index(drop=True)
    ts = df["timestamp"].astype("int64").to_numpy()
    cut1 = np.quantile(ts, TRAIN_QUANTILE)
    cut2 = np.quantile(ts, VAL_QUANTILE)
    train_df = df[ts <= cut1].copy()
    val_df = df[(ts > cut1) & (ts <= cut2)].copy()
    test_df = df[ts > cut2].copy()

    X_train_raw = train_df[MODEL_COLS].copy()
    X_val_raw = val_df[MODEL_COLS].copy()
    X_test_raw = test_df[MODEL_COLS].copy()
    y_train = train_df["is_fraud"].to_numpy()
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    train_medians = X_train_raw[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).median()
    for frame in (X_train_raw, X_val_raw, X_test_raw):
        frame[FEATURE_COLS] = frame[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).fillna(train_medians)

    X_train = pd.get_dummies(X_train_raw, columns=CAT_COLS).fillna(-1)
    X_val = pd.get_dummies(X_val_raw, columns=CAT_COLS).reindex(columns=X_train.columns, fill_value=0).fillna(-1)
    X_test = pd.get_dummies(X_test_raw, columns=CAT_COLS).reindex(columns=X_train.columns, fill_value=0).fillna(-1)

    if not generate_only:
        scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

        model = xgb.XGBClassifier(
            **XGB_PARAMS,
            scale_pos_weight=float(scale_pos_weight),
        )
        model.fit(X_train, y_train)

        model.save_model(XGB_TIER1_JSON)

    X_train.to_pickle(X_TRAIN_PKL); X_val.to_pickle(X_VAL_PKL); X_test.to_pickle(X_TEST_PKL)
    train_df.to_pickle(TRAIN_DF_PKL); val_df.to_pickle(VAL_DF_PKL); test_df.to_pickle(TEST_DF_PKL)

    train_rows, val_rows, test_rows = len(train_df), len(val_df), len(test_df)
    train_rate = train_df["is_fraud"].mean()
    val_rate = val_df["is_fraud"].mean()
    test_rate = test_df["is_fraud"].mean()
    train_impersonation = (train_df.fraud_type == "ai_impersonation").sum()
    val_impersonation = (val_df.fraud_type == "ai_impersonation").sum()
    test_impersonation = (test_df.fraud_type == "ai_impersonation").sum()

    print("Training summary")
    print(f"- Split: train={train_rows:,}, val={val_rows:,}, test={test_rows:,}")
    print(f"- Fraud rate: train={train_rate:.4%}, val={val_rate:.4%}, test={test_rate:.4%}")
    print(f"- AI impersonation cases: train={train_impersonation}, val={val_impersonation}, test={test_impersonation}")
    if not generate_only:
        scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
        print(f"- scale_pos_weight: {scale_pos_weight:.4f}")
        print(f"- Saved model: {XGB_TIER1_JSON}")
    print(f"- Saved feature matrices: {X_TRAIN_PKL}, {X_VAL_PKL}, {X_TEST_PKL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost Tier 1 fraud model")
    parser.add_argument("--generate-only", action="store_true", 
                        help="Generate train/val/test splits and feature matrices without training model")
    args = parser.parse_args()
    train_model(generate_only=args.generate_only)
