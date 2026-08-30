"""
SHAP-driven feature-importance feedback for the rule-based impersonation
generator (ml-pipeline-audit-agent-prompt.md Objective 2).

The previous `inject_impersonation_case` in `rule_generator.py` used the WEAK
pattern: random parameter sampling with no feedback from the detector. The
brief warns that this is exactly the failure mode the audit must fix -- the
generator does not know what the defender is using to detect, so it cannot
target detection blind spots and the model never learns from the attempts.

This module exposes a `SteeringProfile` that the rule-based impersonation
path can consult to bias its parameters toward "look ordinary" on the highest-
importance features (the strong pattern). It:

  1. Reads the SHAP-derived feature importance for the AI-impersonation class
     from a JSON artifact written by `models.explain_shap`.
  2. Falls back to a sensible default ordering if the artifact is missing
     (so the generator still runs in cold-start or CI environments).
  3. Provides `steer_toward_normal`, which nudges a value toward the
     feature's empirical normal median (lower variance / closer-to-median)
     instead of the historical "amplified fraud" mode.

Behavior change is opt-in via `USE_SHAP_FEEDBACK=1`; otherwise no-op so
existing runs are not affected.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SHAP_PATH = _PROJECT_ROOT / "models_artifacts" / "shap_feature_importance.json"
_NORMAL_BOUNDS_JSON = _PROJECT_ROOT / "models_artifacts" / "normal_feature_bounds.json"

DEFAULT_STEERING_FEATURES = [
    "amount",
    "account_age_days",
    "count_30d",
    "tx_last_1hr",
    "tx_last_24hr",
    "three_ds_failures_before_result",
    "new_device",
    "new_merchant",
]


# Ordered by predicted usefulness for "look ordinary" on AI impersonation,
# which is the weakest class per BASELINE_METRICS.md (PR-AUC ~0.0008 in the
# latest audit run). The anti-leakage fixes have already collapsed the means
# of these features onto the normal distribution; the marginal signal is in
# reducing VARIANCE further. In priority order:
#   - amount / account_age_days: amount is the single most-weighted feature
#   - count_30d / tx_last_1hr: velocity features
#   - three_ds_failures_before_result: friction signal
#   - new_device / new_merchant: categorical device signals
#   - merchant_category: not a number, handled separately


def update_normal_bounds(features_df: pd.DataFrame) -> None:
    """Recompute and persist empirical normal IQR bounds from a features df.

    Cheap (~ms) and meant to be called from `run_pipeline.py` once after
    engineering. Idempotent.
    """
    normal = features_df[features_df["fraud_type"] == "normal"]
    bounds = {}
    for col in DEFAULT_STEERING_FEATURES:
        if col not in normal.columns:
            continue
        bounds[col] = {
            "q25": float(normal[col].quantile(0.25)),
            "q50": float(normal[col].quantile(0.50)),
            "q75": float(normal[col].quantile(0.75)),
        }
    _NORMAL_BOUNDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(_NORMAL_BOUNDS_JSON, "w") as f:
        json.dump(bounds, f, indent=2)


def load_feature_ranking() -> list[str]:
    """Return the SHAP-ranked feature list for AI impersonation.

    Reads from `models_artifacts/shap_feature_importance.json` if present
    (written by `models.explain_shap`). Otherwise returns the static default
    ordering. The list is from most-important to least-important, restricted
    to the steerable continuous features.
    """
    if _DEFAULT_SHAP_PATH.exists():
        with open(_DEFAULT_SHAP_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and "ai_impersonation" in data:
            ranked = data["ai_impersonation"]
        elif isinstance(data, list):
            ranked = data
        else:
            ranked = DEFAULT_STEERING_FEATURES
        # Filter to ones we can actually steer; preserve order.
        return [f for f in ranked if f in DEFAULT_STEERING_FEATURES] or DEFAULT_STEERING_FEATURES
    return DEFAULT_STEERING_FEATURES


def is_enabled() -> bool:
    """Opt-in toggle: `USE_SHAP_FEEDBACK=1` switches to the strong pattern."""
    return os.getenv("USE_SHAP_FEEDBACK", "0") == "1"


def steer_toward_normal(value: float, feature: str,
                        rng: np.random.Generator,
                        strength: float | None = None) -> float:
    """Nudge `value` toward the empirical normal median for `feature`.

    `strength` is the fraction of the gap to close in [0, 1]. Defaults to
    0.5 (close half the gap). Setting strength=0 returns `value` unchanged;
    strength=1 snaps to the median. Values are clipped to the normal IQR
    so we don't produce physically implausible transactions.

    Returns `value` unchanged when `is_enabled()` is False (opt-in only).
    """
    if not is_enabled():
        return value
    s = 0.5 if strength is None else max(0.0, min(1.0, float(strength)))
    bounds = _load_normal_bounds().get(feature)
    if not bounds:
        return value
    target = bounds["q50"]
    out = value + s * (target - value)
    return float(np.clip(out, bounds["q25"], bounds["q75"]))


def feature_distance(df_a: pd.DataFrame, df_b: pd.DataFrame,
                     feature_cols: Iterable[str]) -> pd.Series:
    """Mean per-row standardized Euclidean distance from df_a to nearest row
    in df_b over `feature_cols`. Cheap diversity check used by the feedback
    loop to flag rows that are near-duplicates of the missed cases they were
    derived from. Standardization is per-column over the union of df_a + df_b
    so the metric is dimensionless.

    NaN cells in the input are replaced with the union median per column so
    that sparse rolling-window features (e.g. device_trust_age_days for
    new users) do not produce NaN distances. Columns that are entirely NaN
    across both frames contribute 0 to the distance (their sd falls back to
    1.0 in the standardization step).

    Returns a Series indexed by df_a rows of mean distance to nearest df_b row.
    """
    cols = list(feature_cols)
    a = df_a[cols].to_numpy(dtype=float)
    b = df_b[cols].to_numpy(dtype=float)
    if len(a) == 0 or len(b) == 0:
        return pd.Series([], dtype=float)
    union = np.concatenate([a, b], axis=0)
    # Fill NaN per column with the column median so the standardization is
    # defined. Using median (not mean) keeps the substitute near existing
    # values rather than dragging the mean toward zero.
    col_med = np.nanmedian(union, axis=0)
    nan_mask = np.isnan(union)
    if nan_mask.any():
        union = np.where(nan_mask, col_med, union)
    mu = union.mean(axis=0)
    sd = union.std(axis=0)
    sd[sd < 1e-9] = 1.0
    a_z = (a - mu) / sd
    b_z = (b - mu) / sd
    # Brute-force nearest neighbour; fine for the few-hundred-row scale this
    # guard runs at (called from feedback_loop.py at the end of each cycle).
    dists = np.empty(len(a), dtype=float)
    for i, row in enumerate(a_z):
        d = np.linalg.norm(b_z - row, axis=1)
        # Guard NaN rows: if the row itself is NaN after standardization
        # (shouldn't happen post-fill, but defensive), return the median
        # distance across the population rather than NaN.
        if np.isnan(d).any():
            dists[i] = float(np.nanmedian(d))
        else:
            dists[i] = float(np.min(d))
    return pd.Series(dists, index=df_a.index)