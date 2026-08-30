# H.30 Current model-field facts

The authoritative model input count is:

```text
20 numeric features
+ 3 categorical features
= 23 MODEL_COLS
```

Numeric:

```text
amount
account_age_days
tx_last_1min
tx_last_1hr
tx_last_24hr
count_30d
amount_zscore_30d
new_device
new_merchant
merchant_cat_freq_user
time_since_last_s
dist_from_prev_km
geo_velocity_kmh
hour_of_day
three_ds_failures_before_result
three_ds_failures_last_30d
device_trust_age_days
burst_count_10m
is_high_amount_burst
inter_transaction_time_s
```

Categorical:

```text
merchant_category
channel
three_ds_result
```

The current `src/config.py` is the source of truth for this list.

Never create a shortened “frontend version” and then silently submit only the shortened version to the model.

---

