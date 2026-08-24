from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
from imblearn.over_sampling import SMOTENC

df = pd.read_pickle("data/processed/transactions_features.pkl")
order = np.argsort(df["timestamp"].to_numpy())
df = df.iloc[order].reset_index(drop=True)
ts = df["timestamp"].astype("int64").to_numpy()
cut1 = np.quantile(ts, 0.70)
cut2 = np.quantile(ts, 0.80)
train_df = df[ts <= cut1].copy()
val_df = df[(ts > cut1) & (ts <= cut2)].copy()
test_df = df[ts > cut2].copy()

print("rows:", len(train_df), len(val_df), len(test_df))
print("fraud rate:", train_df["is_fraud"].mean(), val_df["is_fraud"].mean(), test_df["is_fraud"].mean())
print("impersonation counts (train/val/test):",
      (train_df.fraud_type == "ai_impersonation").sum(),
      (val_df.fraud_type == "ai_impersonation").sum(),
      (test_df.fraud_type == "ai_impersonation").sum())

feature_cols = ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                "count_30d", "amount_zscore_30d", "new_device", "new_merchant",
                "merchant_cat_freq_user", "time_since_last_s", "dist_from_prev_km",
                "geo_velocity_kmh", "hour_of_day", "three_ds_failures_before_result"]
cat_cols = ["merchant_category", "channel", "three_ds_result"]
model_cols = feature_cols + cat_cols

X_train_raw = train_df[model_cols].copy()
X_val_raw = val_df[model_cols].copy()
X_test_raw = test_df[model_cols].copy()
y_train = train_df["is_fraud"].to_numpy()
y_val = val_df["is_fraud"].to_numpy()
y_test = test_df["is_fraud"].to_numpy()

train_medians = X_train_raw[feature_cols].replace([np.inf, -np.inf], np.nan).median()
for frame in (X_train_raw, X_val_raw, X_test_raw):
    frame[feature_cols] = frame[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(train_medians)

X_train = pd.get_dummies(X_train_raw, columns=cat_cols).fillna(-1)
X_val = pd.get_dummies(X_val_raw, columns=cat_cols).reindex(columns=X_train.columns, fill_value=0).fillna(-1)
X_test = pd.get_dummies(X_test_raw, columns=cat_cols).reindex(columns=X_train.columns, fill_value=0).fillna(-1)

scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
print("scale_pos_weight:", scale_pos_weight)

model = xgb.XGBClassifier(
    n_estimators=300, max_depth=4, learning_rate=0.08,
    scale_pos_weight=float(scale_pos_weight), eval_metric="aucpr",
    subsample=0.8, colsample_bytree=0.8, random_state=42, tree_method="hist",
)
model.fit(X_train, y_train)

Path("models_artifacts").mkdir(parents=True, exist_ok=True)
model.save_model("models_artifacts/xgboost_tier1.json")

X_train.to_pickle("data/processed/X_train.pkl"); X_val.to_pickle("data/processed/X_val.pkl"); X_test.to_pickle("data/processed/X_test.pkl")
train_df.to_pickle("data/processed/train_df.pkl"); val_df.to_pickle("data/processed/val_df.pkl"); test_df.to_pickle("data/processed/test_df.pkl")
print("done")