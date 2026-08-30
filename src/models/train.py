"""Tier 1 baseline trainer: temporal split + XGBoost."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    FEATURE_COLS, CAT_COLS, MODEL_COLS, XGB_PARAMS, XGB_DEVICE,
    TRAIN_QUANTILE, VAL_QUANTILE,
    TRANSACTIONS_FEATURES_PKL,
    TRAIN_DF_PKL, VAL_DF_PKL, TEST_DF_PKL,
    X_TRAIN_PKL, X_VAL_PKL, X_TEST_PKL,
    XGB_TIER1_JSON, ensure_directories,
)
from models import output as out


def _replace_with_retry(tmp, path, attempts: int = 6) -> None:
    """Swap tmp into place with retries.

    Windows transiently locks a file right after a large overwrite (AV scanner
    / indexer), which surfaces as Errno 22 / Access-denied on the destination.
    Callers write to a sibling .tmp first, then swap; corrupted artifacts are
    impossible even if the process dies mid-write.
    """
    import os as _os, time as _time
    last_err = None
    for _ in range(attempts):
        try:
            _os.replace(tmp, path)
            last_err = None
            break
        except (PermissionError, OSError) as e:
            last_err = e
            _time.sleep(1.5)
            try:
                Path(path).unlink()
            except (FileNotFoundError, PermissionError):
                pass
    if last_err is not None:
        raise last_err


def _atomic_pickle(obj, path) -> None:
    """to_pickle with temp-file + replace and retries (see _replace_with_retry)."""
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    obj.to_pickle(tmp)
    _replace_with_retry(tmp, path)


def train_model(generate_only: bool = False) -> None:
    """Split the data temporally and (optionally) train the XGBoost baseline.

    If `generate_only` is True, only the split pickles and feature matrices
    are written; the model is left as-is. This is useful when the caller
    wants to inspect features before committing to a training run.
    """
    ensure_directories()

    if generate_only:
        out.banner("train: --generate-only (no model fit)")

    df = pd.read_pickle(TRANSACTIONS_FEATURES_PKL)
    order = np.argsort(df["timestamp"].to_numpy())
    df = df.iloc[order].reset_index(drop=True)
    ts = df["timestamp"].astype("int64").to_numpy()
    cut1 = np.quantile(ts, TRAIN_QUANTILE)
    cut2 = np.quantile(ts, VAL_QUANTILE)

    # CASE-AWARE SPLIT (audit fix, ml-pipeline-audit-agent-prompt.md Objective 1)
    # Fraud cases are multi-transaction campaigns (bustout ~20 tx, synthetic
    # identity ~20 tx, bnpl_abuse ~12 tx). The previous row-level temporal
    # split fragmented these across train/val/test, so the model could learn
    # a campaign's pattern in train and trivially identify the same campaign
    # in test/val -- case-level leakage, exactly the failure mode the brief
    # warns against. We now assign each case (by case_id) to ONE split, using
    # the case's median timestamp. Rows with no case_id (normal tx, lone
    # fraud rows) keep the row-level temporal split, so the 70/10/20 ratio
    # is preserved for the majority normal population.
    fraud_mask = df["is_fraud"] == 1
    fraud_with_case = fraud_mask & df["case_id"].notna()

    case_assignment = pd.Series(index=df.index, dtype=object)
    if fraud_with_case.any():
        fraud_idx = df.index[fraud_with_case]
        case_ids = df.loc[fraud_idx, "case_id"].to_numpy()
        case_ts = ts[fraud_idx]
        case_med = pd.Series(case_ts, index=case_ids).groupby(level=0).median()
        assigned = np.where(case_med.to_numpy() <= cut1, "train",
                   np.where(case_med.to_numpy() <= cut2, "val", "test"))
        case_to_split = dict(zip(case_med.index.tolist(), assigned.tolist()))
        for idx, cid in zip(fraud_idx, case_ids):
            case_assignment.loc[idx] = case_to_split[cid]

    # Rows that are NOT case-assigned (normal tx + lone fraud rows): fall back
    # to row-level temporal split.
    fallback_mask = case_assignment.isna()
    case_assignment.loc[fallback_mask] = np.where(ts[fallback_mask.to_numpy()] <= cut1, "train",
                                          np.where(ts[fallback_mask.to_numpy()] <= cut2, "val", "test"))

    train_df = df[case_assignment == "train"].copy()
    val_df = df[case_assignment == "val"].copy()
    test_df = df[case_assignment == "test"].copy()

    out.banner("Split summary")
    out.kv("Train", f"{len(train_df):,} rows")
    out.kv("Val",   f"{len(val_df):,} rows")
    out.kv("Test",  f"{len(test_df):,} rows")
    out.kv("Train fraud rate", f"{train_df['is_fraud'].mean():.4%}")
    out.kv("Val fraud rate",   f"{val_df['is_fraud'].mean():.4%}")
    out.kv("Test fraud rate",  f"{test_df['is_fraud'].mean():.4%}")

    # Impersonation is the smallest class — its split footprint determines
    # whether val/test PR-AUC is stable.
    out.kv("AI impersonation (train/val/test)   ",
            f"{ (train_df.fraud_type=='ai_impersonation').sum() } / "
            f"{ (val_df.fraud_type=='ai_impersonation').sum() } / "
            f"{ (test_df.fraud_type=='ai_impersonation').sum() }")

    X_train_raw = train_df[MODEL_COLS].copy()
    X_val_raw = val_df[MODEL_COLS].copy()
    X_test_raw = test_df[MODEL_COLS].copy()
    y_train = train_df["is_fraud"].to_numpy()
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    train_medians = (
        X_train_raw[FEATURE_COLS]
        .replace([np.inf, -np.inf], np.nan)
        .median()
    )
    for frame in (X_train_raw, X_val_raw, X_test_raw):
        frame[FEATURE_COLS] = (
            frame[FEATURE_COLS]
            .replace([np.inf, -np.inf], np.nan)
            .fillna(train_medians)
        )

    X_train = pd.get_dummies(X_train_raw, columns=CAT_COLS).fillna(-1)
    X_val = (
        pd.get_dummies(X_val_raw, columns=CAT_COLS)
        .reindex(columns=X_train.columns, fill_value=0)
        .fillna(-1)
    )
    X_test = (
        pd.get_dummies(X_test_raw, columns=CAT_COLS)
        .reindex(columns=X_train.columns, fill_value=0)
        .fillna(-1)
    )

    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

    if not generate_only:
        out.banner("Training XGBoost")
        out.step(f"  scale_pos_weight = {scale_pos_weight:.2f}")
        out.step(f"  device = {XGB_DEVICE}")
        model = xgb.XGBClassifier(
            **XGB_PARAMS,
            scale_pos_weight=float(scale_pos_weight),
            early_stopping_rounds=50,
        )
        # eval_set on the val split caps useless trees via early stopping.
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        best_iter = getattr(model, "best_iteration", None)
        if best_iter is not None:
            out.kv("Best iteration", str(best_iter))
        # Atomic + retried save: XGBoost's own writer fails with Errno 22 when
        # Windows transiently locks the existing model file during overwrite.
        # Keep the .json suffix on the temp name so save_model stays in JSON
        # format (xgboost picks the format from the file extension).
        tmp_model = XGB_TIER1_JSON.with_name(XGB_TIER1_JSON.stem + ".tmp" + XGB_TIER1_JSON.suffix)
        model.save_model(str(tmp_model))
        _replace_with_retry(tmp_model, XGB_TIER1_JSON)
        out.kv("Saved model", XGB_TIER1_JSON.name)

    for frame, path in [
        (X_train, X_TRAIN_PKL), (X_val, X_VAL_PKL), (X_test, X_TEST_PKL),
        (train_df, TRAIN_DF_PKL), (val_df, VAL_DF_PKL), (test_df, TEST_DF_PKL),
    ]:
        _atomic_pickle(frame, path)
    out.kv("Saved feature matrices", "X_train.pkl, X_val.pkl, X_test.pkl")
    out.kv("Saved splits", "train_df.pkl, val_df.pkl, test_df.pkl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost Tier 1 fraud model")
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Generate train/val/test splits and feature matrices without training.",
    )
    args = parser.parse_args()
    train_model(generate_only=args.generate_only)
