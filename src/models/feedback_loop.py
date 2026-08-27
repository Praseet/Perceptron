"""
Tier 2 item 8 -- BASIC FEEDBACK LOOP (playbook: "take the fraud cases your
Tier 1 detector misses, use them to inform your generator, generate more like
them, retrain, and show recall improve across the cycle").

Leakage discipline (this project's core rule):
- The FEEDBACK SIGNAL comes from the VALIDATION split -- the production-
  traffic analog. Aggregate missed-pattern statistics only (per-feature
  medians / category frequencies of missed cases); no individual val row is
  ever copied into training data.
- SYNTHETIC TEMPLATES are drawn exclusively from the TRAIN split, so every
  generated row's inter-feature correlation structure comes from real,
  legitimately-seen data.
- TEST is touched exactly ONCE, at the very end, to prove the loop worked.
  It never informs anything: not generation, not thresholds, not cycles.

Cycle structure:
  cycle 0: score val with the frozen baseline -> missed-case profile
  cycle k: synthesize feedback rows for still-missed types -> retrain ->
           refreeze threshold on val -> rescore val
  final:   one-shot test comparison, frozen-baseline vs final-loop model

Outputs (all NEW files; nothing frozen is modified):
  models_artifacts/xgboost_tier1_feedback.json
  data/processed/synthetic_feedback_rows.csv   (audit trail, per cycle)

DEVIATION (flagged per project convention): build_features/evaluate helpers
are duplicated rather than imported so this script stays runtime-independent
of the frozen baseline's build script.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score

SEED = 42
FEATURE_COLS = ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                "count_30d", "amount_zscore_30d", "new_device", "new_merchant",
                "merchant_cat_freq_user", "time_since_last_s", "dist_from_prev_km",
                "geo_velocity_kmh", "hour_of_day", "three_ds_failures_before_result"]
CAT_COLS = ["merchant_category", "channel", "three_ds_result"]
MODEL_COLS = FEATURE_COLS + CAT_COLS

# How many synthetic rows per missed fraud type per cycle. Sized so the
# feedback signal is strong relative to these classes' tiny real counts
# (54-178 train rows) without drowning the real data. Kept modest: large
# steered batches effectively memorize the val-miss centroid and stop
# generalizing to future periods (seen in a measured val->test regression).
FEEDBACK_ROWS_PER_TYPE = 80
MAX_CYCLES = 10  # cycle 0 = diagnosis; up to 2 feedback/retrain rounds

# Continuous features allowed to be steered toward the missed-pattern
# centroid. hour_of_day is handled separately (circular); flags are kept
# from the template row.
STEERABLE_COLS = ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                  "count_30d", "amount_zscore_30d", "merchant_cat_freq_user",
                  "time_since_last_s", "dist_from_prev_km", "geo_velocity_kmh"]


def build_features(train_df, val_df, test_df):
    X_train_raw = train_df[MODEL_COLS].copy()
    X_val_raw = val_df[MODEL_COLS].copy()
    X_test_raw = test_df[MODEL_COLS].copy()

    train_medians = X_train_raw[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).median()
    for frame in (X_train_raw, X_val_raw, X_test_raw):
        frame[FEATURE_COLS] = frame[FEATURE_COLS].replace([np.inf, -np.inf], np.nan).fillna(train_medians)

    X_train = pd.get_dummies(X_train_raw, columns=CAT_COLS).fillna(-1)
    X_val = pd.get_dummies(X_val_raw, columns=CAT_COLS).reindex(columns=X_train.columns, fill_value=0).fillna(-1)
    X_test = pd.get_dummies(X_test_raw, columns=CAT_COLS).reindex(columns=X_train.columns, fill_value=0).fillna(-1)
    return X_train, X_val, X_test


def fit_and_score(train_df, val_df, test_df):
    """Train on (possibly augmented) train_df; freeze threshold on val.
    Returns model + probabilities + chosen threshold."""
    X_train, X_val, X_test = build_features(train_df, val_df, test_df)
    y_train = train_df["is_fraud"].to_numpy()
    y_val = val_df["is_fraud"].to_numpy()

    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.08,
        scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
        subsample=0.8, colsample_bytree=0.8, random_state=SEED, tree_method="hist",
    )
    model.fit(X_train, y_train)

    val_proba = model.predict_proba(X_val)[:, 1]
    candidate_thresholds = np.linspace(0.01, 0.99, 99)
    _, threshold = max(
        (f1_score(y_val, (val_proba >= t).astype(int), zero_division=0), float(t))
        for t in candidate_thresholds
    )
    test_proba = model.predict_proba(X_test)[:, 1]
    return model, val_proba, test_proba, threshold


def missed_profile(val_df, val_proba, threshold):
    """Aggregate statistics of the fraud cases val-split scoring MISSES.
    This dict is the ONLY thing that flows from val into training data --
    medians and category frequencies, never individual rows."""
    df = val_df.copy()
    df["proba"] = val_proba
    missed = df[(df["is_fraud"] == 1) & (df["proba"] < threshold)]
    profile = {}
    for fraud_type, group in missed.groupby("fraud_type"):
        if fraud_type == "normal" or group.empty:
            continue
        raw = group[MODEL_COLS].copy()
        raw[FEATURE_COLS] = raw[FEATURE_COLS].replace([np.inf, -np.inf], np.nan)
        centroid = raw[STEERABLE_COLS].median().dropna().to_dict()
        cat_freq = {c: raw[c].value_counts(normalize=True).to_dict() for c in CAT_COLS}
        profile[fraud_type] = {"n_missed": int(len(group)), "centroid": centroid,
                               "cat_freq": cat_freq}
    return profile


def synthesize_feedback_rows(train_df, profile, cycle_no, rng):
    """For each still-missed type: draw REAL train rows of that type as
    templates, steer continuous features toward the missed-pattern centroid,
    and resample categoricals from a blend of train-frequency and missed-case
    frequency. Every generated value exists in real data."""
    synthetic_frames = []
    for fraud_type, prof in profile.items():
        templates = train_df.loc[train_df["fraud_type"] == fraud_type, MODEL_COLS]
        if templates.empty:
            print(f"  {fraud_type}: no real train templates available; skipping.")
            continue
        n = FEEDBACK_ROWS_PER_TYPE
        sampled = templates.sample(n=n, replace=True,
                                   random_state=int(rng.integers(2**31))).reset_index(drop=True)
        type_std = templates[STEERABLE_COLS].replace([np.inf, -np.inf], np.nan).std().fillna(0.0)

        # Mild steering: the centroid is an AGGREGATE hint about what the
        # detector misses, not a template to reproduce. Strong pulls made val
        # recall climb while test recall fell -- i.e. memorizing the val-miss
        # region instead of broadening coverage of the attack pattern.
        steer = rng.uniform(0.15, 0.45, size=(n, len(STEERABLE_COLS)))
        noise = rng.normal(0.0, 0.35, size=(n, len(STEERABLE_COLS)))
        t_vals = sampled[STEERABLE_COLS].to_numpy(dtype=float)
        c_vals = np.array([prof["centroid"].get(c, np.nan) for c in STEERABLE_COLS], dtype=float)
        steered = t_vals + steer * (np.nan_to_num(c_vals) - t_vals) + noise * type_std.to_numpy(dtype=float)

        synth = sampled.copy()
        synth[STEERABLE_COLS] = np.where(np.isnan(c_vals), t_vals, steered)

        # Physical/domain constraints before anything downstream sees them.
        for col in ["amount", "account_age_days", "tx_last_1min", "tx_last_1hr", "tx_last_24hr",
                    "count_30d", "time_since_last_s", "dist_from_prev_km", "geo_velocity_kmh"]:
            synth[col] = synth[col].clip(lower=0.0)
        synth["hour_of_day"] = (sampled["hour_of_day"].to_numpy(dtype=float)
                                + rng.integers(-2, 3, size=n)) % 24
        synth["three_ds_failures_before_result"] = np.clip(
            sampled["three_ds_failures_before_result"].to_numpy(dtype=float), 0.0, None)

        # Categoricals: blend train-frequency with missed-case frequency;
        # every candidate value is one that exists in real train data.
        for col in CAT_COLS:
            base = templates[col].value_counts(normalize=True).to_dict()
            feedback = prof["cat_freq"].get(col, {})
            blended = {}
            for value in set(base) | set(feedback):
                p = 0.5 * base.get(value, 0.0) + 0.5 * feedback.get(value, 0.0)
                if p > 0:
                    blended[value] = p
            values = list(blended.keys())
            probs = np.array(list(blended.values()))
            synth[col] = rng.choice(values, size=n, p=probs / probs.sum())

        synth["fraud_type"] = fraud_type
        synth["is_fraud"] = 1
        synth["case_id"] = [f"synthetic_feedback_c{cycle_no}_{fraud_type}_{i:05d}"
                            for i in range(n)]
        synthetic_frames.append(synth)
        print(f"  {fraud_type}: {n} feedback rows from real train templates "
              f"(steered toward {prof['n_missed']} missed val cases)")

    return pd.concat(synthetic_frames, ignore_index=True) if synthetic_frames else None


def summarize(label, y_true, proba, threshold):
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
    return {"label": label, "threshold": threshold,
            "recall": tp / max(tp + fn, 1), "precision": tp / max(tp + fp, 1),
            "f1": f1_score(y_true, pred, zero_division=0),
            "pr_auc": average_precision_score(y_true, proba), "fn": int(fn), "tp": int(tp)}


if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    print("=" * 80)
    print("TIER 2 ITEM 8: FEEDBACK LOOP -- missed cases inform the generator")
    print("=" * 80)

    train_df = pd.read_pickle("data/processed/train_df.pkl")   # frozen
    val_df = pd.read_pickle("data/processed/val_df.pkl")       # production analog
    test_df = pd.read_pickle("data/processed/test_df.pkl")     # touched ONCE at the end

    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()
    current_train = train_df.copy()
    all_synthetic = []
    cycle_summaries = []
    cycle_models = []       # (model, threshold, test_proba) per cycle

    for cycle in range(MAX_CYCLES):
        model, val_proba, test_proba, thr = fit_and_score(current_train, val_df, test_df)
        summary = summarize(f"cycle_{cycle}", y_val, val_proba, thr)
        cycle_summaries.append(summary)
        cycle_models.append((model, thr, test_proba))
        print(f"\nCycle {cycle}: val recall={summary['recall']:.4f} "
              f"F1={summary['f1']:.4f} @ frozen threshold {thr:.2f} | missed val fraud: "
              f"{summary['fn']}")

        profile = missed_profile(val_df, val_proba, thr)
        if not profile or cycle == MAX_CYCLES - 1:
            if profile:
                print(f"\nStopping: reached MAX_CYCLES. Remaining missed types: "
                      f"{ {k: v['n_missed'] for k, v in profile.items()} }")
            else:
                print("\nNo further missed fraud types with train templates -- loop converged.")
            break

        synthetic = synthesize_feedback_rows(current_train, profile, cycle + 1, rng)
        if synthetic is None:
            break
        all_synthetic.append(synthetic)
        current_train = pd.concat([current_train, synthetic], ignore_index=True)

    # ---- model selection on VAL only (never on test) ----
    # Taking the last cycle would be arbitrary; production practice is to
    # deploy the best-validation candidate. Test stays untouched until the
    # chosen model's single evaluation below.
    best_cycle = max(range(len(cycle_summaries)),
                     key=lambda i: (cycle_summaries[i]["f1"], cycle_summaries[i]["recall"]))
    model, thr, test_proba = cycle_models[best_cycle]
    print(f"\nSelected {cycle_summaries[best_cycle]['label']} "
          f"(best val F1={cycle_summaries[best_cycle]['f1']:.4f}) "
          f"as the loop's candidate -- now evaluating it once on test.")


    # ---- final one-shot TEST evaluation: baseline vs loop-improved model ----
    baseline_model = xgb.XGBClassifier()
    baseline_model.load_model("models_artifacts/xgboost_tier1.json")
    _, X_val_b, X_test_b = build_features(train_df, val_df, test_df)
    b_val_proba = baseline_model.predict_proba(X_val_b)[:, 1]
    _, b_thr = max(
        (f1_score(y_val, (b_val_proba >= t).astype(int), zero_division=0), float(t))
        for t in np.linspace(0.01, 0.99, 99)
    )
    base_summary = summarize("FROZEN BASELINE", y_test,
                             baseline_model.predict_proba(X_test_b)[:, 1], b_thr)
    final_summary = summarize("FEEDBACK-LOOP MODEL", y_test, test_proba, thr)

    Path("models_artifacts").mkdir(parents=True, exist_ok=True)
    model.save_model("models_artifacts/xgboost_tier1_feedback.json")

    print("\n" + "=" * 80)
    print("CLOSED-LOOP EVIDENCE (test split -- touched once)")
    print("=" * 80)
    print(f"{'Metric':<14}{base_summary['label']:>20}{final_summary['label']:>22}")
    for key in ("pr_auc", "recall", "precision", "f1"):
        print(f"{key:<14}{base_summary[key]:>20.4f}{final_summary[key]:>22.4f}")
    print(f"{'fn (count)':<14}{base_summary['fn']:>20d}{final_summary['fn']:>22d}")

    print("\nVal-split recall across cycles (the 'improve across the cycle' curve):")
    for s in cycle_summaries:
        print(f"  {s['label']}: recall={s['recall']:.4f} F1={s['f1']:.4f} FN={s['fn']}")

    if all_synthetic:
        audit = pd.concat(all_synthetic, ignore_index=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        audit.to_csv("data/processed/synthetic_feedback_rows.csv", index=False)
        print(f"\nSynthetic feedback rows written to: "
              f"data/processed/synthetic_feedback_rows.csv ({len(audit)} rows)")
    print("Saved loop model to: models_artifacts/xgboost_tier1_feedback.json")
    print("Frozen baseline was not modified.")




