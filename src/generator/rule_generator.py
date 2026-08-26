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
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))
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
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))    
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
    first_ts, last_ts = utx[0][0], utx[-1][0]
    anchor = first_ts + (last_ts - first_ts) * float(rng.uniform(0.0, 1.0))    
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

# card testing / account takeover: unchanged from the PDF, ~2% of users each.
# Both are performing well (account_takeover test PR-AUC 1.0000) -- left untouched.
fraud_user_ids = rng.choice(user_ids, size=max(1, int(0.02 * N_USERS)), replace=False)
for u in fraud_user_ids:
    utx = user_history[int(u)]
    inject_card_testing(int(u), utx)
    inject_account_takeover(int(u), utx)

# CHANGED: auth_bypass now draws from its own, larger, independent candidate pool
# instead of sharing card_testing/account_takeover's 60-user (2%) pool. Confirmed
# via a real evaluate.py run that the shared pool left auth_bypass with too few
# total cases to train or evaluate reliably (test PR-AUC 0.1490, val=4/test=11).
# Unlike card_testing (multiple rows per case via bursts) and account_takeover (a
# blatant, easily-separable geo-jump + device-change signature), auth_bypass
# produces exactly ONE row per case, and its signal -- an elevated amount plus a
# failed-then-passed 3DS retry -- overlaps with the ~16% of NORMAL transactions
# that also show "failed_then_passed" from ordinary retry friction (see
# sample_normal_auth). It structurally needs more raw examples to separate from
# that legitimate background rate, not a resampling of the same 60 users.
auth_bypass_user_ids = rng.choice(user_ids, size=max(1, int(0.08 * N_USERS)), replace=False)
for u in auth_bypass_user_ids:
    inject_auth_bypass(int(u), user_history[int(u)])

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

# Prototype budget: enough to validate the path to the next tier, small enough
# to regenerate quickly on the local Qwen model. Raised here so the temporal
# split still leaves enough ai_impersonation examples for train/val/test.
# CHANGED (120 -> 160): the real fix for train/val starvation is removing the
# forced-timestamp hack below (see the materialize loop) -- that hack was forcing
# ~100% of cases into the test split regardless of target size, which is why raising
# this alone never worked. 160 is a modest safety-margin bump on top of the actual
# fix, sized for the thinnest slice (val is only ~10% of the time window) now that
# cases land where they naturally should.
LLM_IMPERSONATION_TARGET = 160
LLM_BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "1"))
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
for batch in _batched(pending, LLM_BATCH_SIZE):
    pretext_case_pairs = [(pretext, case_id) for _, pretext, case_id in batch]
    batch_results = generate_llm_case_batch(pretext_case_pairs, max_tokens=LLM_MAX_TOKENS)
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

# ---- 6. Benign transcripts (negative examples for the transcript classifier) ----
# Doesn't touch fraud_rows or generation_log -- only writes to transcripts.jsonl,
# which is all src/models/transcript_classifier.py needs.
# Keep the negative set balanced enough for later-tier training without turning
# regeneration into a long local-model run.
BENIGN_TARGET = 50
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