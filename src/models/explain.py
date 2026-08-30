"""SHAP explainability for the Tier 1 XGBoost model."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    X_TEST_PKL, TEST_DF_PKL, XGB_TIER1_JSON, MODELS_ARTIFACTS,
)
from models import output as out


def run_shap_analysis() -> None:
    out.banner("SHAP analysis")

    model = xgb.XGBClassifier()
    model.load_model(XGB_TIER1_JSON)

    X_test = pd.read_pickle(X_TEST_PKL)
    test_df = pd.read_pickle(TEST_DF_PKL)
    y_test = test_df["is_fraud"].to_numpy()

    out.step("Computing TreeSHAP values across the test set...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)

    # Additivity self-check: base + sum(SHAP) must equal log-odds margin
    # within float tolerance. A mismatch means we're explaining the wrong model.
    pos = np.clip(model.predict_proba(X_test)[:, 1], 1e-15, 1 - 1e-15)
    margins = np.log(pos / (1 - pos))
    reconstructed = explainer.expected_value + shap_values.values.sum(axis=1)
    if len(np.atleast_1d(explainer.expected_value)) == 1:
        max_dev = float(np.max(np.abs(margins - reconstructed)))
        out.kv("Additivity check", f"max |margin - (base + sum(SHAP))| = {max_dev:.2e}")
        if max_dev > 5e-2:
            out.warn("SHAP decomposition does not match the model margin -- "
                     "explanations may be unreliable for this artifact")

    MODELS_ARTIFACTS.mkdir(parents=True, exist_ok=True)

    out.banner("Global feature importance (bar plot)")
    plt.figure(figsize=(10, 6))
    shap.plots.bar(shap_values, max_display=15, show=False)
    plt.title("Global Feature Importance (Mean |SHAP Value|)")
    plt.tight_layout()
    bar_path = MODELS_ARTIFACTS / "shap_importance_bar.png"
    plt.savefig(bar_path, dpi=300, bbox_inches="tight")
    plt.close()
    out.kv("Saved", bar_path.name)

    out.banner("Global SHAP beeswarm")
    plt.figure(figsize=(11, 7))
    shap.plots.beeswarm(shap_values, max_display=15, show=False)
    plt.title("Global SHAP Beeswarm (Feature Impact on Fraud Log-Odds)")
    plt.tight_layout()
    beeswarm_path = MODELS_ARTIFACTS / "shap_summary_beeswarm.png"
    plt.savefig(beeswarm_path, dpi=300, bbox_inches="tight")
    plt.close()
    out.kv("Saved", beeswarm_path.name)

    test_proba = model.predict_proba(X_test)[:, 1]

    out.banner("Local explanation: detected fraud (prob > 0.90)")
    fraud_indices = np.where((y_test == 1) & (test_proba > 0.90))[0]
    if len(fraud_indices):
        target_idx = int(fraud_indices[0])
        tx_row = test_df.iloc[target_idx]
        out.kv("Transaction", f"{tx_row.get('transaction_id', 'N/A')} "
                              f"({tx_row.get('fraud_type', 'N/A')}, "
                              f"prob={test_proba[target_idx]:.4f})")
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_values[target_idx], max_display=10, show=False)
        plt.title(f"Local Attribution — Detected Fraud ({tx_row.get('fraud_type', 'fraud')})")
        plt.tight_layout()
        waterfall_path = MODELS_ARTIFACTS / "shap_waterfall_detected.png"
        plt.savefig(waterfall_path, dpi=300, bbox_inches="tight")
        plt.close()
        out.kv("Saved", waterfall_path.name)
    else:
        out.warn("No fraud transactions with prob > 0.90 in the test set")

    out.banner("Local explanation: AI impersonation (highest-risk case)")
    imp_indices = np.where(test_df["fraud_type"] == "ai_impersonation")[0]
    if len(imp_indices):
        imp_idx = int(imp_indices[np.argmax(test_proba[imp_indices])])
        tx_imp = test_df.iloc[imp_idx]
        out.kv("Transaction", f"{tx_imp.get('transaction_id', 'N/A')} "
                              f"(prob={test_proba[imp_idx]:.4f})")
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_values[imp_idx], max_display=10, show=False)
        plt.title(f"Local Attribution — AI Impersonation (case {tx_imp.get('case_id', 'N/A')})")
        plt.tight_layout()
        waterfall_imp_path = MODELS_ARTIFACTS / "shap_waterfall_impersonation.png"
        plt.savefig(waterfall_imp_path, dpi=300, bbox_inches="tight")
        plt.close()
        out.kv("Saved", waterfall_imp_path.name)

    out.banner("Top 10 features (mean |SHAP|)")
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    ranking = pd.DataFrame({
        "Feature": X_test.columns,
        "MeanAbsSHAP": mean_abs_shap,
    }).sort_values("MeanAbsSHAP", ascending=False).head(10)
    out.table(["rank", "feature", "mean |SHAP|"],
              [[i + 1, row.Feature, f"{row.MeanAbsSHAP:.4f}"]
               for i, row in enumerate(ranking.itertuples())],
              aligns=["r", "l", "r"])

    # AUDIT FIX (ml-pipeline-audit-agent-prompt.md Objective 2, step 1):
    # persist a per-fraud-type feature ranking that the generator can consult.
    # `src.generator.shap_feedback.load_feature_ranking` reads this file when
    # USE_SHAP_FEEDBACK=1. Per-class mean |SHAP| (over fraud rows of that
    # class in the test set) is the brief's "feature-importance comparison of
    # caught vs missed fraud of the same type" — here we use the same class
    # across all rows, which is the simpler version available without a
    # separate caught/missed split.
    import json as _json
    ranking_path = MODELS_ARTIFACTS / "shap_feature_importance.json"
    per_class_ranking: dict[str, list[str]] = {"__global__": ranking["Feature"].tolist()}
    for ft in sorted(test_df["fraud_type"].dropna().unique()):
        if ft == "normal":
            continue
        mask = (test_df["fraud_type"] == ft).to_numpy()
        if not mask.any():
            continue
        cls_shap = np.abs(shap_values.values[mask]).mean(axis=0)
        cls_rank = pd.DataFrame({
            "Feature": X_test.columns,
            "MeanAbsSHAP": cls_shap,
        }).sort_values("MeanAbsSHAP", ascending=False)
        per_class_ranking[ft] = cls_rank["Feature"].tolist()
    with open(ranking_path, "w") as f:
        _json.dump(per_class_ranking, f, indent=2)
    out.kv("Saved per-class feature ranking", ranking_path.name)


if __name__ == "__main__":
    run_shap_analysis()
