"""
Centralized configuration for the fraud detection pipeline.

This module consolidates all constants, feature column definitions, hyperparameters,
and paths to eliminate duplication across train.py, evaluate.py, explain.py,
feedback_loop.py, smotenc_augment.py, smotenc_train.py, and anomaly.py.
"""

from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================
from pathlib import Path

# Project root:
# C:\Users\HP\Desktop\fraud_model
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Model/artifact directory
MODELS_ARTIFACTS = PROJECT_ROOT / "models_artifacts"

# Raw data files
TRANSACTIONS_CSV = DATA_RAW / "transactions.csv"
TRANSCRIPTS_JSONL = DATA_RAW / "transcripts.jsonl"
GENERATION_LOG_CSV = DATA_RAW / "generation_log.csv"

# Processed data files
TRANSACTIONS_FEATURES_PKL = DATA_PROCESSED / "transactions_features.pkl"
TRAIN_DF_PKL = DATA_PROCESSED / "train_df.pkl"
VAL_DF_PKL = DATA_PROCESSED / "val_df.pkl"
TEST_DF_PKL = DATA_PROCESSED / "test_df.pkl"
X_TRAIN_PKL = DATA_PROCESSED / "X_train.pkl"
X_VAL_PKL = DATA_PROCESSED / "X_val.pkl"
X_TEST_PKL = DATA_PROCESSED / "X_test.pkl"

# Augmented data files
TRAIN_DF_SMOTENC_PKL = DATA_PROCESSED / "train_df_smotenc.pkl"
SYNTHETIC_MINORITY_ROWS_SMOTENC_PKL = DATA_PROCESSED / "synthetic_minority_rows_smotenc.pkl"
SYNTHETIC_FEEDBACK_ROWS_CSV = DATA_PROCESSED / "synthetic_feedback_rows.csv"

# Model artifacts
XGB_TIER1_JSON = MODELS_ARTIFACTS / "xgboost_tier1.json"
XGB_TIER1_SMOTENC_JSON = MODELS_ARTIFACTS / "xgboost_tier1_smotenc.json"
XGB_TIER1_FEEDBACK_JSON = MODELS_ARTIFACTS / "xgboost_tier1_feedback.json"
XGB_TIER1_CTGAN_JSON = MODELS_ARTIFACTS / "xgboost_tier1_ctgan_augmented.json"
ISO_FOREST_TIER2_JOBLIB = MODELS_ARTIFACTS / "isolation_forest_tier2.joblib"
ISO_FOREST_CONFIG_JSON = MODELS_ARTIFACTS / "isolation_forest_config.json"
ISO_FOREST_THRESHOLDS_CSV = MODELS_ARTIFACTS / "isolation_forest_thresholds.csv"
FEEDBACK_QUEUE_CSV = DATA_PROCESSED / "anomaly_feedback_queue.csv"

# SHAP outputs
# =============================================================================
# FEATURE COLUMN DEFINITIONS (single source of truth)
# =============================================================================
FEATURE_COLS = [
    "amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
    "count_30d", "amount_zscore_30d", "new_device", "new_merchant",
    "merchant_cat_freq_user", "time_since_last_s", "dist_from_prev_km",
    "geo_velocity_kmh", "hour_of_day", "three_ds_failures_before_result",
    # New user-level features added in v1.1
    "three_ds_failures_last_30d", "device_trust_age_days", "burst_count_10m",
    "is_high_amount_burst", "inter_transaction_time_s",
]

CAT_COLS = ["merchant_category", "channel", "three_ds_result"]
MODEL_COLS = FEATURE_COLS + CAT_COLS

# Binary flag columns (0/1) - for SMOTENC categorical declaration
BINARY_FLAG_COLS = ["new_device", "new_merchant", "is_high_amount_burst"]

# Steerable continuous columns for feedback loop
STEERABLE_COLS = [
    "amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
    "count_30d", "amount_zscore_30d", "merchant_cat_freq_user",
    "time_since_last_s", "dist_from_prev_km", "geo_velocity_kmh",
]

# =============================================================================
# DATA SPLIT CONFIGURATION
# =============================================================================
TRAIN_QUANTILE = 0.70
VAL_QUANTILE = 0.80
TEST_QUANTILE = 1.00  # implicit

# =============================================================================
# XGBOOST HYPERPARAMETERS (Tier 1)
# =============================================================================
XGB_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.08,
    "eval_metric": "aucpr",
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
    "tree_method": "hist",
}

# Threshold search
THRESHOLD_CANDIDATES = 99
THRESHOLD_MIN = 0.01
THRESHOLD_MAX = 0.99

# =============================================================================
# SMOTENC CONFIGURATION
# =============================================================================
SMOTENC_K_NEIGHBORS = 5
SMOTENC_TARGET_CLASSES = {
    "ai_impersonation": 200,
    "auth_bypass": 200,
}
SMOTENC_SEED = 42

# =============================================================================
# FEEDBACK LOOP CONFIGURATION
# =============================================================================
FEEDBACK_ROWS_PER_TYPE = 80
FEEDBACK_MAX_CYCLES = 10
FEEDBACK_SEED = 42
FEEDBACK_STEER_STRENGTH = 0.3

# =============================================================================
# ISOLATION FOREST CONFIGURATION (Tier 2)
# =============================================================================
IF_PARAM_GRID = {
    "n_estimators": [200, 400, 600],
    "max_samples": [128, 256, 512],
    "max_features": [0.5, 0.75, 1.0],
}
IF_FIXED_PARAMS = {
    "random_state": 42,
    "n_jobs": -1,
    "bootstrap": False,
}
IF_N_SPLITS = 5
IF_CONTAMINATION_CANDIDATES = [0.0005, 0.001, 0.002, 0.003, 0.005, 0.007, 0.01]
IF_NORMAL_PERCENTILES = (1.0, 99.0)
IF_FEEDBACK_QUEUE_TOP_N = 200

# =============================================================================
# GENERATOR CONFIGURATION
# =============================================================================
GEN_SEED = 42
SIM_START = "2026-01-01"
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

# Fraud type targets (desired counts in train split)
FRAUD_TYPE_TARGETS = {
    "account_takeover": 120,
    "ai_impersonation": 80,
    "auth_bypass": 220,
    "bustout_identity": 450,
    "card_testing": 340,
}

# =============================================================================
# LLM GENERATOR CONFIGURATION
# =============================================================================
LLM_BATCH_SIZE = 1
LLM_LOCAL_RETRIES = 2
LLM_LOCAL_TEMPERATURE = 0.40
LLM_LOCAL_MAX_TOKENS = 4096

# =============================================================================
# EVALUATION THRESHOLDS FOR BUSINESS TABLE
# =============================================================================
BUSINESS_THRESHOLDS = [0.30, 0.50, 0.70, 0.90]

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LEVEL = "INFO"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def ensure_directories():
    """Create all required directories."""
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    MODELS_ARTIFACTS.mkdir(parents=True, exist_ok=True)


def get_feature_config():
    """Return feature configuration as a dict for serialization."""
    return {
        "feature_cols": FEATURE_COLS,
        "cat_cols": CAT_COLS,
        "model_cols": MODEL_COLS,
        "binary_flag_cols": BINARY_FLAG_COLS,
        "steerable_cols": STEERABLE_COLS,
    }
