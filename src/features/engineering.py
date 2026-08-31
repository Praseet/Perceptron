import os
from pathlib import Path
import sys
import numpy as np
import pandas as pd

# Import centralized configuration (for the default train-only cutoff used
# by the leakage-safe global fallback stat -- see add_features()).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TRAIN_QUANTILE

def rolling_sum_trailing(ts_int, values, window_seconds):
    ts_int = np.asarray(ts_int, dtype=np.int64)
    values = np.asarray(values, dtype=float)
    csum = np.concatenate(([0.0], np.cumsum(values)))
    lo = np.searchsorted(ts_int, ts_int - window_seconds, side="left")
    k = np.arange(len(ts_int))
    return csum[k] - csum[lo]

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1r, lon1r, lat2r, lon2r = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2r - lat1r) / 2) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin((lon2r - lon1r) / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def add_features(df, fit_mask=None):
    """
    Adds base + user-level temporal / behavioural features.

    Base features (existing, untouched):
        tx_last_1min/1hr/24hr, count_30d, amount_zscore_30d, new_device,
        new_merchant, merchant_cat_freq_user, time_since_last_s,
        dist_from_prev_km, geo_velocity_kmh, hour_of_day,
        three_ds_failures_before_result

    New user-level features (additive, no existing column rewritten):
        three_ds_failures_last_30d   - failed 3DS attempts in last 30d per user
        device_trust_age_days        - time since last trusted-device login
        burst_count                  - rolling count of high-amount txns
        inter_transaction_time_s     - time gap between consecutive user txns
        is_high_amount_burst         - flag for rapid-fire >$1k sequence

    Leakage note (fixed): `amount_zscore_30d` falls back to a GLOBAL
    mean/std whenever a row has no trailing-30-day history yet
    (`count_30d == 0` -- disproportionately first-ever transactions, where
    fraud types like account_takeover/bustout_identity concentrate). That
    global mean/std must never be computed over val/test rows, or the
    fallback leaks future information into the split boundary.

    `fit_mask`: boolean array/Series, same length and row-order as `df`,
    marking which rows are allowed to contribute to the global fallback
    mean/std. Pass the same boolean mask you use to build the TRAIN split
    downstream. If omitted (e.g. when running this module standalone,
    before any split exists), a train-only mask is derived internally
    using the same time-quantile convention as train.py
    (`config.TRAIN_QUANTILE`), so the fallback never sees "future" rows
    even in that mode.
    """
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
    df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

    ts_int = df["timestamp"].to_numpy(dtype="datetime64[s]").astype(np.int64)
    amount = df["amount"].to_numpy(dtype=float)
    amount_sq = amount ** 2
    one = np.ones(len(df), dtype=float)

    tx_1min = np.zeros(len(df)); tx_1hr = np.zeros(len(df)); tx_24hr = np.zeros(len(df))
    sum_30d = np.zeros(len(df)); sum2_30d = np.zeros(len(df)); count_30d = np.zeros(len(df))
    s30 = np.zeros(len(df)); s2_30d_raw = np.zeros(len(df))
    new_device = np.zeros(len(df), dtype=int); new_merchant = np.zeros(len(df), dtype=int)
    cat_freq = np.zeros(len(df), dtype=float)

    lat_arr = df["lat"].to_numpy(dtype=float)
    lon_arr = df["lon"].to_numpy(dtype=float)
    dev_arr = df["device_id"].to_numpy()
    merch_arr = df["merchant_id"].to_numpy()
    cat_arr = df["merchant_category"].to_numpy()

    # ---- NEW: per-user 3DS failure count (vectorized, no per-row loop) ----
    threeds_failure_ind = (df["three_ds_failures_before_result"].fillna(0).to_numpy() > 0).astype(float)
    threeds_30d = np.zeros(len(df), dtype=float)
    for _, idx in df.groupby("user_id", sort=False).indices.items():
        idx = np.asarray(idx)
        threeds_30d[idx] = rolling_sum_trailing(ts_int[idx], threeds_failure_ind[idx], 30 * 86400)
    df["three_ds_failures_last_30d"] = threeds_30d

    # ---- main per-user features (VECTORIZED - same output, no per-row Python) ----
    # Lags: previous-row ts/lat/lon within the same user (NaN for first row).
    # NOTE: prev_ts shifts the SECONDS column (_ts_int), not datetime64[ns] --
    # the old loop worked in seconds and downstream math expects the same unit.
    df["_ts_int"] = ts_int
    prev_ts = df.groupby("user_id", sort=False)["_ts_int"].shift(1).to_numpy()
    prev_lat = df.groupby("user_id", sort=False)["lat"].shift(1).to_numpy()
    prev_lon = df.groupby("user_id", sort=False)["lon"].shift(1).to_numpy()
    # "new" flags: differs from the immediately-previous row of the same user.
    new_device = (
        df["device_id"] != df.groupby("user_id", sort=False)["device_id"].shift(1)
    ).fillna(True).astype(int).to_numpy()
    new_merchant = (
        df["merchant_id"] != df.groupby("user_id", sort=False)["merchant_id"].shift(1)
    ).fillna(True).astype(int).to_numpy()

    # Rolling windows over PRIOR rows only (excludes the current row, exactly like
    # the old `past = ts_u[:j]` masks). Per-user numpy calls -- no per-row loop.
    for _, idx in df.groupby("user_id", sort=False).indices.items():
        idx = np.asarray(idx)
        ts_u = ts_int[idx]
        tx_1min[idx] = rolling_sum_trailing(ts_u, one[idx], 60)
        tx_1hr[idx] = rolling_sum_trailing(ts_u, one[idx], 3600)
        tx_24hr[idx] = rolling_sum_trailing(ts_u, one[idx], 86400)
        count_30d[idx] = rolling_sum_trailing(ts_u, one[idx], 30 * 86400)
        s30[idx] = rolling_sum_trailing(ts_u, amount[idx], 30 * 86400)
        s2_30d_raw[idx] = rolling_sum_trailing(ts_u, amount_sq[idx], 30 * 86400)

    # Replicate the exact sum_30d/sum2_30d semantics of the old loop:
    #   len>1 & sd>0 : sum_30d=mean, sum2_30d=sample-var   (else both stay 0)
    #   len==1       : sum_30d=single value, sum2_30d=0
    #   len==0       : both 0
    mean30 = np.where(count_30d > 0, s30 / np.maximum(count_30d, 1), 0.0)
    var_num30 = np.maximum(s2_30d_raw - count_30d * mean30 * mean30, 0.0)
    sd_pos30 = (count_30d > 1) & (var_num30 > 0)
    sum_30d = np.where(count_30d == 1, s30, np.where(sd_pos30, mean30, 0.0))
    sum2_30d = np.where(sd_pos30, var_num30 / np.maximum(count_30d - 1, 1), 0.0)

    # merchant_cat_freq_user = fraction of PRIOR rows of the same user+category.
    prior_same_cat = (
        df.assign(_c=1)
        .groupby(["user_id", "merchant_category"], sort=False)["_c"]
        .cumsum()
        - 1
    ).to_numpy()
    j_within = df.groupby("user_id", sort=False).cumcount().to_numpy()
    cat_freq = np.where(j_within > 0, prior_same_cat / j_within, 0.0)

    df["tx_last_1min"] = tx_1min
    df["tx_last_1hr"] = tx_1hr
    df["tx_last_24hr"] = tx_24hr
    df["count_30d"] = count_30d
    df["new_device"] = new_device
    df["new_merchant"] = new_merchant
    df["merchant_cat_freq_user"] = cat_freq

    # ---- leakage-safe global fallback stats (train-only) ----
    if fit_mask is None:
        # No explicit split provided: derive one internally using the same
        # temporal-quantile convention train.py uses, so the fallback stat
        # is still never computed over what will become val/test rows.
        cut1 = np.quantile(ts_int, TRAIN_QUANTILE)
        fit_mask_arr = ts_int <= cut1
    else:
        fit_mask_arr = np.asarray(fit_mask, dtype=bool)
        if fit_mask_arr.shape[0] != len(df):
            raise ValueError("fit_mask length must match df length "
                             f"({fit_mask_arr.shape[0]} != {len(df)}).")

    mean_amt = np.mean(amount[fit_mask_arr])
    std_amt = max(np.std(amount[fit_mask_arr]), 1e-9)
    # Avoid division by zero: replace sum2_30d=0 with small epsilon
    # P0.6 — `sum2_30d` is already the *sample variance* (SS / (n-1)); the
    # previous code divided by (n-1) AGAIN here, shrinking every 30-day
    # z-score and distorting this core behavioral feature for both XGB and IF.
    denom = np.sqrt(np.where(sum2_30d > 0, sum2_30d, 1.0))
    df["amount_zscore_30d"] = np.where(count_30d > 0,
                                       (amount - sum_30d) / denom,
                                       (amount - mean_amt) / std_amt)

    df["time_since_last_s"] = ts_int - prev_ts.astype(np.int64)
    df["time_since_last_s"] = df["time_since_last_s"].where(df["time_since_last_s"] > 0, np.nan)

    dist = haversine_km(prev_lat, prev_lon, lat_arr, lon_arr)
    df["dist_from_prev_km"] = np.where(np.isfinite(dist), dist, 0.0)

    dt = df["time_since_last_s"].to_numpy(dtype=float)
    dt_hr = np.where(dt > 0, dt / 3600.0, np.nan)
    df["geo_velocity_kmh"] = np.where(np.isfinite(dist) & np.isfinite(dt_hr) & (dt_hr > 1 / 3600),
                                     df["dist_from_prev_km"] / dt_hr, 0.0)

    df["hour_of_day"] = df["timestamp"].dt.hour

    # ---- NEW: device trust age (seconds since THIS device's last use) ----
    # ---- device trust age (seconds since THIS device's last use for this user) ----
    # Same semantics as the old per-row dict loop: within (user, device), the gap
    # to the previous use; NaN when the device is first seen for that user.
    device_age_s = (
        df.groupby(["user_id", "device_id"], sort=False)["_ts_int"].diff().to_numpy()
    )
    df.drop(columns=["_ts_int"], inplace=True)
    df["device_trust_age_s"] = device_age_s
    df["device_trust_age_days"] = device_age_s / 86400.0

    # ---- NEW: burst features for card_testing ----
    high_amt = (amount > 1000).astype(float)
    burst_10m = np.zeros(len(df), dtype=float)
    for _, idx in df.groupby("user_id", sort=False).indices.items():
        idx = np.asarray(idx)
        burst_10m[idx] = rolling_sum_trailing(ts_int[idx], high_amt[idx], 600)
    df["burst_count_10m"] = burst_10m
    df["is_high_amount_burst"] = (burst_10m >= 3).astype(int)

    # inter-transaction time (per user) -- mirrors time_since_last_s for LSTM/GNN pipelines
    df["inter_transaction_time_s"] = df["time_since_last_s"]

    df["three_ds_failures_before_result"] = df["three_ds_failures_before_result"].fillna(0).astype(float)

    return df

if __name__ == "__main__":
    from config import (
        TRANSACTIONS_CSV, TRANSACTIONS_PARQUET, TRANSACTIONS_FEATURES_PKL,
        ensure_directories,
    )

    # Fast path: read the parquet twin if present (pyarrow), else CSV.
    if TRANSACTIONS_PARQUET.exists():
        df = pd.read_parquet(TRANSACTIONS_PARQUET)
    else:
        df = pd.read_csv(TRANSACTIONS_CSV)

    # Pre-flight schema/quality check (see src/validation.py). Non-fatal by
    # default: this catches generator drift (unexpected category/channel
    # values, missing columns, null spikes) loudly in stdout rather than
    # silently propagating into feature engineering.
    try:
        from validation import validate_raw_data
        results = validate_raw_data(df, strict=False)
        errors = [r for r in results if r.severity.value == "error"]
        if errors:
            print(f"[validation] {len(errors)} error(s) in raw data -- see details below:")
            for r in errors:
                print(f"  ERROR [{r.check_name}] {r.message}")
        elif results:
            print(f"[validation] raw data passed with {len(results)} warning/info note(s).")
        else:
            print("[validation] raw data passed all checks.")
    except ImportError:
        print("[validation] src/validation.py not importable -- skipping pre-flight check.")

    df = add_features(df)
    ensure_directories()
    # Atomic write: temp file + replace, so an interrupted run or a transient
    # file lock (Windows Errno 22 on overwrite) can never corrupt the artifact.
    tmp_pkl = TRANSACTIONS_FEATURES_PKL.with_name(TRANSACTIONS_FEATURES_PKL.name + ".tmp")
    df.to_pickle(tmp_pkl)
    # The destination can be transiently locked on Windows (AV/indexer) right
    # after a big overwrite -- retry a few times before giving up.
    import time
    last_err = None
    for attempt in range(6):
        try:
            os.replace(tmp_pkl, TRANSACTIONS_FEATURES_PKL)
            last_err = None
            break
        except (PermissionError, OSError) as e:
            last_err = e
            time.sleep(1.5)
            try:
                TRANSACTIONS_FEATURES_PKL.unlink()
            except (FileNotFoundError, PermissionError):
                pass
    if last_err is not None:
        raise last_err
    print(df.shape)
    print(df.groupby("fraud_type").size())