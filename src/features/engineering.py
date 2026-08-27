from pathlib import Path
import numpy as np
import pandas as pd

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

def add_features(df):
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
    new_device = np.zeros(len(df), dtype=int); new_merchant = np.zeros(len(df), dtype=int)
    cat_freq = np.zeros(len(df), dtype=float)
    prev_ts = np.full(len(df), np.nan); prev_lat = np.full(len(df), np.nan); prev_lon = np.full(len(df), np.nan)

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

    # ---- main per-user loop: compute all rolling & lag features ----
    for _, idx in df.groupby("user_id", sort=False).indices.items():
        idx = np.asarray(idx)
        ts_u = ts_int[idx]
        amt_u = amount[idx]
        lat_u = lat_arr[idx]
        lon_u = lon_arr[idx]
        dev_u = dev_arr[idx]
        merch_u = merch_arr[idx]
        cat_u = cat_arr[idx]

        for j, pos in enumerate(idx):
            now = ts_u[j]
            past = ts_u[:j]
            if j == 0:
                prev_ts[pos] = np.nan
                prev_lat[pos] = np.nan
                prev_lon[pos] = np.nan
            else:
                prev_ts[pos] = ts_u[j - 1]
                prev_lat[pos] = lat_u[j - 1]
                prev_lon[pos] = lon_u[j - 1]

            window_1min = now - 60
            window_1hr = now - 3600
            window_24hr = now - 86400

            mask_1m = past >= window_1min
            mask_1h = past >= window_1hr
            mask_24h = past >= window_24hr

            tx_1min[pos] = mask_1m.sum()
            tx_1hr[pos] = mask_1h.sum()
            tx_24hr[pos] = mask_24h.sum()

            window_30d = now - 30 * 86400
            mask_30d = past >= window_30d
            vals_30d = amt_u[:j][mask_30d]
            count_30d[pos] = len(vals_30d)
            if len(vals_30d) > 1:
                m = vals_30d.mean()
                sd = vals_30d.std(ddof=1)
                if sd > 0:
                    sum_30d[pos] = m
                    sum2_30d[pos] = ((vals_30d - m) ** 2).sum() / (len(vals_30d) - 1)
            elif len(vals_30d) == 1:
                sum_30d[pos] = vals_30d[0]
                sum2_30d[pos] = 0.0

            new_device[pos] = 1 if (j == 0 or dev_u[j] != dev_u[j - 1]) else 0
            new_merchant[pos] = 1 if (j == 0 or merch_u[j] != merch_u[j - 1]) else 0

            if j > 0:
                cat_freq[pos] = np.sum(cat_u[:j] == cat_u[j]) / j

    df["tx_last_1min"] = tx_1min
    df["tx_last_1hr"] = tx_1hr
    df["tx_last_24hr"] = tx_24hr
    df["count_30d"] = count_30d
    df["new_device"] = new_device
    df["new_merchant"] = new_merchant
    df["merchant_cat_freq_user"] = cat_freq

    mean_amt = np.mean(amount)
    std_amt = max(np.std(amount), 1e-9)
    # Avoid division by zero: replace sum2_30d=0 with small epsilon
    denom = np.sqrt(np.where(sum2_30d > 0, sum2_30d / np.maximum(count_30d - 1, 1), 1.0))
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
    device_age_s = np.full(len(df), np.nan)
    for _, idx in df.groupby("user_id", sort=False).indices.items():
        idx = np.asarray(idx)
        last_seen = {}
        for pos in idx:
            d = dev_arr[pos]
            device_age_s[pos] = ts_int[pos] - last_seen[d] if d in last_seen else np.nan
            last_seen[d] = ts_int[pos]
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
    df = pd.read_csv("data/raw/transactions.csv")
    df = add_features(df)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_pickle("data/processed/transactions_features.pkl")
    print(df.shape)
    print(df.groupby("fraud_type").size())