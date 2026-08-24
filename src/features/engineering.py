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

    for _, idx in df.groupby("user_id", sort=False).indices.items():
        idx = np.asarray(idx)
        sub_ts = ts_int[idx]
        tx_1min[idx] = rolling_sum_trailing(sub_ts, one[idx], 60)
        tx_1hr[idx] = rolling_sum_trailing(sub_ts, one[idx], 3600)
        tx_24hr[idx] = rolling_sum_trailing(sub_ts, one[idx], 86400)
        sum_30d[idx] = rolling_sum_trailing(sub_ts, amount[idx], 30 * 86400)
        sum2_30d[idx] = rolling_sum_trailing(sub_ts, amount_sq[idx], 30 * 86400)
        count_30d[idx] = rolling_sum_trailing(sub_ts, one[idx], 30 * 86400)
        if len(idx) > 1:
            prev_ts[idx[1:]] = sub_ts[:-1]
            prev_lat[idx[1:]] = lat_arr[idx[:-1]]
            prev_lon[idx[1:]] = lon_arr[idx[:-1]]
        seen_dev, seen_merch, cat_counter, total_prior = set(), set(), {}, 0
        for pos in idx:
            d, m, c = dev_arr[pos], merch_arr[pos], cat_arr[pos]
            new_device[pos] = int(d not in seen_dev)
            new_merchant[pos] = int(m not in seen_merch)
            cat_freq[pos] = (cat_counter.get(c, 0) / total_prior) if total_prior else 0.0
            seen_dev.add(d); seen_merch.add(m)
            cat_counter[c] = cat_counter.get(c, 0) + 1
            total_prior += 1

    df["tx_last_1min"] = tx_1min; df["tx_last_1hr"] = tx_1hr; df["tx_last_24hr"] = tx_24hr
    df["count_30d"] = count_30d
    mean_30d = np.where(count_30d > 0, sum_30d / np.maximum(count_30d, 1), np.nan)
    var_30d = np.where(count_30d > 0, sum2_30d / np.maximum(count_30d, 1) - mean_30d ** 2, np.nan)
    std_30d = np.sqrt(np.clip(var_30d, 0, None))
    stable_std = np.maximum(std_30d, 0.10 * np.maximum(mean_30d, 1.0))
    z = np.where(count_30d > 0, (amount - mean_30d) / stable_std, 0.0)
    df["amount_zscore_30d"] = np.clip(z, -10, 10)
    df["new_device"] = new_device; df["new_merchant"] = new_merchant
    df["merchant_cat_freq_user"] = cat_freq
    df["time_since_last_s"] = ts_int - prev_ts
    df["dist_from_prev_km"] = haversine_km(prev_lat, prev_lon, lat_arr, lon_arr)
    with np.errstate(divide="ignore", invalid="ignore"):
        geo_velocity = df["dist_from_prev_km"] / (df["time_since_last_s"] / 3600.0)
    df["geo_velocity_kmh"] = geo_velocity.replace([np.inf, -np.inf], np.nan)
    df["hour_of_day"] = df["timestamp"].dt.hour
    df["three_ds_failures_before_result"] = df["three_ds_failures_before_result"].fillna(0).astype(float)
    return df

if __name__ == "__main__":
    df = pd.read_csv("data/raw/transactions.csv")
    df = add_features(df)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df.to_pickle("data/processed/transactions_features.pkl")
    print(df.shape)
    print(df.groupby("fraud_type").size())