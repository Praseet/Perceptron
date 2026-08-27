"""
Tier 2 -- SMOTENC synthetic minority augmentation.

Replaces the CTGAN attempt for the two weakest minority classes
(ai_impersonation, auth_bypass) after the CTGAN run's own range-sanity gate
rejected nearly everything it generated: train_df_ctgan.pkl ended up with
only 2 accepted synthetic rows over the frozen 149,546-row train set
(ai_impersonation got zero). That is the memorization regime its own
docstring warned about at this row count -- a GAN cannot learn a
distribution from tens of rows. SMOTENC's k-NN interpolate/majority-vote
approach degrades gracefully down to k_neighbors+1 rows and makes no claim
of learning a broader generative distribution -- it interpolates between
real examples that already exist, which is the honest claim here.

THE ONE RULE (see README): SMOTENC runs on the RAW model columns BEFORE
pd.get_dummies(). Categorical columns and the 0/1 flags (new_device,
new_merchant) are declared via categorical_features so they receive
neighbor majority-vote values instead of linear interpolation -- a row that
is "channel_online=0.37" can never be produced. Plain SMOTE, or SMOTE run
on already-one-hot-encoded frames, silently reintroduces that bug.

DOES NOT TOUCH: models_artifacts/*, data/processed/train_df.pkl,
train_df_ctgan.pkl, X_*.pkl, val/test pickles. All outputs are new files
with a `_smotenc` suffix. Val/test stay 100% real; synthetic rows only ever
enter the TRAIN split.

Hygiene note: ctgan_augment.py / ctgan_train.py are left in place, unused
by this script -- CTGAN remains the augmentation path for classes that one
day reach hundreds of real rows per class, where it is the stronger tool.
The two paths compose: each writes its own augmented pickle and never
modifies frozen artifacts.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTENC

SEED = 42
FEATURE_COLS = ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                "count_30d", "amount_zscore_30d", "new_device", "new_merchant",
                "merchant_cat_freq_user", "time_since_last_s", "dist_from_prev_km",
                "geo_velocity_kmh", "hour_of_day", "three_ds_failures_before_result"]
CAT_COLS = ["merchant_category", "channel", "three_ds_result"]
MODEL_COLS = FEATURE_COLS + CAT_COLS

# new_device/new_merchant are 0/1 flags -- declared categorical alongside the
# true categoricals so majority-vote keeps them integral (same reasoning as
# ctgan_augment.py's DISCRETE_COLS).
BINARY_FLAG_COLS = ["new_device", "new_merchant"]

# Same two classes CTGAN targeted: weakest per-fraud-type PR-AUC in the
# frozen Tier 1 eval and near-total FN concentration. account_takeover (68
# rows) stays untouched -- it was already well separated (PR-AUC ~0.995),
# and adding synthetic rows there only risks diluting real signal.
TARGET_CLASSES = {
    "ai_impersonation": 200,  # counts are desired totals AFTER resampling
    "auth_bypass": 200,
}

K_NEIGHBORS = 5  # needs min(class_size) >= k+1 = 6; smallest targeted class has 54


def _label_encode_categoricals(X_raw):
    """Integer-encode categoricals with maps fit on REAL train rows only.

    Integer codes (not one-hot dummies) are what SMOTENC wants for its
    categorical columns: it majority-votes over neighbor CODES, so every
    generated value is a code that actually exists in the data.
    """
    X_enc = X_raw.copy()
    category_maps = {}
    for col in CAT_COLS:
        categories = sorted(X_raw[col].dropna().unique(), key=str)
        category_maps[col] = {cat: i for i, cat in enumerate(categories)}
        X_enc[col] = X_raw[col].map(category_maps[col])
    return X_enc, category_maps


def generate_synthetic_minority_rows(train_df):
    """Returns (synthetic_df, info dict). synthetic_df has MODEL_COLS plus
    fraud_type/is_fraud/case_id; all other train columns stay NaN."""
    X_raw = train_df[MODEL_COLS].copy()

    # SMOTENC requires complete numeric inputs. Impute with medians fit on
    # the REAL train rows only (all rows here are real train), same rule as
    # train.py -- never val/test statistics.
    train_medians = X_raw[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).median()
    X_raw[FEATURE_COLS] = X_raw[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).fillna(train_medians)
    if X_raw.isna().any().any():
        raise ValueError("NaNs remain in raw model columns after median imputation "
                         "-- check the feature matrix before running SMOTENC.")

    X_enc, category_maps = _label_encode_categoricals(X_raw)
    y_type = train_df["fraud_type"].to_numpy()

    # Positions within MODEL_COLS order (FEATURE_COLS first).
    categorical_idx = [MODEL_COLS.index(c) for c in BINARY_FLAG_COLS + CAT_COLS]

    class_sizes = pd.Series(y_type).value_counts()
    k_plus_one = K_NEIGHBORS + 1
    for fraud_type in TARGET_CLASSES:
        if class_sizes.get(fraud_type, 0) < k_plus_one:
            raise ValueError(
                f"{fraud_type} has {class_sizes.get(fraud_type, 0)} real train rows; "
                f"SMOTENC needs >= {k_plus_one} (k_neighbors={K_NEIGHBORS}).")

    smotenc = SMOTENC(
        categorical_features=categorical_idx,
        sampling_strategy=dict(TARGET_CLASSES),  # desired per-class totals AFTER resampling;
        k_neighbors=K_NEIGHBORS,                 # without it, "auto" equalizes EVERY minority
        random_state=SEED,                       # class to the majority count
    )
    X_res, y_res = smotenc.fit_resample(X_enc.to_numpy(), y_type)

    n_generated = len(X_res) - len(X_enc)
    print(f"SMOTENC generated {n_generated} synthetic rows "
          f"(train: {len(X_enc):,} -> {len(X_res):,})")

    # Over-samplers append generated samples at the end of the frame.
    syn_numeric = X_res[len(X_enc):]
    syn_types = y_res[len(X_enc):]
    expected_counts = {t: TARGET_CLASSES[t] - int(class_sizes[t]) for t in TARGET_CLASSES}
    actual_counts = pd.Series(syn_types).value_counts().to_dict()
    if actual_counts != expected_counts:
        raise ValueError(f"SMOTENC returned unexpected per-class synthetic counts: "
                         f"{actual_counts}, expected {expected_counts}.")

    return _decode_synthetic(syn_numeric.astype(float), syn_types, category_maps), \
        {"generated": n_generated, "per_class": actual_counts,
         "real_class_counts": class_sizes.to_dict()}


def _decode_synthetic(syn_numeric, syn_types, category_maps):
    """Rebuilds a labeled DataFrame from SMOTENC's numeric output matrix,
    verifying every generated categorical value is a REAL category."""
    syn_df = pd.DataFrame(syn_numeric, columns=MODEL_COLS)
    for col in CAT_COLS:
        inverse_map = {i: cat for cat, i in category_maps[col].items()}
        codes = syn_df[col].round().astype(int)
        unknown = set(codes.unique()) - set(inverse_map)
        if unknown:
            raise ValueError(f"{col}: SMOTENC produced category codes {unknown} "
                             f"that do not exist in the real train data.")
        syn_df[col] = codes.map(inverse_map)

    # Majority-vote should have kept the flags integral; enforce explicitly.
    for col in BINARY_FLAG_COLS:
        bad = ~syn_df[col].isin([0, 1])
        if bad.any():
            raise ValueError(f"{col}: {int(bad.sum())} synthetic rows have non-binary "
                             f"values -- SMOTENC did not receive this column as categorical.")
        syn_df[col] = syn_df[col].astype(int)

    syn_df["fraud_type"] = syn_types
    syn_df["is_fraud"] = 1
    syn_df["case_id"] = [f"synthetic_smotenc_{ft}_{i:05d}" for i, ft in enumerate(syn_types)]
    return syn_df


if __name__ == "__main__":
    print("=" * 80)
    print("TIER 2: SMOTENC SYNTHETIC MINORITY AUGMENTATION")
    print("=" * 80)

    train_df = pd.read_pickle("data/processed/train_df.pkl")  # frozen, read-only here
    print(f"Loaded frozen train_df: {len(train_df):,} rows")

    synthetic_df, info = generate_synthetic_minority_rows(train_df)
    print(f"\nPer-class synthetic rows: {info['per_class']}")

    # Columns not produced by SMOTENC (transaction_id, user_id, timestamp,
    # lat/lon, ...) aren't used by MODEL_COLS but ARE needed so
    # smotenc_train.py can concatenate cleanly with train_df.
    for col in train_df.columns:
        if col not in synthetic_df.columns:
            synthetic_df[col] = np.nan
    synthetic_df = synthetic_df[train_df.columns]

    augmented_train_df = pd.concat([train_df, synthetic_df], ignore_index=True)

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    augmented_train_df.to_pickle("data/processed/train_df_smotenc.pkl")
    synthetic_df.to_pickle("data/processed/synthetic_minority_rows_smotenc.pkl")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Original train_df.pkl (untouched): {len(train_df):,} rows")
    print(f"Synthetic rows generated:          {len(synthetic_df):,} rows")
    print(f"New train_df_smotenc.pkl:          {len(augmented_train_df):,} rows")
    print("\nfraud_type counts in augmented train:")
    print(augmented_train_df["fraud_type"].value_counts().to_string())
    print("\nSaved: data/processed/train_df_smotenc.pkl (new -- train_df.pkl untouched)")
    print("Saved: data/processed/synthetic_minority_rows_smotenc.pkl (synthetic rows only, for audit)")
