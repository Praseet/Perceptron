"""P0.9/P0.10/P0.11/P0.12 — compact validation-driven XGBoost model selection.

Run a small, high-information hyperparameter sweep (plus a scale_pos_weight
sweep and a weak-class-emphasis candidate) on the VALIDATION split only.

Selection metric hierarchy (Section 19 of the plan):
  1. VAL PR-AUC as the primary threshold-free ranking metric
  2. recall at a low-FPR operating point as tie-break
  3. precision at the chosen operating point
  4. weak-class / case-level recall

TEST is never used for selection.

Usage:
  python -m src.models.sweep_train [--candidates N] [--device auto|cuda|cpu]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.config import (
    TRAIN_DF_PKL, VAL_DF_PKL, TEST_DF_PKL,
    X_TRAIN_PKL, X_VAL_PKL, X_TEST_PKL,
    XGB_TIER1_JSON, FEEDBACK_SEED,
    ensure_directories, MODELS_ARTIFACTS,
)

STRUCTURAL_CANDIDATES = [
    # (max_depth, min_child_weight, gamma, subsample, colsample_bytree,
    #  learning_rate, reg_alpha, reg_lambda)
    (4, 3, 0.0, 0.9, 0.9, 0.05, 0.0, 1.0),
    (4, 3, 0.0, 0.9, 0.9, 0.05, 0.1, 5.0),
    (4, 5, 0.25, 0.8, 0.8, 0.05, 0.1, 5.0),
    (5, 3, 0.0, 0.9, 0.9, 0.05, 0.0, 5.0),
    (5, 5, 0.25, 0.8, 0.8, 0.05, 0.1, 5.0),
    (6, 3, 0.25, 0.9, 0.9, 0.05, 0.1, 5.0),
    (6, 5, 1.0, 0.8, 0.8, 0.05, 0.1, 5.0),
    (4, 1, 0.0, 1.0, 1.0, 0.08, 0.0, 1.0),
    (4, 3, 0.0, 0.75, 0.75, 0.03, 0.1, 10.0),
    (5, 1, 0.25, 0.9, 0.9, 0.08, 0.0, 1.0),
    (6, 3, 1.0, 0.75, 0.75, 0.03, 0.1, 10.0),
    (3, 3, 0.0, 0.9, 0.9, 0.08, 0.0, 1.0),
]

SPW_MULTIPLIERS = [0.5, 0.75, 1.0, 1.25, 1.5]


def _base_model(emp_spw, params, device):
    return {
        "n_estimators": 1500,
        "max_depth": params[0],
        "min_child_weight": params[1],
        "gamma": params[2],
        "subsample": params[3],
        "colsample_bytree": params[4],
        "learning_rate": params[5],
        "reg_alpha": params[6],
        "reg_lambda": params[7],
        "scale_pos_weight": float(emp_spw),
        "eval_metric": "aucpr",
        "tree_method": "hist",
        "device": device,
        "random_state": int(FEEDBACK_SEED or 42),
        "early_stopping_rounds": 60,
        "verbosity": 0,
    }
def select_operating_threshold(y_true, proba, max_fpr=0.0005,
                               min_precision=0.90):
    """P0.11 — business-constrained threshold objective computed on VAL only:
       1. maximize recall subject to FPR <= max_fpr
       2. else maximize recall subject to FPR <= 0.001
       3. else maximize F1 subject to precision >= min_precision
       4. else maximize F1
    """
    n_neg = max(int((y_true == 0).sum()), 1)
    cands = []
    for t in np.linspace(0.05, 0.95, 19):
        pred = (proba >= t).astype(int)
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + int((y_true == 1).sum()))
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        fpr = fp / n_neg
        cands.append((float(t), rec, prec, f1, fpr))

    def rank(c):
        # Most-negative tier wins; within a tier, larger secondary wins.
        _, rec, prec, f1, fpr = c
        if fpr <= max_fpr:
            return (-0, rec)
        if fpr <= 0.001:
            return (-1, rec)
        if prec >= min_precision:
            return (-2, f1)
        return (-3, f1)

    return max(cands, key=rank)[0]


def evaluate(model, X_val, y_val, X_test, y_test, thr):
    """Score a fitted model on val + (read-only) test, at operating thr."""
    p_val = model.predict_proba(X_val)[:, 1]
    p_test = model.predict_proba(X_test)[:, 1]

    def _metrics(y, p):
        pred = (p >= thr).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        fpr = fp / max(int((y == 0).sum()), 1)
        return {
            "pr_auc": float(average_precision_score(y, p)),
            "precision": float(prec), "recall": float(rec),
            "f1": float(2 * prec * rec / max(1e-9, prec + rec)),
            "fpr": float(fpr), "fn": int(fn), "fp": int(fp),
        }

    return _metrics(y_val, p_val), _metrics(y_test, p_test), thr
def run_sweep(n_candidates: int, device: str) -> dict:
    ensure_directories()
    train_df = pd.read_pickle(TRAIN_DF_PKL)
    val_df = pd.read_pickle(VAL_DF_PKL)
    test_df = pd.read_pickle(TEST_DF_PKL)
    X_train = pd.read_pickle(X_TRAIN_PKL)
    X_val = pd.read_pickle(X_VAL_PKL)
    X_test = pd.read_pickle(X_TEST_PKL)

    y_train = train_df["is_fraud"].to_numpy()
    y_val = val_df["is_fraud"].to_numpy()
    y_test = test_df["is_fraud"].to_numpy()

    emp_spw = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    print(f"[sweep] train={len(X_train)} val={len(X_val)} test={len(X_test)} "
          f"emp_spw={emp_spw:.1f} device={device}", flush=True)

    if device in ("auto", None):
        try:
            device = "cuda" if xgb.build_info().get("USE_CUDA") else "cpu"
        except Exception:
            device = "cpu"
    print(f"[sweep] device={device}", flush=True)

    baseline = xgb.XGBClassifier()
    baseline.load_model(str(XGB_TIER1_JSON))
    p_val = baseline.predict_proba(X_val)[:, 1]
    base_ap = float(average_precision_score(y_val, p_val))
    print(f"[sweep] baseline VAL PR-AUC = {base_ap:.4f}", flush=True)

    results = []

    def _run_candidate(name, params, spw_mult, sample_weight=None):
        spw = emp_spw * spw_mult
        model = xgb.XGBClassifier(**_base_model(spw, params, device))
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False,
                  sample_weight=sample_weight)
        p_val = model.predict_proba(X_val)[:, 1]
        ap = float(average_precision_score(y_val, p_val))
        thr = select_operating_threshold(y_val, p_val)
        vm, tm, thr = evaluate(model, X_val, y_val, X_test, y_test, thr)
        results.append({
            "name": name, "params": params, "spw_mult": float(spw_mult),
            "spw": float(spw), "val_pr_auc": ap,
            "val": vm, "test": tm, "threshold": thr,
        })
        print(f"[sweep] {name:<28s} val_pr_auc={ap:.4f} "
              f"thr={thr:.3f} val_rec={vm['recall']:.3f} "
              f"val_fpr={vm['fpr']:.5f}",
              flush=True)

    # ---- Phase 1: structural candidates with empirical spw ----
    for i, params in enumerate(STRUCTURAL_CANDIDATES[:n_candidates]):
        _run_candidate(f"struct_{i + 1}", params, 1.0)

    # ---- Phase 2: scale_pos_weight search on top-3 structural candidates ----
    top3 = sorted(results, key=lambda r: r["val_pr_auc"], reverse=True)[:3]
    for base in top3:
        for mult in SPW_MULTIPLIERS:
            _run_candidate(f"spw_{base['name']}_x{mult}", base["params"], mult)

    # ---- Phase 3: weak-class-emphasis candidate (P0.12) ----
    best_struct = sorted(results, key=lambda r: r["val_pr_auc"], reverse=True)[0]
    w = np.ones(len(X_train), dtype=float)
    w[train_df["is_fraud"].to_numpy() == 1] = 6.0
    weak = train_df["fraud_type"].isin(
        ["ai_impersonation", "auth_bypass", "card_testing"]
    ).to_numpy()
    w[weak & (train_df["is_fraud"].to_numpy() == 1)] = 9.0
    _run_candidate("weak_class_emphasis", best_struct["params"], 1.0,
                   sample_weight=w)

    # ---- Select on VAL (never TEST) ----
    best = max(results, key=lambda r: (r["val_pr_auc"], r["val"]["recall"]))
    df_results = pd.DataFrame([
        {**{k: v for k, v in r.items() if not isinstance(v, dict)},
         "val_recall": r["val"]["recall"], "val_fpr": r["val"]["fpr"],
         "test_pr_auc": r["test"]["pr_auc"]}
        for r in results
    ])
    report_path = MODELS_ARTIFACTS / "sweep_report.json"
    report_path.write_text(
        json.dumps({
            "baseline_val_pr_auc": base_ap,
            "best_name": best["name"],
            "best_params": best["params"],
            "best_spw_mult": best["spw_mult"],
            "best_spw": best["spw"],
            "best_val_pr_auc": best["val_pr_auc"],
            "best_val": best["val"],
            "best_threshold": best["threshold"],
            "best_test": best["test"],
            "device": device,
            "all": df_results.to_dict(orient="records"),
        }, indent=2),
        encoding="utf-8",
    )
    print(f"\n[sweep] baseline VAL PR-AUC = {base_ap:.4f}", flush=True)
    print(f"[sweep] BEST: {best['name']} "
          f"VAL PR-AUC = {best['val_pr_auc']:.4f} "
          f"thr={best['threshold']:.3f} "
          f"(val rec={best['val']['recall']:.3f}, "
          f"fpr={best['val']['fpr']:.5f})",
          flush=True)
    print(f"[sweep] report -> {report_path}", flush=True)
    return {"best": best, "results": results}
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=int, default=8,
                        help="Number of structural candidates (max 12)")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--apply", action="store_true",
                        help="Write the winning model to xgboost_tier1.json "
                             "(backing up the current baseline first).")
    args = parser.parse_args()

    out = run_sweep(min(args.candidates, len(STRUCTURAL_CANDIDATES)), args.device)
    best = out["best"]

    if args.apply:
        backup = XGB_TIER1_JSON.with_name("xgboost_tier1.pre_sweep.json")
        if not backup.exists():
            os.replace(str(XGB_TIER1_JSON), str(backup))
            print(f"[apply] backed up baseline -> {backup.name}")
        d = best["params"]
        spw = best["spw"]
        model = xgb.XGBClassifier(**_base_model(spw, d, args.device or "cuda"))
        train_df = pd.read_pickle(TRAIN_DF_PKL)
        X_train = pd.read_pickle(X_TRAIN_PKL)
        y_train = train_df["is_fraud"].to_numpy()
        model.set_params(early_stopping_rounds=None)
        X_val = pd.read_pickle(X_VAL_PKL)
        y_val = pd.read_pickle(VAL_DF_PKL)["is_fraud"].to_numpy()
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        tmp = XGB_TIER1_JSON.with_name("xgboost_tier1.new.json")
        model.save_model(str(tmp))
        os.replace(str(tmp), str(XGB_TIER1_JSON))
        print(f"[apply] saved winning model -> {XGB_TIER1_JSON}")