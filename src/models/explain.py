import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb

def run_shap_analysis():
    """
    Computes TreeSHAP feature attributions on XGBoost to satisfy real-world banking explainability
    and compliance requirements. Generates both global importance and individual transaction waterfall charts.
    """
    print("=" * 70)
    print("TIER 2: SHAP (SHapley Additive exPlanations) EXPLAINABILITY")
    print("=" * 70)

    # 1. Load Model & Data
    model = xgb.XGBClassifier()
    model.load_model("models_artifacts/xgboost_tier1.json")

    X_test = pd.read_pickle("data/processed/X_test.pkl")
    test_df = pd.read_pickle("data/processed/test_df.pkl")
    y_test = test_df["is_fraud"].to_numpy()

    # 2. Build TreeExplainer
    print("Computing TreeSHAP values across test dataset...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)

    Path("models_artifacts").mkdir(parents=True, exist_ok=True)

    # 3. Global Summary: Mean Absolute SHAP (Feature Importance Bar Plot)
    plt.figure(figsize=(10, 6))
    shap.plots.bar(shap_values, max_display=15, show=False)
    plt.title("Global Feature Importance (Mean |SHAP Value|)", fontsize=14, pad=15)
    plt.tight_layout()
    bar_path = "models_artifacts/shap_importance_bar.png"
    plt.savefig(bar_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Global feature importance plot saved to: {bar_path}")

    # 4. Global Beeswarm Plot (Shows direction and magnitude of features)
    plt.figure(figsize=(11, 7))
    shap.plots.beeswarm(shap_values, max_display=15, show=False)
    plt.title("Global SHAP Beeswarm Summary (Feature Impact on Fraud Log-Odds)", fontsize=14, pad=15)
    plt.tight_layout()
    beeswarm_path = "models_artifacts/shap_summary_beeswarm.png"
    plt.savefig(beeswarm_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Global beeswarm plot saved to: {beeswarm_path}")

    # 5. Local Explanation: High-Risk Detected Fraud Transaction
    test_proba = model.predict_proba(X_test)[:, 1]
    fraud_indices = np.where((y_test == 1) & (test_proba > 0.90))[0]
    if len(fraud_indices) > 0:
        target_idx = int(fraud_indices[0])
        tx_row = test_df.iloc[target_idx]
        print(f"\nExplaining Detected Fraud Transaction: ID={tx_row.get('transaction_id', 'N/A')} (Type: {tx_row.get('fraud_type', 'N/A')}, Prob: {test_proba[target_idx]:.4f})")
        
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_values[target_idx], max_display=10, show=False)
        plt.title(f"Local Decision Attribution — Detected Fraud ({tx_row.get('fraud_type', 'fraud')})", fontsize=12, pad=15)
        plt.tight_layout()
        waterfall_path = "models_artifacts/shap_waterfall_detected.png"
        plt.savefig(waterfall_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Detected transaction waterfall saved to: {waterfall_path}")

    # 6. Local Explanation: Borderline / Edge-Case Transaction (e.g. AI Impersonation)
    impersonation_indices = np.where(test_df["fraud_type"] == "ai_impersonation")[0]
    if len(impersonation_indices) > 0:
        imp_idx = int(impersonation_indices[0])
        tx_imp = test_df.iloc[imp_idx]
        print(f"\nExplaining AI-Impersonation Case: ID={tx_imp.get('transaction_id', 'N/A')} (Prob: {test_proba[imp_idx]:.4f})")
        
        plt.figure(figsize=(10, 6))
        shap.plots.waterfall(shap_values[imp_idx], max_display=10, show=False)
        plt.title(f"Local Decision Attribution — AI Impersonation (Case: {tx_imp.get('case_id', 'N/A')})", fontsize=12, pad=15)
        plt.tight_layout()
        waterfall_imp_path = "models_artifacts/shap_waterfall_impersonation.png"
        plt.savefig(waterfall_imp_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"AI Impersonation transaction waterfall saved to: {waterfall_imp_path}")

    # 7. Print Top Global Contributing Features
    mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
    top_feature_ranking = pd.DataFrame({
        "Feature": X_test.columns,
        "Mean_Abs_SHAP": mean_abs_shap
    }).sort_values("Mean_Abs_SHAP", ascending=False).reset_index(drop=True)

    print("\n--- Top 10 Most Impactful Features (SHAP Global Ranking) ---")
    print(top_feature_ranking.head(10).to_string(index=False))

    return explainer

if __name__ == "__main__":
    run_shap_analysis()
