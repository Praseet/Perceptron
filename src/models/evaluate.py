from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score

print("=" * 80)
print("MASTERCARD GENAI PAYMENT FRAUD HACKATHON — DEFEND EVALUATION SUITE")
print("=" * 80)

# ============================================================
# 1. Load Data and Supervised Model (XGBoost Tier 1)
# ============================================================
X_val = pd.read_pickle("data/processed/X_val.pkl")
X_test = pd.read_pickle("data/processed/X_test.pkl")
val_df = pd.read_pickle("data/processed/val_df.pkl")
test_df = pd.read_pickle("data/processed/test_df.pkl")
y_val = val_df["is_fraud"].to_numpy()
y_test = test_df["is_fraud"].to_numpy()

xgb_model = xgb.XGBClassifier()
xgb_model.load_model("models_artifacts/xgboost_tier1.json")

val_proba_xgb = xgb_model.predict_proba(X_val)[:, 1]
test_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

# ============================================================
# 2. Load Unsupervised Model (Isolation Forest Tier 2) if available
# ============================================================
iso_forest_path = Path("models_artifacts/isolation_forest_tier2.joblib")
has_iso_forest = iso_forest_path.exists()

if has_iso_forest:
    iso_forest = joblib.load(iso_forest_path)
    val_scores_iso = -iso_forest.decision_function(X_val)
    test_scores_iso = -iso_forest.decision_function(X_test)
    s_min, s_max = val_scores_iso.min(), val_scores_iso.max()
    val_proba_iso = (val_scores_iso - s_min) / max(s_max - s_min, 1e-9)
    test_proba_iso = (test_scores_iso - s_min) / max(s_max - s_min, 1e-9)

# ============================================================
# 3. Benchmark Metrics & Prevalence Baseline
# ============================================================
prevalence = float(y_test.mean())
xgb_val_pr = average_precision_score(y_val, val_proba_xgb)
xgb_test_pr = average_precision_score(y_test, test_proba_xgb)

print(f"\n[Test Prevalence Baseline]: {prevalence:.5f} ({y_test.sum()} frauds / {len(y_test):,} transactions)")
print(f"XGBoost (Supervised Tier 1)   -> Val PR-AUC: {xgb_val_pr:.4f} | Test PR-AUC: {xgb_test_pr:.4f}")

if has_iso_forest:
    iso_val_pr = average_precision_score(y_val, val_proba_iso)
    iso_test_pr = average_precision_score(y_test, test_proba_iso)
    print(f"Isolation Forest (Unsupervised Tier 2) -> Val PR-AUC: {iso_val_pr:.4f} | Test PR-AUC: {iso_test_pr:.4f}")

# ============================================================
# 4. Validation-Frozen Threshold Selection (XGBoost)
# ============================================================
candidate_thresholds = np.linspace(0.01, 0.99, 99)
val_scores = [
    (f1_score(y_val, (val_proba_xgb >= t).astype(int), zero_division=0), float(t))
    for t in candidate_thresholds
]
_, chosen_threshold = max(val_scores)
test_pred = (test_proba_xgb >= chosen_threshold).astype(int)
tn, fp, fn, tp = confusion_matrix(y_test, test_pred).ravel()

precision = tp / max(tp + fp, 1)
recall = tp / max(tp + fn, 1)
f1 = f1_score(y_test, test_pred, zero_division=0)
fpr = fp / max(fp + tn, 1)

print("\n" + "=" * 80)
print(f"XGBOOST OPERATING PERFORMANCE @ FROZEN THRESHOLD ({chosen_threshold:.2f})")
print("=" * 80)
print(f"Precision:            {precision:.4f}")
print(f"Recall:               {recall:.4f}")
print(f"F1-Score:             {f1:.4f}")
print(f"False Positive Rate:  {fpr:.6f}")
print(f"Confusion Matrix:     TP={tp}, FP={fp}, TN={tn}, FN={fn}")

# Business tradeoff table
print("\n--- Business Operating Thresholds ---")
for thr in [0.30, 0.50, 0.70, 0.90, chosen_threshold]:
    pred_t = (test_proba_xgb >= thr).astype(int)
    tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test, pred_t).ravel()
    p_t = tp_t / max(tp_t + fp_t, 1)
    r_t = tp_t / max(tp_t + fn_t, 1)
    f1_t = f1_score(y_test, pred_t, zero_division=0)
    marker = "  <-- (Validation-Frozen)" if abs(thr - chosen_threshold) < 1e-4 else ""
    print(f"Threshold: {thr:.2f} | Precision: {p_t:.3f} | Recall: {r_t:.3f} | F1: {f1_t:.3f} | FP: {fp_t:3d} | FN: {fn_t:3d}{marker}")

# ============================================================
# 5. Per-Fraud-Type PR-AUC & Case-Level Recall
# ============================================================
print("\n" + "=" * 80)
print("PER-FRAUD-FAMILY PERFORMANCE & CASE-LEVEL RECALL")
print("=" * 80)

for ft in sorted(test_df["fraud_type"].dropna().unique()):
    if ft == "normal":
        continue
    n_cases = (test_df.fraud_type == ft).sum()
    mask = test_df["fraud_type"].isin(["normal", ft]).to_numpy()
    ap = average_precision_score(test_df.loc[mask, "is_fraud"], test_proba_xgb[mask])
    flag = "  <-- LOW SAMPLE" if n_cases < 10 else ""
    print(f"{ft:22s} count={n_cases:4d} | PR-AUC={ap:.4f}{flag}")

scored = test_df[["case_id", "is_fraud", "fraud_type"]].copy()
scored["pred"] = test_pred
fraud_cases = scored.loc[scored["is_fraud"] == 1].dropna(subset=["case_id"])
case_detected = fraud_cases.groupby("case_id")["pred"].max()
case_recall = float(case_detected.mean()) if len(case_detected) else 0.0

print(f"\nAggregate Case-Level Recall: {case_recall:.4f} ({int(case_detected.sum())}/{len(case_detected)} attack campaigns detected)")

# ============================================================
# 6. Missed Cases Diagnostics (False Negatives)
# ============================================================
missed = test_df[(y_test == 1) & (test_pred == 0)]
print(f"\nTotal False Negatives: {len(missed)}")
if len(missed) > 0:
    print(missed['fraud_type'].value_counts().to_string())

print("\n" + "=" * 80)
print("EVALUATION COMPLETE — All metrics logged to CHANGELOG.md")
print("=" * 80)
