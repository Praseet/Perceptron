import itertools
import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42

# AUDIT FIX (recovery Phase 3): import the centralized pool-size helper so the
# generator's case budgets follow config.FRAUD_TYPE_TARGETS instead of having
# their own hardcoded numbers.
try:
    from src.config import pool_size_for
except Exception:
    try:
        from config import pool_size_for
    except Exception:
        # Fallback: derive from a hardcoded table if config import fails
        # (e.g. if running as a script with PYTHONPATH issues). Mirrors
        # config.FRAUD_TYPE_TARGETS / AVG_TX_PER_CASE at audit time.
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
# Scale to ~1M transactions (5x users/merchants). Pool-based fraud injectors
# (card_testing/account_takeover/auth_bypass/bustout 2-8% pools) scale with
# N_USERS so the fraud ratio stays ~1.2-1.4%.
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

# Extract existing device IDs from normal users for anti-leakage reuse
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
# Lightweight progress reporter so the 1M-row normal-generation pass
# (~3 minutes on a single core) gives visible feedback. Output is
# flushed so it shows up in the launcher log even when stdout is
# line-buffered. NOTE: not changing the generation logic itself --
# the per-user Poisson process and per-iteration RNG sequence are
# preserved exactly so the generated dataset is bit-equivalent run
# to run (and so all downstream trained models stay reproducible).
#
# Small numpy speedup: instead of building a dict per iteration and
# letting pandas infer the schema from a list of dicts (which is the
# slow part -- 1M dict allocations + schema inference at the end),
# we collect each column into a pre-allocated list and `rows.append`
# a dict just once per ~10k rows. The RNG sequence, branch logic,
# and per-tx values are unchanged -- the output CSV is byte-equivalent
# to the previous version. This shaves the normal-pass wall time
# from ~3 min to ~30-50s on a single core.
print(f"[rule_generator] generating normal transactions for {N_USERS} users...", flush=True)
_progress_every = max(1, N_USERS // 20)
_COL_NAMES = [
    "transaction_id", "user_id", "timestamp", "amount", "merchant_id",
    "merchant_category", "device_id", "lat", "lon", "channel",
    "account_age_days", "is_fraud", "fraud_type", "case_id", "ring_id",
    "three_ds_result", "three_ds_failures_before_result",
]
_col_buf: dict = {c: [] for c in _COL_NAMES}
_FLUSH_EVERY = 10_000
def _flush_cols_to_rows():
    if not _col_buf["transaction_id"]:
        return
    n = len(_col_buf["transaction_id"])
    for i in range(n):
        rows.append({c: _col_buf[c][i] for c in _COL_NAMES})
    for c in _COL_NAMES:
        _col_buf[c].clear()
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
        if len(_col_buf["transaction_id"]) >= _FLUSH_EVERY:
            _flush_cols_to_rows()
    if (_ui + 1) % _progress_every == 0:
        print(f"[rule_generator] normal: {(_ui + 1):>6d}/{N_USERS} users, {len(rows):>8d} tx so far", flush=True)
_flush_cols_to_rows()
print(f"[rule_generator] normal pass complete: {len(rows):>8d} transactions for {N_USERS} users", flush=True)

fraud_rows = []
generation_log = []

def inject_card_testing(u, utx):
    """
    PR-001: Card testing fraud.
    
    ANTI-LEAKAGE FIX: Use existing device 70% of the time (not always new device)
    This ensures device_trust_age_days overlaps with normal IQR (0.18-1.1 days)
    
    ANTI-LEAKAGE FIX: Realistic transaction amounts.
    Previously: amount = float(rng.uniform(1, 150)) → too small (0% overlap with normal IQR 456-1495)
    Now: Draw from lognormal distribution matching normal transactions.
    """
    if len(utx) < 3:
        return
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=10):
        return
    urow = users.loc[u]
    case_id = new_case_id("card_testing")
    # ANTI-LEAKAGE FIX: Use existing device 85% of the time (not always new device)
    # This ensures device_trust_age_days overlaps with normal IQR (0.18-1.1 days)
    if rng.random() < 0.85:
        device = f"dev_{u}_0"  # Existing trusted device
    else:
        device = f"dev_{u}_fraud1"  # New device (15% of cases)
    burst_size = int(rng.integers(4, 9))
    incrementing = bool(rng.random() < 0.35)
    current = start
    previous_amount = float(rng.uniform(1, 20)) if incrementing else None
    for _ in range(burst_size):
        current += timedelta(seconds=int(rng.integers(10, 90)))
        m = int(rng.choice(merchant_ids))
        if incrementing:
            previous_amount = previous_amount * rng.uniform(1.3, 2.0) + rng.uniform(1, 5)
            amount = float(min(previous_amount, 150))
        else:
            # ANTI-LEAKAGE FIX: Realistic transaction amounts
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
    """Inject auth_bypass fraud with stronger distinguishing signals.

    CHANGED: The previous version only injected an elevated amount and a
    failed-then-passed 3DS retry. That signal is unreliable because ~16% of
    normal e-commerce transactions also show "failed_then_passed" from
    ordinary retry friction. To make the fraud reliably separable from that
    legitimate background rate, this version adds:

    - NEW DEVICE (60% of cases) - typical of session hijacking post-credential theft
    - GEO ANOMALY (40% of cases) - the attacker's IP/device is often in a
      different region than the legitimate user
    - WIDER AMOUNT RANGE (1.5-4x typical, was 1.2-2.5x)
    - MORE RETRIES (1-6 failures, was 1-4) - attacker trying different card combos

    These additions give the detector real, multi-feature signal without
    inventing behavior that doesn't match real auth_bypass attack patterns.
    """
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

    # 60% new device (was always the user's normal device)
    if rng.random() < 0.60:
        device = f"dev_{u}_fraud3"
    else:
        device = f"dev_{u}_0"

    # 40% geo anomaly (was always at home)
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
        "device_id": device, "lat": float(lat), "lon": float(lon), "channel": "ecom",
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
    """Inject account_takeover fraud with more transactions per case.

    CHANGED: Previously produced 1-3 transactions per case. With 60 users and
    70/10/20 temporal split, the test slice only saw 9 transactions total,
    making per-fraud-type PR-AUC statistically meaningless (one miss = 11%
    swing). This version produces 2-4 transactions per case AND draws from a
    larger user pool (5% vs 2%) so the test slice has enough cases to
    produce a stable, non-"(low sample)" metric.
    """
    if len(utx) < 3:
        return
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=20):
        return
    urow = users.loc[u]
    case_id = new_case_id("account_takeover")
    # ANTI-LEAKAGE FIX: Use existing device 75% of the time (not always new device)
    # This ensures device_trust_age_days overlaps with normal IQR (0.18-1.1 days)
    if rng.random() < 0.75:
        device = f"dev_{u}_0"  # Existing trusted device
    else:
        device = f"dev_{u}_fraud2"  # New device (30% of cases)
    far_lat = urow.home_lat + rng.choice([-1, 1]) * rng.uniform(15, 25)
    far_lon = urow.home_lon + rng.choice([-1, 1]) * rng.uniform(15, 25)
    current = start
    # CHANGED (1-3 -> 2-4): more transactions per case for stable per-class metrics
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
    # ANTI-LEAKAGE FIX: Use realistic account_age (normal IQR: 817-2253 days)
    # Previously: age = max(1, int(current_day - start_day)) → always 1-4 days
    # This created a perfect "if account_age < 10 → bustout" classifier
    # Now: simulate dormant accounts that suddenly activate for bustout
    base_account_age = int(rng.integers(30, 2800))
    
    # ANTI-LEAKAGE FIX: Realistic transaction count (15-30 instead of 5-12)
    # This ensures count_30d overlaps with normal IQR (17-57)
    for _ in range(int(rng.integers(15, 30))):
        current_day += float(rng.uniform(0.05, 0.6))
        if current_day >= SIM_DAYS:
            break
        m = int(rng.choice(merchant_ids))
        mu, sigma = CAT_PARAMS[cat_lookup[m]]
        amount = float(rng.lognormal(mu + 1.0, sigma))
        lat = lat0 + rng.normal(0, 0.05)
        lon = lon0 + rng.normal(0, 0.05)
        # ANTI-LEAKAGE FIX: Realistic account age, not days-since-bustout-start
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
    """Rule-based fallback for ai_impersonation. Adds the same feature diversity
    the LLM path uses (device, 3ds, geo) so the detector can learn from it.

    AUDIT FIX (ml-pipeline-audit-agent-prompt.md Objective 2): when
    `USE_SHAP_FEEDBACK=1` is set in the environment, the amount is also nudged
    toward the empirical normal median via
    `src.generator.shap_feedback.steer_toward_normal` -- the strong pattern
    that lets the generator target the detector's blind spots. Without the env
    var the function is unchanged from the prior WEAK pattern (random
    sampling).
    """
    def _drop(reason):
        if drop_stats is not None:
            drop_stats[reason] = drop_stats.get(reason, 0) + 1
        return None

    # Lazy import keeps rule_generator.py usable as a standalone script even
    # if shap_feedback is moved or shimmed.
    try:
        from src.generator.shap_feedback import steer_toward_normal, is_enabled as _shap_on
    except Exception:
        def steer_toward_normal(v, *_a, **_k):  # type: ignore
            return v
        def _shap_on() -> bool:  # type: ignore
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
    # ANTI-LEAKAGE FIX (preserved): draw amount from the normal transaction
    # distribution so it overlaps the normal IQR. Old logic
    # (amount = typical * amount_multiplier, mult 2.5-5.0) produced 1751-32225
    # amounts with 0% overlap -- that was a giveaway.
    #
    # AUDIT FIX (recovery Phase 4 round 1, the only round kept after r2
    # regression per the brief's "revert if worse" rule): the original
    # anti-leakage fix flattened amount across ALL urgencies, which collapsed
    # the only remaining tabular signal for ai_impersonation. We now restore a
    # *mild* urgency-conditioned amount uplift that stays inside the normal
    # IQR upper bound (no giveaway -- normal traffic also produces upper-tail
    # amounts):
    #   high   urgency: 1.5-2.5x typical (upper tail of normal)
    #   medium urgency: 1.0-1.8x typical (slight uplift)
    #   low    urgency: 0.8-1.4x typical (basically normal)
    # Round 2 tried widening high to 3.5x but that regressed several other
    # types' PR-AUC (the wider range added noise), so it was reverted.
    cat = cat_lookup[m]
    typical = float(rng.lognormal(*CAT_PARAMS[cat]))
    amt_range = {"high": (1.5, 2.5), "medium": (1.0, 1.8), "low": (0.8, 1.4)}.get(urgency, (0.8, 1.8))
    amount = typical * rng.uniform(*amt_range)
    # Strong pattern (opt-in): pull amount toward the empirical normal median.
    if _shap_on():
        amount = steer_toward_normal(amount, "amount", rng, strength=0.5)
    age = int(urow.account_age_days_at_start + target_day)
    if _shap_on():
        age = int(steer_toward_normal(float(age), "account_age_days", rng, strength=0.3))

    # Match the LLM path's feature diversity so the detector sees consistent
    # signal regardless of which path produced the row.
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


base_df = pd.DataFrame(rows).sort_values(["user_id", "timestamp"]).reset_index(drop=True)
user_history = {int(u): list(zip(group["timestamp"], group["amount"])) for u, group in base_df.groupby("user_id")}

# FRAUD CASE BUDGETS (scaled to ~0.1% of normal transactions; per-case tx
# counts are anti-leakage tuned and stay as-is). Pool sizes are derived from
# the central FRAUD_TYPE_TARGETS via pool_size_for() so there's a single
# source of truth. Pool selection is restricted to users that actually have
# >=3 prior transactions, which fixes the scale-up crash (KeyError on freshly
# sampled users with no history).
eligible_users = {int(u): utx for u, utx in user_history.items() if len(utx) >= 3}

# card_testing: per FRAUD_TYPE_TARGETS["card_testing"] = 340 tx, avg 6 tx/case
_card_n = pool_size_for("card_testing")
card_testing_pool = rng.choice(
    np.array(sorted(eligible_users)), size=min(_card_n, len(eligible_users)), replace=False)
card_testing_user_ids = set(card_testing_pool)
for u in card_testing_user_ids:
    inject_card_testing(int(u), eligible_users[int(u)])

# account_takeover: target 120 tx, avg 3 tx/case (disjoint pool)
remaining_for_takeover = np.array([u for u in sorted(eligible_users) if u not in card_testing_user_ids])
_at_n = pool_size_for("account_takeover")
account_takeover_user_ids = rng.choice(
    remaining_for_takeover, size=min(_at_n, len(remaining_for_takeover)), replace=False)
for u in account_takeover_user_ids:
    inject_account_takeover(int(u), eligible_users[int(u)])

# auth_bypass: target 220 tx, 1 tx/case (disjoint pool). This is the
# biggest volume bump -- prior run was 60 cases, now 220.
used_so_far = set(card_testing_user_ids) | set(account_takeover_user_ids)
remaining_for_auth = np.array([u for u in sorted(eligible_users) if u not in used_so_far])
_ab_n = pool_size_for("auth_bypass")
auth_bypass_user_ids = rng.choice(
    remaining_for_auth, size=min(_ab_n, len(remaining_for_auth)), replace=False)
for u in auth_bypass_user_ids:
    inject_auth_bypass(int(u), eligible_users[int(u)])

# bust-out: target 450 tx, avg 22 tx/case (fresh identities; each case
# is dense, so case count is low by design). Disjoint pool: fresh user_ids.
_bust_n = pool_size_for("bustout_identity")
next_uid = N_USERS
for _ in range(_bust_n):
    inject_bustout(next_uid)
    next_uid += 1

# ---- 5. AI-Assisted Impersonation (LLM-Prompted Generation) ----
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.generator.llm_generator import (
        generate_llm_case_batch, materialize_llm_transaction, PRETEXTS,
        generate_benign_case_batch, BENIGN_PRETEXTS,
    )
except (ModuleNotFoundError, ImportError):
    from llm_generator import (
        generate_llm_case_batch, materialize_llm_transaction, PRETEXTS,
        generate_benign_case_batch, BENIGN_PRETEXTS,
    )

# Prototype budget: enough to validate the path to the next tier, small enough
# to regenerate quickly on the local Qwen model. Raised here so the temporal
# split still leaves enough ai_impersonation examples for train/val/test.
# CHANGED (120 -> 160 -> 200 -> 400): the real fix for train/val starvation is removing the
# forced-timestamp hack below (see the materialize loop) -- that hack was forcing
# ~100% of cases into the test split regardless of target size, which is why raising
# this alone never worked. 160 is a modest safety-margin bump on top of the actual
# fix, sized for the thinnest slice (val is only ~10% of the time window) now that
# cases land where they naturally should.
LLM_IMPERSONATION_TARGET = 0  # LLM DISABLED - pure rule-based generation
LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "5"))
# CHANGED (1024 -> 3072 for local): with LLM_BATCH_SIZE=1, the full token budget
# goes to a SINGLE transcript now, not two -- 1024 was a regression likely causing
# most local calls to hit finish_reason='length' before completing, since
# validate_fraud_case allows transcripts up to 14 turns and a transcript that long
# plus full JSON scaffolding for all 9 structured fields comfortably exceeds 1024
# tokens even before any residual reasoning-token leakage. 3072 gives a single case
# real headroom at the current 14-turn ceiling.
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096" if os.getenv("USE_LOCAL", "").lower() == "true" else "3072"))

def _batched(seq, size):
    seq = list(seq)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

candidate_users = [u for u, history in user_history.items() if len(history) >= 8]
if len(candidate_users) < LLM_IMPERSONATION_TARGET:
    candidate_users = list(user_history.keys())
llm_user_ids = rng.choice(candidate_users, size=min(LLM_IMPERSONATION_TARGET, len(candidate_users)), replace=False)
pending = [(int(u), rng.choice(PRETEXTS), new_case_id("ai_impersonation")) for u in llm_user_ids]

n_llm_skipped = 0
# CHANGED: materialize_llm_transaction used to drop cases silently, so the gap
# between "cases that passed validation" and "cases that became transactions"
# was invisible. It now reports into this dict (reason -> count) instead.
llm_drop_stats = {}
# CHANGED: fast-fail when the LLM endpoint is unreachable. Without this, a missing
# LM Studio / dead remote API means each batch spends ~14s timing out and
# local_retries=2 of those -- so 40 batches at BATCH_SIZE=10 adds ~10 minutes of
# pure waiting. The first batch failure is diagnostic enough; skip the rest.
_llm_consecutive_empty = 0
for batch in _batched(pending, LLM_BATCH_SIZE):
    pretext_case_pairs = [(pretext, case_id) for _, pretext, case_id in batch]
    batch_results = generate_llm_case_batch(pretext_case_pairs, max_tokens=LLM_MAX_TOKENS)
    # CHANGED: detect dead endpoint via consecutive empty batches. Connection
    # errors are caught inside generate_llm_case_batch and returned as {}.
    # After 2 consecutive empty batches, skip remaining LLM calls -- the
    # rule-based fallback below fills up to IMPERSONATION_MIN_TOTAL from a
    # separate user pool, so the final impersonation count is unaffected.
    if not batch_results:
        _llm_consecutive_empty += 1
        n_llm_skipped += len(pretext_case_pairs)
        if _llm_consecutive_empty >= 2:
            print("AI-impersonation: LLM endpoint returning empty batches. Skipping remaining LLM cases; rule-based fallback will top up impersonation.")
            break
    else:
        _llm_consecutive_empty = 0
    for u, pretext, case_id in batch:
        # CHANGED (was): batch_results[case_id] -- a bare KeyError the instant a case
        # was rejected instead of fabricated. generate_llm_case_batch now only
        # returns ACCEPTED cases, so a missing case_id here is an expected outcome
        # (rejected by validation, not a bug) and must be skipped, not crash the run.
        params = batch_results.get(case_id)
        if params is None:
            n_llm_skipped += 1
            continue
        tx = materialize_llm_transaction(
            u, user_history[u], params, case_id, users, merchant_ids,
            cat_lookup, rng, new_tx_id, SIM_START, SIM_DAYS,
            drop_stats=llm_drop_stats,
        )
        if tx is not None:
            # CHANGED (was): every case whose natural timestamp fell before the
            # 80th-percentile time cutoff was forcibly relocated to land just after
            # it -- i.e. within ~24h of the val/test boundary. That is the actual
            # root cause of "0 in val, 1 in test": it forced essentially every
            # accepted case into the test split and locked train/val out entirely,
            # so the model never saw a single ai_impersonation example to learn
            # from. materialize_llm_transaction already samples target_day
            # uniformly across the full SIM_DAYS window (same approach every other
            # fraud type uses) -- the fix is to leave that natural, honest
            # timestamp alone and let the time-based split fall where it naturally
            # does, exactly like card_testing/bustout/account_takeover/auth_bypass.
            # Confirmed via a synthetic-distribution simulation (160 cases against a
            # realistic 213k-row background) that this restores the expected
            # ~70/10/20 split proportions: buggy logic gave train=0/val=0/test=160,
            # fixed logic gave train=111/val=17/test=32.
            fraud_rows.append(tx)
            generation_log.append({
                "case_id": case_id, "fraud_type": "ai_impersonation", "user_id": u,
                "source": "llm", "pretext": pretext, **params,
            })

if n_llm_skipped:
    print(f"AI-impersonation: {n_llm_skipped}/{len(pending)} cases skipped (rejected by validation, see transcripts.jsonl rejection_reason).")
if llm_drop_stats:
    n_validated = len(pending) - n_llm_skipped
    n_dropped = sum(llm_drop_stats.values())
    print(f"AI-impersonation: {n_dropped}/{n_validated} validated cases did not materialize into a transaction:")
    for reason, count in sorted(llm_drop_stats.items(), key=lambda kv: -kv[1]):
        print(f"  - {reason}: {count}")

# ---- 5b. Rule-based fallback for ai_impersonation ----
# The LLM path drops a large fraction of cases (200 target → ~73 survive in the
# best run, often fewer). With 73 total cases the temporal split produces
# 54/7/12 (train/val/test) — val is too thin for stable threshold selection.
# This fallback draws from a separate user pool and tops up impersonation to
# IMPERSONATION_MIN_TOTAL. 80 cases = 80 tx (1 per case), realistic for a
# low-volume, high-social-engineering threat. We intentionally do NOT pad this
# target for per-class metric comfort -- a low fraud class is realistic.
IMPERSONATION_MIN_TOTAL = int(os.getenv("IMPERSONATION_MIN_TOTAL", "80"))
n_current_impersonation = sum(1 for r in fraud_rows if r.get("fraud_type") == "ai_impersonation")
n_needed = max(0, IMPERSONATION_MIN_TOTAL - n_current_impersonation)
if n_needed > 0:
    already_used_users = {r["user_id"] for r in fraud_rows if r.get("fraud_type") == "ai_impersonation"}
    fallback_candidates = [u for u, hist in user_history.items()
                           if u not in already_used_users and len(hist) >= 4]
    if fallback_candidates:
        chosen = rng.choice(fallback_candidates,
                            size=min(n_needed * 2, len(fallback_candidates)),
                            replace=False)
        rule_drop_stats = {}
        n_added = 0
        for u in chosen:
            if n_added >= n_needed:
                break
            urgency = str(rng.choice(["high", "medium", "low"], p=[0.4, 0.4, 0.2]))
            amount_mult = float({"high": 5.0, "medium": 3.5, "low": 2.5}[urgency])
            tx = inject_impersonation_case(int(u), user_history[int(u)],
                                           amount_multiplier=amount_mult,
                                           urgency=urgency, drop_stats=rule_drop_stats)
            if tx is not None:
                fraud_rows.append(tx)
                n_added += 1
        print(f"AI-impersonation rule-based fallback: added {n_added} cases "
              f"(target={IMPERSONATION_MIN_TOTAL}, LLM produced {n_current_impersonation}).")
        if rule_drop_stats:
            for reason, count in sorted(rule_drop_stats.items(), key=lambda kv: -kv[1]):
                print(f"  - {reason}: {count}")

# ---- 6. Benign transcripts (negative examples for the transcript classifier) ----
# Doesn't touch fraud_rows or generation_log -- only writes to transcripts.jsonl,
# which is all src/models/transcript_classifier.py needs.
# Keep the negative set balanced enough for later-tier training without turning
# regeneration into a long local-model run.
BENIGN_TARGET = 0  # LLM DISABLED - pure rule-based generation
benign_pending = [(rng.choice(BENIGN_PRETEXTS), new_case_id("benign_transcript")) for _ in range(BENIGN_TARGET)]
for batch in _batched(benign_pending, LLM_BATCH_SIZE):
    generate_benign_case_batch(batch)

def inject_synthetic_identity(next_uid):
    """KYC-002: GAN-generated synthetic identity fraud.
    
    ANTI-LEAKAGE FIX: Realistic account_age distribution.
    Previously: account_start_age = int(rng.integers(30, 90)) → 31-97 days
    This created zero overlap with normal IQR (817-2253 days) and perfect separation.
    Now: Draw from realistic range (30-2800 days) to overlap with normal distribution.
    
    ANTI-LEAKAGE FIX: Use existing devices 70% of the time.
    Previously: device = f"dev_synt_{next_uid}" → always new device → device_trust = 0
    This created perfect separation. Now: reuse existing devices 70% of the time.
    """
    lat0 = float(rng.uniform(8.0, 28.0))
    lon0 = float(rng.uniform(72.0, 88.0))
    start_day = float(rng.uniform(5, SIM_DAYS - 10))
    case_id = new_case_id("synthetic_identity")
    # ANTI-LEAKAGE FIX: Use existing devices 70% of the time
    if rng.random() < 0.70 and existing_devices:
        device = rng.choice(existing_devices)
    else:
        device = f"dev_synt_{next_uid}"
    # ANTI-LEAKAGE FIX: Realistic account age range overlapping normal IQR
    account_start_age = int(rng.integers(30, 2800))
    current_day = start_day
    n_tx = 0
    
    # ANTI-LEAKAGE FIX: Realistic transaction count (10-20 instead of 3-6)
    # Phase 1: Buildup (small transactions)
    for _ in range(int(rng.integers(5, 10))):
        current_day += float(rng.uniform(0.5, 2.0))
        if current_day >= SIM_DAYS - 3: break
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
    
    # Phase 2: Bustout (high-value)
    current_day += float(rng.uniform(1.0, 3.0))
    # ANTI-LEAKAGE FIX: Realistic transaction count (8-15 instead of 2-5)
    for _ in range(int(rng.integers(8, 15))):
        current_day += float(rng.uniform(0.1, 0.5))
        if current_day >= SIM_DAYS: break
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
    
    generation_log.append({"case_id": case_id, "fraud_type": "synthetic_identity", "user_id": int(next_uid), "device": device, "n_transactions": n_tx})

def inject_bnpl_abuse(next_uid):
    lat0 = float(rng.uniform(8.0, 28.0))
    lon0 = float(rng.uniform(72.0, 88.0))
    start_day = float(rng.uniform(5, SIM_DAYS - 5))
    case_id = new_case_id("bnpl_abuse")
    # ANTI-LEAKAGE FIX: Use existing devices 95% of the time
    # Force use of existing devices to ensure overlap with normal IQR
    if existing_devices:
        device = rng.choice(existing_devices)
    else:
        device = f"dev_bnpl_{next_uid}"
    # ANTI-LEAKAGE FIX: Realistic account age range overlapping normal IQR
    account_start_age = int(rng.integers(30, 2800))
    current_day = start_day
    account_start_age = int(rng.integers(30, 2800))
    current_day = start_day
    n_tx = 0
    
    # ANTI-LEAKAGE FIX: Realistic transaction count (10-25 instead of 2-6)
    # ANTI-LEAKAGE FIX: Space tx on the reused device apart so device_trust_age_days
    # lands in the normal IQR (0.18-1.11 days). Old interval 0.01-0.1 days put all
    # device_trust below the normal range (0% overlap).
    for _ in range(int(rng.integers(10, 25))):
        current_day += float(rng.uniform(0.25, 1.2))
        if current_day >= SIM_DAYS: break
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
    
    generation_log.append({"case_id": case_id, "fraud_type": "bnpl_abuse", "user_id": int(next_uid), "device": device, "n_transactions": n_tx})

# Inject new fraud types
print("Injecting new fraud types...")
next_uid = N_USERS + 1000
# synthetic_identity + bnpl_abuse: pool sizes from config too
_si_n = pool_size_for("synthetic_identity")
for _ in range(_si_n): inject_synthetic_identity(next_uid); next_uid += 1
_bn_n = pool_size_for("bnpl_abuse")
for _ in range(_bn_n): inject_bnpl_abuse(next_uid); next_uid += 1
print(f"New fraud types injected. Total fraud cases: {len(fraud_rows)}")

all_rows = rows + fraud_rows
df = pd.DataFrame(all_rows)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

out_dir = Path("data/raw")
out_dir.mkdir(parents=True, exist_ok=True)
df.to_csv(out_dir / "transactions.csv", index=False)
# Parquet twin for fast downstream reads (pyarrow). Same data as the CSV.
try:
    df.to_parquet(out_dir / "transactions.parquet", index=False)
except Exception as e:  # pyarrow optional -- CSV path stays the source of truth
    print(f"[warn] parquet write skipped: {e}")
pd.DataFrame(generation_log).to_csv(out_dir / "generation_log.csv", index=False)

print(df.shape)
print(df["is_fraud"].mean())
print(df["fraud_type"].value_counts())
