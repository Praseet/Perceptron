"""
Sklearn-compatible transformers for the fraud detection pipeline.

These transformers encapsulate all feature engineering steps so they can be
packaged with the model for production inference without data leakage.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline

# Import centralized configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import (
    FEATURE_COLS, CAT_COLS, MODEL_COLS, BINARY_FLAG_COLS,
    STEERABLE_COLS
)


class DateTimeFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extract datetime features from timestamp column."""

    def __init__(self, timestamp_col="timestamp"):
        self.timestamp_col = timestamp_col

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        if self.timestamp_col in X.columns:
            X[self.timestamp_col] = pd.to_datetime(X[self.timestamp_col], errors="raise")
            X["hour_of_day"] = X[self.timestamp_col].dt.hour
        return X


class RollingFeatureExtractor(BaseEstimator, TransformerMixin):
    """Compute rolling temporal features per user using only training data statistics."""
    
    def __init__(self, timestamp_col="timestamp", user_col="user_id", amount_col="amount",
                 device_col="device_id", merchant_col="merchant_id",
                 category_col="merchant_category", lat_col="lat", lon_col="lon",
                 three_ds_col="three_ds_failures_before_result"):
        self.timestamp_col = timestamp_col
        self.user_col = user_col
        self.amount_col = amount_col
        self.device_col = device_col
        self.merchant_col = merchant_col
        self.category_col = category_col
        self.lat_col = lat_col
        self.lon_col = lon_col
        self.three_ds_col = three_ds_col
        
        # Statistics stored during fit (from training data only)
        self.global_amount_mean_ = None
        self.global_amount_std_ = None
        self.user_stats_ = {}  # per-user stats for amount_zscore_30d fallback

    def _rolling_sum_trailing(self, ts_int, values, window_seconds):
        ts_int = np.asarray(ts_int, dtype=np.int64)
        values = np.asarray(values, dtype=float)
        csum = np.concatenate(([0.0], np.cumsum(values)))
        lo = np.searchsorted(ts_int, ts_int - window_seconds, side="left")
        k = np.arange(len(ts_int))
        return csum[k] - csum[lo]

    def _haversine_km(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1r, lon1r, lat2r, lon2r = map(np.radians, [lat1, lon1, lat2, lon2])
        a = np.sin((lat2r - lat1r) / 2) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin((lon2r - lon1r) / 2) ** 2
        return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

    def fit(self, X, y=None):
        X = X.copy()
        X[self.timestamp_col] = pd.to_datetime(X[self.timestamp_col], errors="raise")
        X = X.sort_values([self.user_col, self.timestamp_col]).reset_index(drop=True)
        
        amount = X[self.amount_col].to_numpy(dtype=float)
        self.global_amount_mean_ = np.mean(amount)
        self.global_amount_std_ = max(np.std(amount), 1e-9)
        
        # Compute per-user 30-day stats for amount_zscore_30d fallback
        ts_int = X[self.timestamp_col].to_numpy(dtype="datetime64[s]").astype(np.int64)
        for user_id, group in X.groupby(self.user_col, sort=False):
            idx = group.index.to_numpy()
            ts_u = ts_int[idx]
            amt_u = amount[idx]
            
            # Compute 30-day rolling stats for each position (using only past data)
            # For fit, we compute the overall user stats as fallback
            vals_30d_all = amt_u[ts_u >= (ts_u[-1] - 30 * 86400)] if len(ts_u) > 0 else np.array([])
            if len(vals_30d_all) > 0:
                mean_30d = np.mean(vals_30d_all)
                std_30d = max(np.std(vals_30d_all, ddof=1), 1e-9) if len(vals_30d_all) > 1 else 1e-9
                count_30d = len(vals_30d_all)
            else:
                mean_30d = self.global_amount_mean_
                std_30d = self.global_amount_std_
                count_30d = 0
            
            self.user_stats_[user_id] = {
                "amount_30d_mean": mean_30d,
                "amount_30d_std": std_30d,
                "count_30d": count_30d,
            }
        
        return self

    def transform(self, X):
        X = X.copy()
        X[self.timestamp_col] = pd.to_datetime(X[self.timestamp_col], errors="raise")
        X = X.sort_values([self.user_col, self.timestamp_col]).reset_index(drop=True)
        
        ts_int = X[self.timestamp_col].to_numpy(dtype="datetime64[s]").astype(np.int64)
        amount = X[self.amount_col].to_numpy(dtype=float)
        lat_arr = X[self.lat_col].to_numpy(dtype=float)
        lon_arr = X[self.lon_col].to_numpy(dtype=float)
        dev_arr = X[self.device_col].to_numpy()
        merch_arr = X[self.merchant_col].to_numpy()
        cat_arr = X[self.category_col].to_numpy()
        three_ds_arr = X[self.three_ds_col].fillna(0).to_numpy(dtype=float)
        
        n = len(X)
        tx_1min = np.zeros(n)
        tx_1hr = np.zeros(n)
        tx_24hr = np.zeros(n)
        count_30d = np.zeros(n)
        sum_30d = np.zeros(n)
        sum2_30d = np.zeros(n)
        new_device = np.zeros(n, dtype=int)
        new_merchant = np.zeros(n, dtype=int)
        cat_freq = np.zeros(n, dtype=float)
        prev_ts = np.full(n, np.nan)
        prev_lat = np.full(n, np.nan)
        prev_lon = np.full(n, np.nan)
        threeds_30d = np.zeros(n, dtype=float)
        device_age_s = np.full(n, np.nan)
        high_amt = (amount > 1000).astype(float)
        burst_10m = np.zeros(n, dtype=float)
        
        # Per-user loop for rolling features
        for _, idx in X.groupby(self.user_col, sort=False).indices.items():
            idx = np.asarray(idx)
            ts_u = ts_int[idx]
            amt_u = amount[idx]
            lat_u = lat_arr[idx]
            lon_u = lon_arr[idx]
            dev_u = dev_arr[idx]
            merch_u = merch_arr[idx]
            cat_u = cat_arr[idx]
            three_ds_u = three_ds_arr[idx]
            
            # 3DS failures in last 30d
            threeds_ind = (three_ds_u > 0).astype(float)
            threeds_30d[idx] = self._rolling_sum_trailing(ts_u, threeds_ind, 30 * 86400)
            
            # Burst count (high amount in last 10 min)
            burst_10m[idx] = self._rolling_sum_trailing(ts_u, high_amt[idx], 600)
            
            # Device trust age
            last_seen = {}
            for j, pos in enumerate(idx):
                d = dev_u[j]
                device_age_s[pos] = ts_u[j] - last_seen[d] if d in last_seen else np.nan
                last_seen[d] = ts_u[j]
            
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
        
        # Assign computed features
        X["tx_last_1min"] = tx_1min
        X["tx_last_1hr"] = tx_1hr
        X["tx_last_24hr"] = tx_24hr
        X["count_30d"] = count_30d
        X["new_device"] = new_device
        X["new_merchant"] = new_merchant
        X["merchant_cat_freq_user"] = cat_freq
        X["three_ds_failures_last_30d"] = threeds_30d
        X["device_trust_age_s"] = device_age_s
        X["device_trust_age_days"] = device_age_s / 86400.0
        X["burst_count_10m"] = burst_10m
        X["is_high_amount_burst"] = (burst_10m >= 3).astype(int)
        
        # amount_zscore_30d
        denom = np.sqrt(np.where(sum2_30d > 0, sum2_30d / np.maximum(count_30d - 1, 1), 1.0))
        X["amount_zscore_30d"] = np.where(
            count_30d > 0,
            (amount - sum_30d) / denom,
            (amount - self.global_amount_mean_) / self.global_amount_std_
        )
        
        # time_since_last_s
        X["time_since_last_s"] = ts_int - prev_ts.astype(np.int64)
        X["time_since_last_s"] = X["time_since_last_s"].where(X["time_since_last_s"] > 0, np.nan)
        
        # Distance and geo velocity
        dist = self._haversine_km(prev_lat, prev_lon, lat_arr, lon_arr)
        X["dist_from_prev_km"] = np.where(np.isfinite(dist), dist, 0.0)
        
        dt = X["time_since_last_s"].to_numpy(dtype=float)
        dt_hr = np.where(dt > 0, dt / 3600.0, np.nan)
        X["geo_velocity_kmh"] = np.where(
            np.isfinite(dist) & np.isfinite(dt_hr) & (dt_hr > 1 / 3600),
            X["dist_from_prev_km"] / dt_hr, 0.0
        )
        
        X["hour_of_day"] = X[self.timestamp_col].dt.hour
        X["inter_transaction_time_s"] = X["time_since_last_s"]
        X["three_ds_failures_before_result"] = three_ds_arr
        
        return X


class CategoricalEncoder(BaseEstimator, TransformerMixin):
    """Encode categorical columns using OneHotEncoder with handle_unknown='ignore'."""

    def __init__(self, cat_cols=None):
        self.cat_cols = cat_cols or CAT_COLS
        self.encoder_ = None
        self.feature_names_out_ = None

    def fit(self, X, y=None):
        X_cat = X[self.cat_cols].astype(str)
        self.encoder_ = OneHotEncoder(
            sparse_output=False,
            handle_unknown="ignore",
            dtype=np.float32
        )
        self.encoder_.fit(X_cat)
        self.feature_names_out_ = self.encoder_.get_feature_names_out(self.cat_cols)
        return self

    def transform(self, X):
        X_cat = X[self.cat_cols].astype(str)
        X_encoded = self.encoder_.transform(X_cat)
        encoded_df = pd.DataFrame(
            X_encoded,
            columns=self.feature_names_out_,
            index=X.index
        )
        X = X.drop(columns=self.cat_cols)
        X = pd.concat([X, encoded_df], axis=1)
        return X

    def get_feature_names_out(self, input_features=None):
        if self.feature_names_out_ is not None:
            return self.feature_names_out_
        return np.array([])


class FeatureSelector(BaseEstimator, TransformerMixin):
    """Select and order features to match training-time feature matrix."""

    def __init__(self, expected_features=None):
        self.expected_features = expected_features

    def fit(self, X, y=None):
        if self.expected_features is None:
            self.expected_features = list(X.columns)
        return self

    def transform(self, X):
        # Add missing columns with default values
        for col in self.expected_features:
            if col not in X.columns:
                if col in BINARY_FLAG_COLS:
                    X[col] = 0
                else:
                    X[col] = 0.0
        # Reorder columns to match training
        X = X[self.expected_features]
        return X


class NumericScaler(BaseEstimator, TransformerMixin):
    """Scale numeric features using StandardScaler fitted on training data."""

    def __init__(self, feature_cols=None):
        self.feature_cols = feature_cols or FEATURE_COLS
        self.scaler_ = None

    def fit(self, X, y=None):
        X_num = X[self.feature_cols].replace([np.inf, -np.inf], np.nan)
        self.scaler_ = StandardScaler()
        self.scaler_.fit(X_num)
        return self

    def transform(self, X):
        X = X.copy()
        X_num = X[self.feature_cols].replace([np.inf, -np.inf], np.nan)
        X_scaled = self.scaler_.transform(X_num)
        X[self.feature_cols] = X_scaled
        return X


class FeaturePipeline:
    """Convenience class to build the full feature engineering pipeline."""

    @staticmethod
    def create_pipeline(training_columns=None):
        """Create a sklearn Pipeline with all transformers."""
        steps = [
            ("datetime", DateTimeFeatureExtractor()),
            ("rolling_features", RollingFeatureExtractor()),
            ("categorical", CategoricalEncoder()),
            ("selector", FeatureSelector(expected_features=training_columns)),
            ("scaler", NumericScaler()),
        ]
        return Pipeline(steps)