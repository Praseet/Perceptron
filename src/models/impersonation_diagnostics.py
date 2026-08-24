from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb


# ============================================================
# CONFIG
# ============================================================

THRESHOLD = 0.94

TEST_DF_PATH = "data/processed/test_df.pkl"
X_TEST_PATH = "data/processed/X_test.pkl"
MODEL_PATH = "models_artifacts/xgboost_tier1.json"

GENERATION_LOG_PATH = "data/raw/generation_log.csv"


# ============================================================
# 1. LOAD MODEL + TEST DATA
# ============================================================

print("=" * 80)
print("AI-IMPERSONATION FORENSIC DIAGNOSTIC")
print("=" * 80)

model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)

test_df = pd.read_pickle(TEST_DF_PATH)
X_test = pd.read_pickle(X_TEST_PATH)

test_df = test_df.reset_index(drop=True)

test_proba = model.predict_proba(X_test)[:, 1]

test_df["fraud_probability"] = test_proba

test_df["predicted_fraud"] = (
    test_df["fraud_probability"] >= THRESHOLD
).astype(int)


# ============================================================
# 2. SELECT AI-IMPERSONATION CASES
# ============================================================

ai_df = test_df[
    (test_df["fraud_type"] == "ai_impersonation") &
    (test_df["is_fraud"] == 1)
].copy()

print(f"\nAI-impersonation test transactions: {len(ai_df)}")


ai_df["detection_status"] = np.where(
    ai_df["predicted_fraud"] == 1,
    "DETECTED",
    "MISSED"
)


# ============================================================
# 3. LOAD GENERATION LOG
# ============================================================

generation_log = pd.read_csv(GENERATION_LOG_PATH)

print(
    f"Generation-log rows: {len(generation_log):,}"
)

print(
    "\nGeneration-log columns:"
)

print(
    generation_log.columns.tolist()
)


# ============================================================
# 4. KEEP AI-IMPERSONATION GENERATOR INFORMATION
# ============================================================

gen_ai = generation_log[
    generation_log["fraud_type"] == "ai_impersonation"
].copy()

print(
    f"\nAI-impersonation generation-log rows: {len(gen_ai)}"
)


# ============================================================
# 5. MERGE GENERATOR DATA WITH MODEL OUTPUT
# ============================================================

# case_id is the safest join key because the generator explicitly
# creates one for each fraud case.

audit = ai_df.merge(
    gen_ai,
    on="case_id",
    how="left",
    suffixes=("", "_generator")
)


# ============================================================
# 6. CHECK FOR JOIN PROBLEMS
# ============================================================

missing_generator = audit["fraud_type_generator"].isna().sum()

print(
    f"\nAI cases without generator-log match: "
    f"{missing_generator}"
)

if missing_generator > 0:
    print(
        "\nWARNING: Some AI-impersonation test cases could not "
        "be matched to generation_log.csv."
    )


# ============================================================
# 7. DISPLAY THE MOST IMPORTANT COLUMNS
# ============================================================

important_columns = [
    # Identity
    "case_id",
    "user_id",
    "timestamp",

    # Model result
    "fraud_probability",
    "detection_status",

    # Transaction
    "amount",
    "merchant_category",
    "device_id",
    "channel",
    "three_ds_result",
    "three_ds_failures_before_result",

    # Behavioral model features
    "amount_zscore_30d",
    "new_device",
    "new_merchant",
    "merchant_cat_freq_user",
    "time_since_last_s",
    "dist_from_prev_km",
    "geo_velocity_kmh",
    "tx_last_1min",
    "tx_last_1hr",
    "tx_last_24hr",
    "count_30d",
    "hour_of_day",

    # LLM / generator information
    "amount_multiplier",
    "urgency_level",
    "pretext_category",
    "transaction_attempted",
    "fallback",
]

important_columns = [
    c for c in important_columns
    if c in audit.columns
]


# ============================================================
# 8. PRINT DETECTED CASES
# ============================================================

print("\n" + "=" * 80)
print("DETECTED AI-IMPERSONATION CASES")
print("=" * 80)

detected = audit[
    audit["detection_status"] == "DETECTED"
].copy()

print(
    detected[
        important_columns
    ]
    .sort_values("fraud_probability", ascending=False)
    .to_string(index=False)
)


# ============================================================
# 9. PRINT MISSED CASES
# ============================================================

print("\n" + "=" * 80)
print("MISSED AI-IMPERSONATION CASES")
print("=" * 80)

missed = audit[
    audit["detection_status"] == "MISSED"
].copy()

print(
    missed[
        important_columns
    ]
    .sort_values("fraud_probability", ascending=False)
    .to_string(index=False)
)


# ============================================================
# 10. NUMERICAL COMPARISON
# ============================================================

numeric_features = [
    "amount",
    "fraud_probability",
    "amount_multiplier",
    "amount_zscore_30d",
    "new_device",
    "new_merchant",
    "merchant_cat_freq_user",
    "time_since_last_s",
    "dist_from_prev_km",
    "geo_velocity_kmh",
    "tx_last_1min",
    "tx_last_1hr",
    "tx_last_24hr",
    "count_30d",
    "hour_of_day",
]

numeric_features = [
    c for c in numeric_features
    if c in audit.columns
]


detected_stats = detected[numeric_features].agg(
    ["mean", "median", "min", "max"]
).T

missed_stats = missed[numeric_features].agg(
    ["mean", "median", "min", "max"]
).T


comparison = pd.DataFrame({
    "detected_mean": detected_stats["mean"],
    "missed_mean": missed_stats["mean"],

    "detected_median": detected_stats["median"],
    "missed_median": missed_stats["median"],

    "detected_min": detected_stats["min"],
    "missed_min": missed_stats["min"],

    "detected_max": detected_stats["max"],
    "missed_max": missed_stats["max"],
})


print("\n" + "=" * 80)
print("DETECTED vs MISSED — NUMERICAL COMPARISON")
print("=" * 80)

print(
    comparison.to_string()
)


# ============================================================
# 11. CATEGORICAL COMPARISON
# ============================================================

categorical_features = [
    "urgency_level",
    "pretext_category",
    "transaction_attempted",
    "fallback",
    "merchant_category",
    "three_ds_result",
    "channel",
    "new_device",
    "new_merchant",
]


for col in categorical_features:

    if col not in audit.columns:
        continue

    print("\n" + "=" * 80)
    print(f"{col.upper()} — DETECTED")
    print("=" * 80)

    print(
        detected[col]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
        .to_string()
    )

    print("\n" + "=" * 80)
    print(f"{col.upper()} — MISSED")
    print("=" * 80)

    print(
        missed[col]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
        .to_string()
    )


# ============================================================
# 12. SORT ALL AI CASES BY MODEL CONFIDENCE
# ============================================================

print("\n" + "=" * 80)
print("ALL AI-IMPERSONATION CASES — LOWEST TO HIGHEST SCORE")
print("=" * 80)

sort_columns = [
    "case_id",
    "fraud_probability",
    "detection_status",
    "amount",
    "amount_multiplier",
    "amount_zscore_30d",
    "new_device",
    "new_merchant",
    "merchant_cat_freq_user",
    "hour_of_day",
    "urgency_level",
    "pretext_category",
]

sort_columns = [
    c for c in sort_columns
    if c in audit.columns
]

print(
    audit[
        sort_columns
    ]
    .sort_values("fraud_probability")
    .to_string(index=False)
)


# ============================================================
# 13. SAVE EVERYTHING FOR FURTHER ANALYSIS
# ============================================================

output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

audit_path = (
    output_dir /
    "ai_impersonation_forensic_audit.csv"
)

audit.to_csv(
    audit_path,
    index=False
)

print(
    f"\nSaved forensic audit to: {audit_path}"
)