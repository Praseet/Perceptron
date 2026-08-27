"""
Tier 2 -- CTGAN synthetic minority augmentation.

Generates synthetic ai_impersonation and auth_bypass transaction rows to
address the two classes with weakest per-fraud-type PR-AUC in the frozen
Tier 1 evaluation (ai_impersonation PR-AUC=0.16 n=8 test, auth_bypass
PR-AUC=0.14 n=11 test) and near-total False Negative concentration
(18 of 19 test FNs are one of these two classes).

DOES NOT TOUCH: models_artifacts/xgboost_tier1.json, data/processed/train_df.pkl,
X_train.pkl, val_df.pkl, X_val.pkl, test_df.pkl, X_test.pkl. All outputs are new
files with a `_ctgan` suffix. Val/test stay 100% real -- synthetic rows only
ever enter the TRAIN split, matching this project's existing discipline of
never letting synthetic/future information leak into evaluation.

ASSUMPTIONS / DEVIATIONS (flagged per request):
- ai_impersonation has only 26 real TRAIN rows. CTGAN is normally trained on
  hundreds-to-thousands of rows; at n=26 it will tend to interpolate near/
  memorize the existing examples rather than learn a genuinely broader
  distribution. Treat synthetic rows as *interpolation*, not new signal --
  the real test of value is the before/after eval in train_v2_ctgan.py, not
  an assumption that augmentation automatically helps.
- CTGAN defaults (batch_size=500, pac=10) assume large training sets; with
  26-59 rows those defaults would error (batch_size must be a multiple of
  pac and can't sensibly exceed the dataset). Both are reduced below.
- Fixed seeds (numpy/random/torch) are set for reproducibility, but CTGAN's
  underlying GAN training is not guaranteed bit-exact across
  hardware/backends even with seeds fixed -- flagging this as a known
  upstream limitation, not a bug in this script.
- pip install ctgan (brings in torch as a dependency).
"""
from pathlib import Path
import random
import numpy as np
import pandas as pd
import torch
from ctgan import CTGAN

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

FEATURE_COLS = ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                "count_30d", "amount_zscore_30d", "new_device", "new_merchant",
                "merchant_cat_freq_user", "time_since_last_s", "dist_from_prev_km",
                "geo_velocity_kmh", "hour_of_day", "three_ds_failures_before_result"]
CAT_COLS = ["merchant_category", "channel", "three_ds_result"]
MODEL_COLS = FEATURE_COLS + CAT_COLS
# new_device/new_merchant are 0/1 flags, not continuous -- CTGAN treats
# anything not listed here as continuous, so they must be declared discrete
# alongside the true categoricals or CTGAN will try to model a continuous
# distribution over what is actually a two-value flag.
DISCRETE_COLS = CAT_COLS + ["new_device", "new_merchant"]

# Targeted at the two classes with weakest per-type PR-AUC and the bulk of
# test-set false negatives in the frozen Tier 1 evaluation. account_takeover
# (PR-AUC=0.9952) and bustout_identity/card_testing (PR-AUC ~1.0) are already
# well-separated and are NOT augmented -- there's no problem to solve there,
# and adding synthetic rows only risks diluting real signal.
TARGET_CLASSES = {
    "ai_impersonation": 200,  # 26 real train rows -> target 200 combined
    "auth_bypass": 200,       # ~41 real train rows -> target 200 combined
}


def _fit_ctgan_for_class(train_df: pd.DataFrame, fraud_type: str) -> CTGAN:
    class_rows = train_df.loc[train_df["fraud_type"] == fraud_type, MODEL_COLS].copy()
    n_real = len(class_rows)
    print(f"  Real TRAIN rows for {fraud_type}: {n_real}")
    if n_real < 10:
        raise ValueError(f"{fraud_type} has only {n_real} real train rows -- too few for CTGAN "
                          f"to fit meaningfully. Skipping rather than fabricating from noise.")

    # pac=1 and a small batch_size are deviations from CTGAN's library
    # defaults (batch_size=500, pac=10), required because those defaults
    # assume a training set far larger than our minority classes.
    batch_size = min(64, n_real)
    model = CTGAN(epochs=300, batch_size=batch_size, pac=1, verbose=False)
    model.fit(class_rows, discrete_columns=DISCRETE_COLS)
    return model


def _validate_synthetic_rows(synthetic: pd.DataFrame, real: pd.DataFrame) -> pd.DataFrame:
    """
    Range-sanity gate: reject synthetic rows with values outside what the
    real minority-class rows ever showed (with slack), for columns where an
    out-of-range value is nonsensical rather than merely unusual. Same
    "reject, don't silently launder" discipline this project's LLM-transcript
    validators already use, applied here to tabular data.
    """
    keep = pd.Series(True, index=synthetic.index)
    for col in ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                "count_30d", "time_since_last_s", "dist_from_prev_km", "geo_velocity_kmh"]:
        if col not in synthetic.columns:
            continue
        lo = min(0.0, real[col].min())
        hi = real[col].max() * 1.5 + 1e-6  # 50% slack above the largest real value observed
        keep &= synthetic[col].between(lo, hi)
    if "hour_of_day" in synthetic.columns:
        keep &= synthetic["hour_of_day"].between(0, 23)
    n_rejected = int((~keep).sum())
    if n_rejected:
        print(f"  Range-sanity gate rejected {n_rejected}/{len(synthetic)} synthetic rows.")
    return synthetic.loc[keep].reset_index(drop=True)


def generate_synthetic_minority_rows(train_df: pd.DataFrame) -> pd.DataFrame:
    synthetic_frames = []
    for fraud_type, target_total in TARGET_CLASSES.items():
        print(f"\nFitting CTGAN for '{fraud_type}'...")
        real_rows = train_df.loc[train_df["fraud_type"] == fraud_type, MODEL_COLS].reset_index(drop=True)
        n_needed = max(0, target_total - len(real_rows))
        if n_needed == 0:
            print(f"  Already at/above target ({len(real_rows)} >= {target_total}); skipping.")
            continue

        model = _fit_ctgan_for_class(train_df, fraud_type)

        # Oversample and filter rather than sampling exactly n_needed, since
        # the range-sanity gate will reject some fraction of rows.
        raw_sample = model.sample(n_needed * 2)
        valid_sample = _validate_synthetic_rows(raw_sample, real_rows)
        if len(valid_sample) < n_needed:
            print(f"  WARNING: only {len(valid_sample)}/{n_needed} valid synthetic rows generated "
                  f"for {fraud_type} after the sanity gate -- using what passed rather than "
                  f"padding with rejected rows.")
        valid_sample = valid_sample.head(n_needed)

        valid_sample["fraud_type"] = fraud_type
        valid_sample["is_fraud"] = 1
        valid_sample["case_id"] = [f"synthetic_ctgan_{fraud_type}_{i:05d}" for i in range(len(valid_sample))]
        print(f"  Accepted {len(valid_sample)} synthetic '{fraud_type}' rows "
              f"({len(real_rows)} real + {len(valid_sample)} synthetic = "
              f"{len(real_rows) + len(valid_sample)} total in augmented train).")
        synthetic_frames.append(valid_sample)

    if not synthetic_frames:
        return pd.DataFrame(columns=list(train_df.columns))
    return pd.concat(synthetic_frames, ignore_index=True)


if __name__ == "__main__":
    print("=" * 80)
    print("TIER 2: CTGAN SYNTHETIC MINORITY AUGMENTATION")
    print("=" * 80)

    train_df = pd.read_pickle("data/processed/train_df.pkl")  # frozen, read-only here
    print(f"Loaded frozen train_df: {len(train_df):,} rows")

    synthetic_df = generate_synthetic_minority_rows(train_df)

    # Columns not produced by CTGAN (transaction_id, user_id, timestamp,
    # lat/lon, etc.) aren't used by MODEL_COLS or needed for training, but
    # ARE needed so train_v2_ctgan.py can concatenate cleanly with train_df.
    for col in train_df.columns:
        if col not in synthetic_df.columns:
            synthetic_df[col] = np.nan
    synthetic_df = synthetic_df[train_df.columns]

    augmented_train_df = pd.concat([train_df, synthetic_df], ignore_index=True)

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    augmented_train_df.to_pickle("data/processed/train_df_ctgan.pkl")
    synthetic_df.to_pickle("data/processed/synthetic_minority_rows_ctgan.pkl")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Original train_df.pkl (untouched): {len(train_df):,} rows")
    print(f"Synthetic rows generated:          {len(synthetic_df):,} rows")
    print(f"New train_df_ctgan.pkl:            {len(augmented_train_df):,} rows")
    print("\nfraud_type counts in augmented train:")
    print(augmented_train_df["fraud_type"].value_counts().to_string())
    print("\nSaved: data/processed/train_df_ctgan.pkl (new -- train_df.pkl untouched)")
    print("Saved: data/processed/synthetic_minority_rows_ctgan.pkl (synthetic rows only, for audit)")