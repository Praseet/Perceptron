import itertools
import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42

try:
    from src.config import pool_size_for
except Exception:
    try:
        from config import pool_size_for
    except Exception:
        _FTT = {
            "account_takeover": 120, "ai_impersonation": 80, "auth_bypass": 220,
            "bustout_identity": 450, "card_testing": 340, "synthetic_identity": 100,
            "bnpl_abuse": 80,
        }
        _APC = {
            "card_testing": 6, "account_takeover": 3, "auth_bypass": 1,
            "bustout_identity": 22, "ai_impersonation": 1,
            "synthetic_identity": 19, "bnpl_abuse": 17,
        }
        import math as _math
        def pool_size_for(ft):
            return max(1, _math.ceil(_FTT[ft] / _APC[ft]))

rng = np.random.default_rng(SEED)

SIM_START = datetime(2026, 1, 1)
SIM_DAYS = 60
N_USERS = 15000
N_MERCHANTS = 1000

CATEGORIES = [
    "grocery", "restaurant", "fuel", "ecommerce", "utility",
    "travel", "electronics", "pharmacy", "entertainment", "clothing"
]
CAT_PARAMS = {
    "grocery": (6.5, 0.5), "restaurant": (6.2, 0.6), "fuel": (6.8, 0.4),
    "ecommerce": (7.0, 0.9), "utility": (6.7, 0.5), "travel": (8.0, 1.0),
    "electronics": (8.3, 0.9), "pharmacy": (5.8, 0.6),
    "entertainment": (6.3, 0.7), "clothing": (6.9, 0.7),
}

CASE_COUNTER = itertools.count(1)
TX_COUNTER = itertools.count(1)

def new_case_id(fraud_type: str) -> str:
    return f"case_{fraud_type}_{next(CASE_COUNTER):06d}"

def new_tx_id() -> str:
    return f"tx_{next(TX_COUNTER):09d}"

merchant_ids = np.arange(N_MERCHANTS)
merchant_category = rng.choice(CATEGORIES, size=N_MERCHANTS)
cat_lookup = dict(zip(merchant_ids, merchant_category))

user_ids = np.arange(N_USERS)
home_lat = rng.uniform(8.0, 28.0, N_USERS)
home_lon = rng.uniform(72.0, 88.0, N_USERS)
account_age_at_start = rng.integers(30, 3000, N_USERS)
base_rate = np.clip(rng.gamma(shape=2.0, scale=0.6, size=N_USERS), 0.05, None)

existing_devices = [f"dev_{u}_0" for u in range(N_USERS)]

users = pd.DataFrame({
    "user_id": user_ids,
    "home_lat": home_lat,
    "home_lon": home_lon,
    "account_age_days_at_start": account_age_at_start,
    "base_transaction_rate": base_rate,
}).set_index("user_id")

user_habitual = {u: rng.choice(merchant_ids, size=8, replace=False) for u in user_ids}

def sample_normal_auth():
    draw = rng.random()
    if draw < 0.78:
        return "passed_first_try", 0
    if draw < 0.94:
        return "failed_then_passed", int(rng.integers(1, 5))
    return "not_attempted", 0

def sample_event_timestamp(day_float: float) -> datetime:
    return SIM_START + timedelta(days=float(day_float))

rows = []
print(f"[generator] generating normal transactions for {N_USERS} users...", flush=True)
_COL_NAMES = [
    "transaction_id", "user_id", "timestamp", "amount", "merchant_id",
    "merchant_category", "device_id", "lat", "lon", "channel",
    "account_age_days", "is_fraud", "fraud_type", "case_id", "ring_id",
    "three_ds_result", "three_ds_failures_before_result",
]
_col_buf: dict = {c: [] for c in _COL_NAMES}
_progress_every = max(1, N_USERS // 20)
for _ui, u in enumerate(user_ids):
    urow = users.loc[u]
    t = rng.uniform(0.0, 1.0)
    while True:
        t += rng.exponential(1.0 / urow.base_transaction_rate)
        if t >= SIM_DAYS:
            break
        m = int(rng.choice(user_habitual[u])) if rng.random() < 0.90 else int(rng.choice(merchant_ids))
        cat = cat_lookup[m]
        amount = float(rng.lognormal(*CAT_PARAMS[cat]))
        device = f"dev_{u}_0" if rng.random() < 0.95 else f"dev_{u}_1"
        if rng.random() < 0.03:
            lat = urow.home_lat + rng.normal(0, 6)
            lon = urow.home_lon + rng.normal(0, 6)
        else:
            lat = urow.home_lat + rng.normal(0, 0.05)
            lon = urow.home_lon + rng.normal(0, 0.05)
        channel = "card_present" if rng.random() < 0.55 else "ecom"
        if channel == "ecom":
            three_ds_result, failures = sample_normal_auth()
        else:
            three_ds_result, failures = "not_attempted", 0
        event_age = int(urow.account_age_days_at_start + t)
        _col_buf["transaction_id"].append(new_tx_id())
        _col_buf["user_id"].append(int(u))
        _col_buf["timestamp"].append(sample_event_timestamp(t))
        _col_buf["amount"].append(amount)
        _col_buf["merchant_id"].append(m)
        _col_buf["merchant_category"].append(cat)
        _col_buf["device_id"].append(device)
        _col_buf["lat"].append(float(lat))
        _col_buf["lon"].append(float(lon))
        _col_buf["channel"].append(channel)
        _col_buf["account_age_days"].append(event_age)
        _col_buf["is_fraud"].append(0)
        _col_buf["fraud_type"].append("normal")
        _col_buf["case_id"].append(None)
        _col_buf["ring_id"].append(None)
        _col_buf["three_ds_result"].append(three_ds_result)
        _col_buf["three_ds_failures_before_result"].append(failures)
    if (_ui + 1) % _progress_every == 0:
        print(f"[generator] normal: {(_ui + 1):>6d}/{N_USERS} users, {len(_col_buf['transaction_id']):>8d} tx so far", flush=True)
n = len(_col_buf["transaction_id"])
for i in range(n):
    rows.append({c: _col_buf[c][i] for c in _COL_NAMES})
print(f"[generator] normal pass complete: {len(rows):>8d} transactions for {N_USERS} users", flush=True)

fraud_rows = []
generation_log = []

def inject_card_testing(u, utx):
    if len(utx) < 3:
        return
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=10):
        return
    urow = users.loc[u]
    case_id = new_case_id("card_testing")
    if rng.random() < 0.85:
        device = f"dev_{u}_0"
    else:
        device = f"dev_{u}_fraud1"
    burst_size = int(rng.integers(4, 9))
    incrementing = bool(rng.random() < 0.35)
    current = start
    previous_amount = float(rng.uniform(1, 20)) if incrementing else None
    for _ in range(burst_size):
        current += timedelta(days=float(rng.uniform(0.25, 1.2)))
        m = int(rng.choice(merchant_ids))
        if incrementing:
            previous_amount = previous_amount * rng.uniform(1.3, 2.0) + rng.uniform(1, 5)
            amount = float(min(previous_amount, 150))
        else:
            mu, sigma = CAT_PARAMS[cat_lookup[m]]
            amount = float(rng.lognormal(mu, sigma) * rng.uniform(0.5, 1.5))
        lat = urow.home_lat + rng.normal(0, 0.05)
        lon = urow.home_lon + rng.normal(0, 0.05)
        age = int(users.loc[u, "account_age_days_at_start"] + (current - SIM_START).total_seconds() / 86400)
        fraud_rows.append({
            "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": current,
            "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
            "device_id": device, "lat": float(lat), "lon": float(lon), "channel": "ecom",
            "account_age_days": age, "is_fraud": 1, "fraud_type": "card_testing",
            "case_id": case_id, "ring_id": None,
            "three_ds_result": "not_attempted", "three_ds_failures_before_result": 0,
        })
    generation_log.append({
        "case_id": case_id, "fraud_type": "card_testing", "user_id": int(u),
        "burst_size": burst_size, "probing_mode": "incrementing" if incrementing else "independent",
        "device": device,
    })

def inject_auth_bypass(u, utx):
    if len(utx) < 3:
        return
    urow = users.loc[u]
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=10):
        return
    case_id = new_case_id("auth_bypass")
    m = int(rng.choice(merchant_ids))
    failures = int(rng.integers(1, 6))
    amount = float(rng.lognormal(*CAT_PARAMS[cat_lookup[m]]) * rng.uniform(1.5, 4.0))
    if rng.random() < 0.60:
        device = f"dev_{u}_fraud3"
    else:
        device = f"dev_{u}_0"
    if rng.random() < 0.40:
        lat = urow.home_lat + rng.choice([-1, 1]) * rng.uniform(3, 12)
        lon = urow.home_lon + rng.choice([-1, 1]) * rng.uniform(3, 12)
    else:
        lat = urow.home_lat + rng.normal(0, 0.05)
        lon = urow.home_lon + rng.normal(0, 0.05)
    age = int(urow.account_age_days_at_start + (start - SIM_START).total_seconds() / 86400)
    fraud_rows.append({
        "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": start,
        "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
        "device_id": device, "lat": lat, "lon": lon, "channel": "ecom",
        "account_age_days": age, "is_fraud": 1, "fraud_type": "auth_bypass",
        "case_id": case_id, "ring_id": None,
        "three_ds_result": "failed_then_passed", "three_ds_failures_before_result": failures,
    })
    generation_log.append({
        "case_id": case_id, "fraud_type": "auth_bypass", "user_id": int(u),
        "auth_failures_before_success": failures,
        "new_device": device != f"dev_{u}_0",
        "geo_anomaly": abs(lat - urow.home_lat) > 0.5,
    })

def inject_account_takeover(u, utx):
    if len(utx) < 3:
        return
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=20):
        return
    urow = users.loc[u]
    case_id = new_case_id("account_takeover")
    if rng.random() < 0.75:
        device = f"dev_{u}_0"
    else:
        device = f"dev_{u}_fraud2"
    far_lat = urow.home_lat + rng.choice([-1, 1]) * rng.uniform(15, 25)
    far_lon = urow.home_lon + rng.choice([-1, 1]) * rng.uniform(15, 25)
    current = start
    n_tx = int(rng.integers(2, 5))
    for _ in range(n_tx):
        current += timedelta(minutes=int(rng.integers(10, 40)))
        m = int(rng.choice(merchant_ids))
        amount = float(rng.lognormal(*CAT_PARAMS[cat_lookup[m]]) * rng.uniform(1.5, 3.0))
        age = int(urow.account_age_days_at_start + (current - SIM_START).total_seconds() / 86400)
        fraud_rows.append({
            "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": current,
            "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
            "device_id": device, "lat": float(far_lat), "lon": float(far_lon), "channel": "ecom",
            "account_age_days": age, "is_fraud": 1, "fraud_type": "account_takeover",
            "case_id": case_id, "ring_id": None,
            "three_ds_result": "not_attempted", "three_ds_failures_before_result": 0,
        })
    generation_log.append({
        "case_id": case_id, "fraud_type": "account_takeover", "user_id": int(u),
        "device": device, "n_transactions": n_tx,
    })

RING_POOL_MAX_USES = 4
ring_pool = []

def get_bustout_device(next_uid):
    if ring_pool and rng.random() < 0.25:
        idx = int(rng.integers(0, len(ring_pool)))
        entry = ring_pool[idx]
        entry[1] += 1
        device, _, ring_id = entry
        if entry[1] >= RING_POOL_MAX_USES:
            ring_pool.pop(idx)
        return device, ring_id
    device = f"dev_{next_uid}_0"
    ring_id = None
    if rng.random() < 0.40:
        ring_id = f"ring_{next_uid:06d}"
        ring_pool.append([device, 1, ring_id])
    return device, ring_id

def inject_bustout(next_uid):
    lat0 = float(rng.uniform(8.0, 28.0))
    lon0 = float(rng.uniform(72.0, 88.0))
    start_day = float(rng.uniform(5, SIM_DAYS - 5))
    case_id = new_case_id("bustout_identity")
    device, ring_id = get_bustout_device(next_uid)
    current_day = start_day
    n_tx = 0
    base_account_age = int(rng.integers(30, 2800))
    for _ in range(int(rng.integers(15, 30))):
        current_day += float(rng.uniform(0.05, 0.6))
        if current_day >= SIM_DAYS:
            break
        m = int(rng.choice(merchant_ids))
        mu, sigma = CAT_PARAMS[cat_lookup[m]]
        amount = float(rng.lognormal(mu + 1.0, sigma))
        lat = lat0 + rng.normal(0, 0.05)
        lon = lon0 + rng.normal(0, 0.05)
        age = base_account_age + int(current_day - start_day)
        fraud_rows.append({
            "transaction_id": new_tx_id(), "user_id": int(next_uid),
            "timestamp": sample_event_timestamp(current_day), "amount": amount,
            "merchant_id": m, "merchant_category": cat_lookup[m], "device_id": device,
            "lat": float(lat), "lon": float(lon), "channel": "ecom",
            "account_age_days": age, "is_fraud": 1, "fraud_type": "bustout_identity",
            "case_id": case_id, "ring_id": ring_id,
            "three_ds_result": "not_attempted", "three_ds_failures_before_result": 0,
        })
        n_tx += 1
    generation_log.append({
        "case_id": case_id, "fraud_type": "bustout_identity", "user_id": int(next_uid),
        "device": device, "ring_id": ring_id, "n_transactions": n_tx,
    })

def inject_impersonation_case(u, utx, amount_multiplier, urgency="medium", drop_stats=None):
    def _drop(reason):
        if drop_stats is not None:
            drop_stats[reason] = drop_stats.get(reason, 0) + 1
        return None
    try:
        from src.generator.shap_feedback import steer_toward_normal, is_enabled as _shap_on
    except Exception:
        def steer_toward_normal(v, *_a, **_k):
            return v
        def _shap_on():
            return False
    urow = users.loc[u]
    target_day = rng.uniform(0.0, float(SIM_DAYS))
    start = SIM_START + timedelta(days=float(target_day))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=5):
        return _drop("too_close_to_sim_end")
    prior_tx = [r for r in utx if r[0] < start]
    if len(prior_tx) < 2:
        return _drop("insufficient_prior_history")
    m = int(rng.choice(merchant_ids))
    cat = cat_lookup[m]
    typical = float(rng.lognormal(*CAT_PARAMS[cat]))
    amt_range = {"high": (1.5, 2.5), "medium": (1.0, 1.8), "low": (0.8, 1.4)}.get(urgency, (0.8, 1.8))
    amount = typical * rng.uniform(*amt_range)
    if _shap_on():
        amount = steer_toward_normal(amount, "amount", rng, strength=0.5)
    age = int(urow.account_age_days_at_start + target_day)
    if _shap_on():
        age = int(steer_toward_normal(float(age), "account_age_days", rng, strength=0.3))
    new_device_prob = {"high": 0.30, "medium": 0.15, "low": 0.05}.get(urgency, 0.15)
    device_id = f"dev_{u}_new" if rng.random() < new_device_prob else f"dev_{u}_0"
    friction_prob = {"high": 0.35, "medium": 0.20, "low": 0.08}.get(urgency, 0.20)
    if rng.random() < friction_prob:
        three_ds_result = "failed_then_passed"
        three_ds_failures = int(rng.integers(1, 3))
    else:
        three_ds_result = "passed_first_try"
        three_ds_failures = 0
    if rng.random() < 0.12:
        lat = float(urow.home_lat + rng.normal(0, 2.0))
        lon = float(urow.home_lon + rng.normal(0, 2.0))
    else:
        lat = float(urow.home_lat + rng.normal(0, 0.05))
        lon = float(urow.home_lon + rng.normal(0, 0.05))
    return {
        "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": start,
        "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
        "device_id": device_id, "lat": lat, "lon": lon, "channel": "ecom",
        "account_age_days": age, "is_fraud": 1, "fraud_type": "ai_impersonation",
        "case_id": new_case_id("ai_impersonation"), "ring_id": None,
        "three_ds_result": three_ds_result,
        "three_ds_failures_before_result": three_ds_failures,
    }

def inject_synthetic_identity(next_uid):
    lat0 = float(rng.uniform(8.0, 28.0))
    lon0 = float(rng.uniform(72.0, 88.0))
    start_day = float(rng.uniform(5, SIM_DAYS - 10))
    case_id = new_case_id("synthetic_identity")
    if rng.random() < 0.70 and existing_devices:
        device = rng.choice(existing_devices)
    else:
        device = f"dev_synt_{next_uid}"
    account_start_age = int(rng.integers(30, 2800))
    current_day = start_day
    n_tx = 0
    for _ in range(int(rng.integers(18, 30))):
        current_day += float(rng.uniform(0.8, 1.6))
        if current_day >= SIM_DAYS - 3:
            break
        m = int(rng.choice([mid for mid, cat in cat_lookup.items() if cat in ["grocery", "restaurant", "fuel"]]))
        amount = float(rng.lognormal(*CAT_PARAMS[cat_lookup[m]]) * rng.uniform(0.5, 1.2))
        fraud_rows.append({
            "transaction_id": new_tx_id(), "user_id": int(next_uid),
            "timestamp": sample_event_timestamp(current_day), "amount": amount,
            "merchant_id": m, "merchant_category": cat_lookup[m], "device_id": device,
            "lat": lat0 + rng.normal(0, 0.02), "lon": lon0 + rng.normal(0, 0.02), "channel": "ecom",
            "account_age_days": account_start_age + int(current_day - start_day),
            "is_fraud": 1, "fraud_type": "synthetic_identity", "case_id": case_id,
            "ring_id": f"ring_synt_{next_uid}", "three_ds_result": "success", "three_ds_failures_before_result": 0,
        })
        n_tx += 1
    current_day += float(rng.uniform(1.0, 3.0))
    for _ in range(int(rng.integers(8, 15))):
        current_day += float(rng.uniform(0.1, 0.5))
        if current_day >= SIM_DAYS:
            break
        m = int(rng.choice([mid for mid, cat in cat_lookup.items() if cat in ["electronics", "travel", "ecommerce"]]))
        amount = float(rng.lognormal(*CAT_PARAMS[cat_lookup[m]]) * rng.uniform(3.0, 8.0))
        fraud_rows.append({
            "transaction_id": new_tx_id(), "user_id": int(next_uid),
            "timestamp": sample_event_timestamp(current_day), "amount": amount,
            "merchant_id": m, "merchant_category": cat_lookup[m], "device_id": device,
            "lat": lat0 + rng.normal(0, 0.02), "lon": lon0 + rng.normal(0, 0.02), "channel": "ecom",
            "account_age_days": account_start_age + int(current_day - start_day),
            "is_fraud": 1, "fraud_type": "synthetic_identity", "case_id": case_id,
            "ring_id": f"ring_synt_{next_uid}", "three_ds_result": "success", "three_ds_failures_before_result": 0,
        })
        n_tx += 1
    generation_log.append({
        "case_id": case_id, "fraud_type": "synthetic_identity", "user_id": int(next_uid),
        "device": device, "n_transactions": n_tx,
    })

def inject_bnpl_abuse(next_uid):
    lat0 = float(rng.uniform(8.0, 28.0))
    lon0 = float(rng.uniform(72.0, 88.0))
    start_day = float(rng.uniform(5, SIM_DAYS - 5))
    case_id = new_case_id("bnpl_abuse")
    if existing_devices:
        device = rng.choice(existing_devices)
    else:
        device = f"dev_bnpl_{next_uid}"
    account_start_age = int(rng.integers(30, 2800))
    current_day = start_day
    n_tx = 0
    for _ in range(int(rng.integers(10, 25))):
        current_day += float(rng.uniform(0.25, 1.2))
        if current_day >= SIM_DAYS:
            break
        m = int(rng.choice([mid for mid, cat in cat_lookup.items() if cat in ["electronics", "clothing", "ecommerce"]]))
        amount = float(rng.lognormal(*CAT_PARAMS[cat_lookup[m]]) * rng.uniform(2.5, 6.0))
        fraud_rows.append({
            "transaction_id": new_tx_id(), "user_id": int(next_uid),
            "timestamp": sample_event_timestamp(current_day), "amount": amount,
            "merchant_id": m, "merchant_category": cat_lookup[m], "device_id": device,
            "lat": lat0 + rng.normal(0, 0.01), "lon": lon0 + rng.normal(0, 0.01), "channel": "ecom",
            "account_age_days": account_start_age + int(current_day - start_day),
            "is_fraud": 1, "fraud_type": "bnpl_abuse", "case_id": case_id,
            "ring_id": f"ring_bnpl_{next_uid}", "three_ds_result": "success", "three_ds_failures_before_result": 0,
        })
        n_tx += 1
    generation_log.append({
        "case_id": case_id, "fraud_type": "bnpl_abuse", "user_id": int(next_uid),
        "device": device, "n_transactions": n_tx,
    })

base_df = pd.DataFrame(rows).sort_values(["user_id", "timestamp"]).reset_index(drop=True)
user_history = {int(u): list(zip(group["timestamp"], group["amount"])) for u, group in base_df.groupby("user_id")}

eligible_users = {int(u): utx for u, utx in user_history.items() if len(utx) >= 3}

_card_n = pool_size_for("card_testing")
card_testing_pool = rng.choice(
    np.array(sorted(eligible_users)), size=min(_card_n, len(eligible_users)), replace=False
)
card_testing_user_ids = set(card_testing_pool)
for u in card_testing_user_ids:
    inject_card_testing(int(u), eligible_users[int(u)])

remaining_for_takeover = np.array([u for u in sorted(eligible_users) if u not in card_testing_user_ids])
_at_n = pool_size_for("account_takeover")
account_takeover_user_ids = rng.choice(
    remaining_for_takeover, size=min(_at_n, len(remaining_for_takeover)), replace=False
)
for u in account_takeover_user_ids:
    inject_account_takeover(int(u), eligible_users[int(u)])

used_so_far = set(card_testing_user_ids) | set(account_takeover_user_ids)
remaining_for_auth = np.array([u for u in sorted(eligible_users) if u not in used_so_far])
_ab_n = pool_size_for("auth_bypass")
auth_bypass_user_ids = rng.choice(
    remaining_for_auth, size=min(_ab_n, len(remaining_for_auth)), replace=False
)
for u in auth_bypass_user_ids:
    inject_auth_bypass(int(u), eligible_users[int(u)])

_bust_n = pool_size_for("bustout_identity")
next_uid = N_USERS
for _ in range(_bust_n):
    inject_bustout(next_uid)
    next_uid += 1
next_uid = N_USERS + 1000
_si_n = pool_size_for("synthetic_identity")
for _ in range(_si_n):
    inject_synthetic_identity(next_uid)
    next_uid += 1
_bn_n = pool_size_for("bnpl_abuse")
for _ in range(_bn_n):
    inject_bnpl_abuse(next_uid)
    next_uid += 1
print(f"[generator] done. Total fraud cases: {len(fraud_rows)}")

all_rows = rows + fraud_rows
df = pd.DataFrame(all_rows)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

out_dir = Path("data/raw")
out_dir.mkdir(parents=True, exist_ok=True)
df.to_csv(out_dir / "transactions.csv", index=False)
try:
    df.to_parquet(out_dir / "transactions.parquet", index=False)
except Exception as e:
    print(f"[warn] parquet write skipped: {e}")
pd.DataFrame(generation_log).to_csv(out_dir / "generation_log.csv", index=False)

print(df.shape)
print(df["is_fraud"].mean())
print(df["fraud_type"].value_counts())
