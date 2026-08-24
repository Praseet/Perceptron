import itertools
import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

SIM_START = datetime(2026, 1, 1)
SIM_DAYS = 60
N_USERS = 3000
N_MERCHANTS = 250

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
for u in user_ids:
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
        rows.append({
            "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": sample_event_timestamp(t),
            "amount": amount, "merchant_id": m, "merchant_category": cat, "device_id": device,
            "lat": float(lat), "lon": float(lon), "channel": channel, "account_age_days": event_age,
            "is_fraud": 0, "fraud_type": "normal", "case_id": None, "ring_id": None,
            "three_ds_result": three_ds_result, "three_ds_failures_before_result": failures,
        })

fraud_rows = []
generation_log = []

def inject_card_testing(u, utx):
    if len(utx) < 3:
        return
    anchor = utx[int(rng.integers(1, max(2, int(len(utx) * 0.7))))][0]
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=10):
        return
    urow = users.loc[u]
    case_id = new_case_id("card_testing")
    device = f"dev_{u}_fraud1"
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
            amount = float(rng.uniform(1, 150))
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
    anchor = utx[int(rng.integers(1, max(2, int(len(utx) * 0.7))))][0]
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=10):
        return
    case_id = new_case_id("auth_bypass")
    m = int(rng.choice(merchant_ids))
    failures = int(rng.integers(1, 4))
    amount = float(rng.lognormal(*CAT_PARAMS[cat_lookup[m]]) * rng.uniform(1.2, 2.5))
    lat = urow.home_lat + rng.normal(0, 0.05)
    lon = urow.home_lon + rng.normal(0, 0.05)
    age = int(urow.account_age_days_at_start + (start - SIM_START).total_seconds() / 86400)
    fraud_rows.append({
        "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": start,
        "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
        "device_id": f"dev_{u}_0", "lat": float(lat), "lon": float(lon), "channel": "ecom",
        "account_age_days": age, "is_fraud": 1, "fraud_type": "auth_bypass",
        "case_id": case_id, "ring_id": None,
        "three_ds_result": "failed_then_passed", "three_ds_failures_before_result": failures,
    })
    generation_log.append({
        "case_id": case_id, "fraud_type": "auth_bypass", "user_id": int(u),
        "auth_failures_before_success": failures,
    })

def inject_account_takeover(u, utx):
    if len(utx) < 3:
        return
    anchor = utx[int(rng.integers(1, max(2, int(len(utx) * 0.7))))][0]
    start = anchor + timedelta(minutes=int(rng.integers(30, 300)))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=20):
        return
    urow = users.loc[u]
    case_id = new_case_id("account_takeover")
    device = f"dev_{u}_fraud2"
    far_lat = urow.home_lat + rng.choice([-1, 1]) * rng.uniform(15, 25)
    far_lon = urow.home_lon + rng.choice([-1, 1]) * rng.uniform(15, 25)
    current = start
    n_tx = int(rng.integers(1, 3))
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
    for _ in range(int(rng.integers(5, 12))):
        current_day += float(rng.uniform(0.05, 0.6))
        if current_day >= SIM_DAYS:
            break
        m = int(rng.choice(merchant_ids))
        mu, sigma = CAT_PARAMS[cat_lookup[m]]
        amount = float(rng.lognormal(mu + 1.0, sigma))
        lat = lat0 + rng.normal(0, 0.05)
        lon = lon0 + rng.normal(0, 0.05)
        age = max(1, int(current_day - start_day))
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

def inject_impersonation_case(u, utx, amount_multiplier):
    urow = users.loc[u]
    target_day = rng.uniform(0.0, float(SIM_DAYS))
    start = SIM_START + timedelta(days=float(target_day))
    if start >= SIM_START + timedelta(days=SIM_DAYS) - timedelta(minutes=5):
        return None
    prior_tx = [r for r in utx if r[0] < start]
    if len(prior_tx) < 2:
        return None
    case_id = new_case_id("ai_impersonation")
    m = int(rng.choice(merchant_ids))
    typical = float(np.mean([r[1] for r in prior_tx]))
    amount = float(typical * amount_multiplier)
    age = int(urow.account_age_days_at_start + target_day)
    return {
        "transaction_id": new_tx_id(), "user_id": int(u), "timestamp": start,
        "amount": amount, "merchant_id": m, "merchant_category": cat_lookup[m],
        "device_id": f"dev_{u}_0", "lat": float(urow.home_lat + rng.normal(0, 0.05)),
        "lon": float(urow.home_lon + rng.normal(0, 0.05)), "channel": "ecom",
        "account_age_days": age, "is_fraud": 1, "fraud_type": "ai_impersonation",
        "case_id": case_id, "ring_id": None,
        "three_ds_result": "passed_first_try", "three_ds_failures_before_result": 0,
    }


base_df = pd.DataFrame(rows).sort_values(["user_id", "timestamp"]).reset_index(drop=True)
user_history = {int(u): list(zip(group["timestamp"], group["amount"])) for u, group in base_df.groupby("user_id")}

# card testing / auth bypass / account takeover: unchanged from the PDF, ~2% of users each
fraud_user_ids = rng.choice(user_ids, size=max(1, int(0.02 * N_USERS)), replace=False)
for u in fraud_user_ids:
    utx = user_history[int(u)]
    inject_card_testing(int(u), utx)
    inject_auth_bypass(int(u), utx)
    inject_account_takeover(int(u), utx)

# bust-out: unchanged, fresh identities
next_uid = N_USERS
for _ in range(max(1, int(0.02 * N_USERS))):
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

# CHANGED: batched instead of one API call per case.
# LLM_BATCH_SIZE cases now share a single call. At LLM_IMPERSONATION_TARGET=60 and
# batch size 3 that's 20 calls instead of 60. Qwen3.5 can consume output tokens
# in hidden reasoning, so local runs default to a larger, configurable budget.
# CHANGED: 768 -> 1536 for non-local. The fraud prompt now asks for 6-10 turns with
# earned objection/resolution arcs instead of a fixed 4 short turns, which needs more
# output budget per case than the old fixed-length format did.
LLM_IMPERSONATION_TARGET = 60
LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096" if os.getenv("USE_LOCAL", "").lower() == "true" else "1536"))

def _batched(seq, size):
    seq = list(seq)
    for i in range(0, len(seq), size):
        yield seq[i:i + size]

llm_user_ids = rng.choice(user_ids, size=min(LLM_IMPERSONATION_TARGET, N_USERS), replace=False)
pending = [(int(u), rng.choice(PRETEXTS), new_case_id("ai_impersonation")) for u in llm_user_ids]

for batch in _batched(pending, LLM_BATCH_SIZE):
    pretext_case_pairs = [(pretext, case_id) for _, pretext, case_id in batch]
    batch_results = generate_llm_case_batch(pretext_case_pairs, max_tokens=LLM_MAX_TOKENS)
    for u, pretext, case_id in batch:
        params = batch_results[case_id]
        tx = materialize_llm_transaction(
            u, user_history[u], params, case_id, users, merchant_ids,
            cat_lookup, rng, new_tx_id, SIM_START, SIM_DAYS,
        )
        if tx is not None:
            fraud_rows.append(tx)
            generation_log.append({
                "case_id": case_id, "fraud_type": "ai_impersonation", "user_id": u,
                "source": "llm", "pretext": pretext, **params,
            })

# ---- 6. Benign transcripts (negative examples for the transcript classifier) ----
# Doesn't touch fraud_rows or generation_log -- only writes to transcripts.jsonl,
# which is all src/models/transcript_classifier.py needs.
# CHANGED: also batched -- BENIGN_TARGET=40 at batch size 5 is 8 calls instead of 40.
BENIGN_TARGET = 40
benign_pending = [(rng.choice(BENIGN_PRETEXTS), new_case_id("benign_transcript")) for _ in range(BENIGN_TARGET)]
for batch in _batched(benign_pending, LLM_BATCH_SIZE):
    generate_benign_case_batch(batch)

all_rows = rows + fraud_rows
df = pd.DataFrame(all_rows)
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="raise")
df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

out_dir = Path("data/raw")
out_dir.mkdir(parents=True, exist_ok=True)
df.to_csv(out_dir / "transactions.csv", index=False)
pd.DataFrame(generation_log).to_csv(out_dir / "generation_log.csv", index=False)

print(df.shape)
print(df["is_fraud"].mean())
print(df["fraud_type"].value_counts())