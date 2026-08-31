"""
Anti-leakage fixes for fraud generation.

PROBLEM: Fraud types have zero feature overlap with normal transactions,
enabling trivial model cheating (100% PR-AUC via single-feature thresholds).

ROOT CAUSES:
1. card_testing/account_takeover: Use brand-new devices → device_trust ≈ 0
2. bustout_identity: New synthetic users → account_age = 1-4 days
3. synthetic_identity: New synthetic users → account_age = 31-97 days
4. bnpl_abuse: New synthetic users → account_age = 7-44 days

FIXES:
1. Make fraud inject into EXISTING user histories (not brand-new users)
2. Vary device_trust_age to overlap with normal IQR (0.18-1.1 days)
3. Vary account_age to overlap with normal IQR (817-2253 days)
4. Add realistic noise/jitter to all fraud features
"""

import sys
import pandas as pd
import numpy as np

def compute_normal_iqr_bounds(df):
    """Compute IQR bounds for key features from normal transactions."""
    normal = df[df['fraud_type'] == 'normal']
    return {
        'account_age_days': (
            normal['account_age_days'].quantile(0.25),
            normal['account_age_days'].quantile(0.75)
        ),
        'device_trust_age_days': (
            normal['device_trust_age_days'].quantile(0.25),
            normal['device_trust_age_days'].quantile(0.75)
        ),
        'count_30d': (
            normal['count_30d'].quantile(0.25),
            normal['count_30d'].quantile(0.75)
        ),
        'tx_last_1hr': (
            normal['tx_last_1hr'].quantile(0.25),
            normal['tx_last_1hr'].quantile(0.75)
        ),
        'amount': (
            normal['amount'].quantile(0.25),
            normal['amount'].quantile(0.75)
        ),
    }

def validate_no_leakage(df, fraud_type, bounds):
    """Check that fraud features have realistic overlap with normal IQR."""
    sub = df[df['fraud_type'] == fraud_type]
    if len(sub) == 0:
        return True, "No transactions to validate"
    
    issues = []
    for feat, (q25, q75) in bounds.items():
        if feat not in sub.columns:
            continue
        overlap = np.mean((sub[feat] >= q25) & (sub[feat] <= q75))
        if overlap < 0.05:  # Less than 5% overlap is suspicious
            issues.append(f"{feat}: {overlap:.1%} overlap (need >5%)")
    
    if issues:
        return False, "Low overlap: " + "; ".join(issues)
    return True, "OK"

if __name__ == "__main__":
    df = pd.read_pickle('data/processed/transactions_features.pkl')
    bounds = compute_normal_iqr_bounds(df)
    
    print("Normal IQR bounds:")
    for feat, (q25, q75) in bounds.items():
        print(f"  {feat}: [{q25:.2f}, {q75:.2f}]")
    
    print("\nLeakage validation:")
    all_ok = True
    for ft in ['card_testing', 'account_takeover', 'bustout_identity', 
               'synthetic_identity', 'bnpl_abuse', 'auth_bypass', 'ai_impersonation']:
        ok, msg = validate_no_leakage(df, ft, bounds)
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  {ft:20s}: {status} - {msg}")

    print(f"\nAnti-leakage gate: {'PASS' if all_ok else 'FAIL'}")
    # REAL GATE: fail loudly so run_pipeline.py (which checks the subprocess
    # return code) actually stops on a leak, instead of printing FAIL and
    # returning 0 as if nothing were wrong.
    sys.exit(0 if all_ok else 1)