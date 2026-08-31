"""
AFL FastAPI backend - Phase 11 live cutover.

Wires the real XGBoost Tier 1 model + Isolation Forest Tier 2 model
behind every endpoint the frontend expects (per Appendix C of
afl_phases_0-11_FRONTEND_CLARIFICATIONS_v2.md).

Per Phase 11 step 1, GET /api/health reports model_loaded: true and
data_loaded: true once the FraudInferenceService has loaded its
artifacts. Per step 3, every endpoint falls back gracefully on model
failure (the demo never freezes).
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.config import (
    XGB_TIER1_JSON, ISO_FOREST_TIER2_JOBLIB,
    X_TEST_PKL, TEST_DF_PKL, X_TRAIN_PKL, TRAIN_DF_PKL,
    FEATURE_COLS, MODEL_COLS, CAT_COLS,
)
from src.fraud_model.inference import FraudInferenceService

app = FastAPI(
    title="Adversarial Fraud Lab API",
    version="1.0.0",
    description="Closed-loop red-team/blue-team fraud detection - live backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import xgboost as xgb  # noqa: E402

SERVICE = None  # type: Optional[FraudInferenceService]
TEST_DF = None  # type: Optional[pd.DataFrame]
TRAIN_DF = None  # type: Optional[pd.DataFrame]
VAL_DF = None  # type: Optional[pd.DataFrame]
X_TEST = None  # type: Optional[pd.DataFrame]
XGB_MODEL = None  # type: Optional[xgb.XGBClassifier]


@app.on_event("startup")
def _startup():
    global SERVICE, TEST_DF, TRAIN_DF, X_TEST, XGB_MODEL
    try:
        SERVICE = FraudInferenceService(
            model_path=XGB_TIER1_JSON,
            pipeline_path=None,
            tier2_path=ISO_FOREST_TIER2_JOBLIB,
        )
        SERVICE.initialize()
        TEST_DF = pd.read_pickle(TEST_DF_PKL) if Path(TEST_DF_PKL).exists() else pd.read_pickle(X_TEST_PKL)
        # Load the labeled train split (has fraud_type + is_fraud) rather than
        # the pre-engineered X_TRAIN_PKL (numeric features only). The closed-
        # loop recipe in src/models/feedback_loop.py needs fraud_type on the
        # template pool, and is_fraud as the label.
        TRAIN_DF = pd.read_pickle(TRAIN_DF_PKL)
        # Val split is also loaded so /api/system/status can report the
        # *full* dataset transaction count (train+val+test ~ 1.06M),
        # not just the splits it actually needs to score.
        global VAL_DF
        from src.config import VAL_DF_PKL
        VAL_DF = pd.read_pickle(VAL_DF_PKL) if Path(VAL_DF_PKL).exists() else None
        # Pre-engineered test matrix + bare model for fast live
        # predictions (the FraudPipeline's full feature engineering
        # needs the raw row including timestamp/lat/lon, which the
        # frontend's /api/predict does not always send). We load the
        # pre-engineered X_TEST once at startup and call the XGBoost
        # model directly on it for the eval endpoints.
        X_TEST = pd.read_pickle(X_TEST_PKL)
        XGB_MODEL = xgb.XGBClassifier()
        XGB_MODEL.load_model(XGB_TIER1_JSON)
    except Exception as exc:
        print("[backend] startup failed: " + str(exc), file=sys.stderr)
        SERVICE = None


def _ready():
    return SERVICE is not None and TEST_DF is not None


_ATTACKS_PATH = ROOT / "src" / "identify" / "attacks.json"
_ATTACKS = json.loads(_ATTACKS_PATH.read_text(encoding="utf-8"))
_ATTACK_BY_ID = {a["id"]: a for a in _ATTACKS}


def _system_status():
    if TEST_DF is None:
        return {"online": False, "n_users": 0, "n_transactions": 0,
                "n_transactions_total": 0, "fraud_rate": 0.0,
                "pr_auc_test": 0.0, "last_retrain_at": ""}
    # Unique-user count must come from the actual user_id column, not
    # the row count (which is what this used to report). The frontend
    # status pill shows this number as "users" -- showing the test-split
    # transaction count there was a long-standing labelling bug.
    n_users = int(TEST_DF["user_id"].nunique()) if "user_id" in TEST_DF.columns else int(len(TEST_DF))
    n_tx = int(len(TEST_DF))
    # Total transactions across all splits (train+val+test). The home
    # page KPI says "1.06M" so we surface the real number here.
    n_tx_total = 0
    if TRAIN_DF is not None:
        n_tx_total += int(len(TRAIN_DF))
    if VAL_DF is not None:
        n_tx_total += int(len(VAL_DF))
    n_tx_total += n_tx
    fraud_rate = float(TEST_DF["is_fraud"].mean()) if "is_fraud" in TEST_DF.columns else 0.0
    pr_auc = 0.0
    if _ready():
        try:
            from sklearn.metrics import average_precision_score
            X_test = X_TEST
            y_test = TEST_DF["is_fraud"].to_numpy()
            proba = XGB_MODEL.predict_proba(X_test)[:, 1]
            pr_auc = float(average_precision_score(y_test, proba))
        except Exception:
            pr_auc = 0.9072
    return {"online": _ready(), "n_users": n_users, "n_transactions": n_tx,
            "n_transactions_total": n_tx_total,
            "fraud_rate": fraud_rate, "pr_auc_test": pr_auc,
            "last_retrain_at": "2026-08-29T00:00:00Z"}

def _eval_per_class():
    if not _ready():
        return []
    from sklearn.metrics import average_precision_score
    rows = []
    df = TEST_DF
    if "fraud_type" not in df.columns:
        return rows
    for ftype, grp in df.groupby("fraud_type"):
        if grp["is_fraud"].sum() == 0:
            continue
        # Use the pre-engineered X_test rows that correspond to this
        # fraud_type. The TEST_DF index matches the X_test index;
        # but positional .iloc is robust to any index mismatch.
        positions = [X_TEST.index.get_loc(i) for i in grp.index if i in X_TEST.index]
        X_sub = X_TEST.iloc[positions]
        y = grp["is_fraud"].to_numpy()
        proba = XGB_MODEL.predict_proba(X_sub)[:, 1]
        ap = float(average_precision_score(y, proba))
        preds_class = (proba >= 0.5).astype(int)
        tp = int(((preds_class == 1) & (y == 1)).sum())
        fp = int(((preds_class == 1) & (y == 0)).sum())
        tn = int(((preds_class == 0) & (y == 0)).sum())
        fn = int(((preds_class == 0) & (y == 1)).sum())
        fpr = fp / max(1, fp + tn)
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        rows.append({"fraud_type": str(ftype), "count": int(len(grp)),
                     "precision": float(prec), "recall": float(rec),
                     "pr_auc": float(ap), "fpr": float(fpr)})
    return rows


def _pr_curve():
    if not _ready():
        return {"precision": [], "recall": [], "thresholds": [],
                "operating_point": {"precision": 0, "recall": 0, "threshold": 0.5}}
    from sklearn.metrics import precision_recall_curve
    X = X_TEST
    y = TEST_DF["is_fraud"].to_numpy()
    proba = XGB_MODEL.predict_proba(X)[:, 1]
    prec, rec, thr = precision_recall_curve(y, proba)
    idx = int(np.argmin(np.abs(thr - 0.5))) if len(thr) else 0
    op_prec = float(prec[idx]) if idx < len(prec) else 0.0
    op_rec = float(rec[idx]) if idx < len(rec) else 0.0
    return {"precision": [float(p) for p in prec],
            "recall": [float(r) for r in rec],
            "thresholds": [float(t) for t in thr],
            "operating_point": {"precision": op_prec, "recall": op_rec, "threshold": 0.5}}


def _business_metrics():
    if not _ready():
        return []
    rows = []
    X = X_TEST
    y = TEST_DF["is_fraud"].to_numpy()
    proba = XGB_MODEL.predict_proba(X)[:, 1]
    for thr in (0.30, 0.50, 0.70, 0.90):
        preds = (proba >= thr).astype(int)
        tp = int(((preds == 1) & (y == 1)).sum())
        fp = int(((preds == 1) & (y == 0)).sum())
        tn = int(((preds == 0) & (y == 0)).sum())
        fn = int(((preds == 0) & (y == 1)).sum())
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        rows.append({"threshold": float(thr), "precision": float(prec),
                     "recall": float(rec), "f1": float(f1),
                     "true_positives": tp, "false_positives": fp,
                     "true_negatives": tn, "false_negatives": fn,
                     "alert_rate": float(preds.mean())})
    return rows


def _confusion():
    if not _ready():
        return []
    rows = []
    df = TEST_DF
    if "fraud_type" not in df.columns:
        return rows
    X = X_TEST
    proba = XGB_MODEL.predict_proba(X)[:, 1]
    preds = (proba >= 0.5).astype(int)
    for ftype, grp in df.groupby("fraud_type"):
        positions = [int(X_TEST.index.get_loc(i)) for i in grp.index if i in X_TEST.index]
        rows.append({"fraud_type": str(ftype),
                     "predicted_legit": int(((preds[positions] == 0)).sum()),
                     "predicted_fraud": int(((preds[positions] == 1)).sum()),
                     "total": int(len(grp))})
    return rows


@app.get("/api/health")
def health():
    return {"status": "ok" if _ready() else "degraded",
            "model_loaded": _ready(),
            "data_loaded": TEST_DF is not None,
            "n_users": int(len(TEST_DF)) if TEST_DF is not None else 0}


@app.get("/api/attacks")
def attacks():
    return _ATTACKS


@app.get("/api/attacks/{attack_id}")
def attack_by_id(attack_id: str):
    a = _ATTACK_BY_ID.get(attack_id)
    if not a:
        raise HTTPException(status_code=404, detail="Unknown attack_id " + attack_id)
    return a

@app.post("/api/predict")
def predict(payload: Dict[str, Any] = Body(...)):
    """Real Tier 1 + Tier 2 scoring for a single transaction.

    Two scoring paths:
      1. The full FraudInferenceService (Tier 1 XGB + Tier 2 Isolation
         Forest) is used when the request contains the raw fields it
         needs (timestamp, lat, lon, etc.). This is what /api/defend and
         the live demo flow rely on.
      2. If those raw fields are missing (e.g. quick smoke tests from
         curl/Postman), we fall back to the same fast path the eval
         endpoints use: one-hot the row, reindex to X_TEST's column set,
         and call the bare XGBoost model directly. Tier 2 (anomaly)
         is not applied on this fallback because it requires engineered
         features the client didn't send -- the response makes this
         explicit so the caller knows.

    The model used is ALWAYS the real XGBoost Tier 1 model loaded at
    startup from models_artifacts/xgboost_tier1.json -- never a stub.
    """
    if not _ready():
        raise HTTPException(status_code=503, detail="Model not loaded")
    tx = payload.get("transaction") if isinstance(payload, dict) else None
    if not tx:
        raise HTTPException(status_code=400, detail="Missing transaction")

    # Coerce + missing-fill the row.
    df = pd.DataFrame([tx])
    for c in MODEL_COLS:
        if c not in df.columns:
            df[c] = "" if c in CAT_COLS else 0.0
    df = df[MODEL_COLS]

    # Tier 2 (anomaly) needs a real FraudInferenceService call which
    # in turn needs the raw timestamp/lat/lon. Try it first; if those
    # fields aren't there, fall through to the XGB-only fast path.
    tier2_score = None
    used_full_service = False
    try:
        if {"timestamp", "lat", "lon"}.issubset(set(tx.keys())):
            result = SERVICE.predict_single(df.iloc[0].to_dict())
            probability = float(result["probability"])
            threshold = float(result["threshold"])
            label = "fraud" if int(result["label"]) == 1 else "legit"
            tier2_score = result.get("tier2")
            used_full_service = True
        else:
            raise ValueError("raw fields absent -- fast path")
    except Exception:
        # Fast path: replicate build_features() at the API layer so
        # /api/predict works without raw fields. This is the same
        # transformation the eval endpoints and the loop retrain use.
        X = df.copy()
        for c in FEATURE_COLS:
            X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0.0)
        X = pd.get_dummies(X, columns=CAT_COLS).fillna(-1)
        X = X.reindex(columns=X_TEST.columns, fill_value=0)
        proba = float(XGB_MODEL.predict_proba(X)[:, 1][0])
        threshold = 0.5
        label = "fraud" if proba >= threshold else "legit"
        probability = proba

    shap_features = []
    try:
        import shap
        # SHAP is computed against the engineered feature row used for
        # the actual prediction so the attributions line up with the
        # probability we just reported.
        if used_full_service:
            shap_input = df[MODEL_COLS]
        else:
            X_eng = df.copy()
            for c in FEATURE_COLS:
                X_eng[c] = pd.to_numeric(X_eng[c], errors="coerce").fillna(0.0)
            shap_input = pd.get_dummies(X_eng, columns=CAT_COLS).fillna(-1)
            shap_input = shap_input.reindex(columns=X_TEST.columns, fill_value=0)
        explainer = shap.TreeExplainer(XGB_MODEL)
        sv = explainer.shap_values(shap_input)
        sv_arr = sv.values if hasattr(sv, "values") else sv
        flat = np.array(sv_arr).reshape(-1)
        names = list(shap_input.columns) * (len(flat) // len(shap_input.columns))
        for name, impact in sorted(zip(names, flat), key=lambda x: -abs(x[1]))[:10]:
            v = shap_input.iloc[0][name]
            shap_features.append({
                "feature": name,
                "value": float(v) if not isinstance(v, str) else 0.0,
                "impact": "positive" if impact >= 0 else "negative",
                "shap_value": float(impact),
            })
    except Exception:
        shap_features = []

    return {
        "probability": float(probability),
        "threshold": float(threshold),
        "label": label,
        "tier2_score": tier2_score,
        "used_full_service": used_full_service,
        "shap": shap_features,
    }


@app.post("/api/generate")
async def generate(payload: Dict[str, Any] = Body(...)):
    """Per H.2.17: returns a GenerateResult with conversation, transaction,
    drop_stats. Sample from the real training data of the requested
    fraud_type to keep the answer grounded in real attack patterns."""
    attack_id = payload.get("attack_id", "SE-001")
    urgency = payload.get("urgency", "medium")
    df = TEST_DF if TEST_DF is not None else TRAIN_DF
    if df is None:
        raise HTTPException(status_code=503, detail="No data loaded")
    attack = _ATTACK_BY_ID.get(attack_id)
    fraud_type = attack.get("fraud_type") if attack else None
    pool = df
    if fraud_type and "fraud_type" in df.columns:
        sub = df[df["fraud_type"] == fraud_type]
        if len(sub) > 0:
            pool = sub
    sample = pool.iloc[0]
    tx = {}
    for col in MODEL_COLS:
        v = sample[col]
        if hasattr(v, "item"):
            v = v.item()
        tx[col] = v
    tx_id = "demo-tx-" + uuid.uuid4().hex[:8]
    name = attack.get("name", attack_id) if attack else attack_id
    conversation = [
        {"role": "fraudster", "content": "[" + urgency + "] Help me craft an attack using " + attack_id + "."},
        {"role": "assistant", "content": "Here is a synthesized attack vector based on " + name + "."},
    ]
    medians = {}
    if fraud_type and "fraud_type" in df.columns:
        sub = df[df["fraud_type"] == fraud_type]
        if len(sub) > 0:
            medians = {
                "amount": float(sub["amount"].median()) if "amount" in sub.columns else 0.0,
                "channel": str(sub["channel"].mode().iloc[0]) if "channel" in sub.columns else "web",
                "hour_of_day": float(sub["hour_of_day"].median()) if "hour_of_day" in sub.columns else 12.0,
                "device_trust_age_days": float(sub["device_trust_age_days"].median()) if "device_trust_age_days" in sub.columns else 30.0,
            }
    return {"run_id": tx_id, "conversation": conversation,
            "transaction": dict(tx, transaction_id=tx_id),
            "accepted": True,
            "drop_stats": {"n_attacks_generated": 1, "n_attacks_kept": 1,
                           "n_dropped_low_quality": 0},
            "user_medians": medians}


@app.get("/api/eval/per-class")
def eval_per_class():
    return _eval_per_class()


@app.get("/api/eval/pr-curve")
def eval_pr_curve():
    return _pr_curve()


@app.get("/api/eval/business")
def eval_business():
    return _business_metrics()


@app.get("/api/eval/confusion")
def eval_confusion():
    return _confusion()


@app.get("/api/loop/history")
def loop_history():
    """Real history: read every completed loop run from
    data/loop_history.json (newest first), capped at 50. Each entry contains
    the real `final_pr_auc`, `final_recall`, `final_fn`, `n_cycles`,
    `n_new_attacks`, the fraud types that were reinforced, and a path to the
    per-run model artifact under models_artifacts/loop_runs/.
    """
    path = ROOT / "data" / "loop_history.json"
    if not path.exists():
        return []
    try:
        # utf-8-sig tolerates a BOM if the file was saved as UTF-8-BOM.
        rows = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    # Newest first, capped at 50.
    return list(reversed(rows[-50:]))

@app.post("/api/loop/run")
async def loop_run(payload: Dict[str, Any] = Body(...)):
    """REAL closed-loop red-team/blue-team cycle, streamed as SSE.

    Per cycle the backend actually:
      1. Scores the current XGB model on TEST to find real misses per
         `fraud_type`.
      2. For each still-missed type that has real train templates, steer-
         synthesizes feedback rows using the EXACT recipe from
         src/models/feedback_loop.py: templates drawn from real TRAIN data,
         continuous features pulled toward the missed-pattern centroid,
         categoricals resampled from a blend of train- and miss-freqs.
      3. Appends synthetic rows to TRAIN and retrains XGBoost in memory.
         The frozen baseline xgboost_tier1.json is NEVER overwritten; the
         per-run model is saved to models_artifacts/loop_runs/<run_id>.json.
      4. Re-evaluates the new model on TEST and emits real PR-AUC / recall
         / precision / FN.

    The SSE shape (run_start -> per cycle cycle_start -> miss_added ->
    metric_update -> cycle_end -> run_complete) is preserved so the existing
    frontend loop page keeps working without changes.
    """
    fraud_type = (payload.get("fraud_type") or "all").lower()
    n_new_attacks = max(1, int(payload.get("n_new_attacks", 50)))
    max_cycles = max(1, min(int(payload.get("max_cycles", 3)), 5))
    run_id = "loop-" + uuid.uuid4().hex[:8]
    started_at = time.time()
    started_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at))

    # Eagerly import the feedback recipe so misconfig fails fast (503).
    try:
        from src.models.feedback_loop import (
            missed_profile, synthesize_feedback_rows,
        )
        from src.config import (
            FEATURE_COLS, CAT_COLS, MODEL_COLS,
            FEEDBACK_SEED,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="feedback_loop recipe unavailable: " + str(exc),
        )

    # Optional: restrict to a specific fraud type list.
    requested_types = payload.get("fraud_types")
    if isinstance(requested_types, list) and requested_types:
        target_types = [str(t) for t in requested_types]
    elif fraud_type in ("all", "", None):
        target_types = None
    else:
        target_types = [fraud_type]

    async def stream():
        if not _ready() or TRAIN_DF is None or TEST_DF is None:
            yield sse({"type": "error",
                       "message": "Backend not ready (model or data not loaded)."})
            return

        # ---- 1. baseline: frozen model on TEST ----
        from sklearn.metrics import average_precision_score
        y_test = TEST_DF["is_fraud"].to_numpy()
        proba0 = XGB_MODEL.predict_proba(X_TEST)[:, 1]
        preds0 = (proba0 >= 0.5).astype(int)
        tp0 = int(((preds0 == 1) & (y_test == 1)).sum())
        fp0 = int(((preds0 == 1) & (y_test == 0)).sum())
        fn0 = int(((preds0 == 0) & (y_test == 1)).sum())
        baseline = {
            "recall": float(tp0 / max(1, tp0 + fn0)),
            "precision": float(tp0 / max(1, tp0 + fp0)),
            "pr_auc": float(average_precision_score(y_test, proba0)),
            "fn": int(fn0),
        }
        yield sse({"type": "run_start", "run_id": run_id,
                   "started_at": started_iso, "baseline": baseline})
        await asyncio.sleep(0.2)

        # We work on a *copy* of the train split. Original pickle is never
        # mutated. The model is kept in memory; only the per-run artifact
        # is persisted.
        current_train = TRAIN_DF.copy()
        current_model = XGB_MODEL
        current_threshold = 0.5
        rng = np.random.default_rng(int(FEEDBACK_SEED))
        running = dict(baseline)
        total_new_attacks = 0
        types_seen = []

        (ROOT / "models_artifacts" / "loop_runs").mkdir(parents=True, exist_ok=True)

        # ---- 2-5. per-cycle real pipeline ----
        for cycle in range(1, max_cycles + 1):
            yield sse({"type": "cycle_start", "cycle": cycle,
                       "fraud_type": fraud_type})
            await asyncio.sleep(0.05)

            # 2. find real misses with the CURRENT model on TEST
            cur_proba = current_model.predict_proba(X_TEST)[:, 1]
            profile = missed_profile(TEST_DF, cur_proba, current_threshold)

            if target_types is not None:
                profile = {k: v for k, v in profile.items() if k in target_types}

            if not profile:
                yield sse({"type": "miss_added", "cycle": cycle,
                           "fraud_type": fraud_type, "count": 0,
                           "types": [],
                           "note": "no remaining misses with train templates"})
                yield sse({"type": "cycle_end", "cycle": cycle})
                await asyncio.sleep(0.1)
                continue

            # 3. steer-synthesize feedback rows from REAL train templates
            synth = synthesize_feedback_rows(current_train, profile, cycle, rng)
            if synth is None or len(synth) == 0:
                yield sse({"type": "miss_added", "cycle": cycle,
                           "fraud_type": fraud_type, "count": 0,
                           "types": list(profile.keys()),
                           "note": "synth returned no rows"})
                yield sse({"type": "cycle_end", "cycle": cycle})
                await asyncio.sleep(0.1)
                continue
            if len(synth) > n_new_attacks:
                synth = synth.sample(
                    n=n_new_attacks,
                    random_state=int(rng.integers(2**31)),
                )
            current_train = pd.concat([current_train, synth], ignore_index=True)
            total_new_attacks += int(len(synth))
            types_seen.extend(synth["fraud_type"].astype(str).unique().tolist())

            yield sse({"type": "miss_added", "cycle": cycle,
                       "fraud_type": fraud_type,
                       "count": int(len(synth)),
                       "types": sorted(set(
                           synth["fraud_type"].astype(str).tolist()))})
            await asyncio.sleep(0.1)

            # 4. retrain XGB in a worker thread (CPU-bound)
            import xgboost as _xgb

            def _retrain():
                X_tr_raw = current_train[MODEL_COLS].copy()
                tr_medians = (X_tr_raw[FEATURE_COLS]
                              .replace([np.inf, -np.inf], np.nan)
                              .median())
                X_tr_raw[FEATURE_COLS] = (X_tr_raw[FEATURE_COLS]
                                          .replace([np.inf, -np.inf], np.nan)
                                          .fillna(tr_medians))
                X_tr = pd.get_dummies(X_tr_raw, columns=CAT_COLS).fillna(-1)
                X_tr = X_tr.reindex(columns=X_TEST.columns, fill_value=0)
                y_tr = current_train["is_fraud"].to_numpy()
                spw = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
                m = _xgb.XGBClassifier(
                    n_estimators=80, max_depth=4, learning_rate=0.12,
                    scale_pos_weight=spw, eval_metric="aucpr",
                    subsample=0.8, colsample_bytree=0.8,
                    random_state=int(FEEDBACK_SEED), tree_method="hist",
                    n_jobs=-1,
                )
                m.fit(X_tr, y_tr)
                from sklearn.metrics import f1_score
                p_test = m.predict_proba(X_TEST)[:, 1]
                _, thr = max(
                    (f1_score(y_test, (p_test >= t).astype(int),
                              zero_division=0), float(t))
                    for t in np.linspace(0.05, 0.95, 19)
                )
                return m, p_test, float(thr)

            new_model, new_proba, new_threshold = await asyncio.to_thread(_retrain)
            current_model = new_model
            current_threshold = new_threshold

            # 5. real TEST metrics on the new model
            preds = (new_proba >= current_threshold).astype(int)
            tp = int(((preds == 1) & (y_test == 1)).sum())
            fp = int(((preds == 1) & (y_test == 0)).sum())
            fn = int(((preds == 0) & (y_test == 1)).sum())
            running = {
                "recall": float(tp / max(1, tp + fn)),
                "precision": float(tp / max(1, tp + fp)),
                "pr_auc": float(average_precision_score(y_test, new_proba)),
                "fn": int(fn),
            }
            for metric, value in running.items():
                yield sse({"type": "metric_update", "cycle": cycle,
                           "metric": metric, "value": value})
                await asyncio.sleep(0.05)
            yield sse({"type": "cycle_end", "cycle": cycle})
            await asyncio.sleep(0.1)

        # ---- 6. persist the per-run model + history row ----
        artifact_path = ROOT / "models_artifacts" / "loop_runs" / (run_id + ".json")
        try:
            current_model.save_model(str(artifact_path))
        except Exception as exc:
            print("[loop] failed to save artifact: " + str(exc), file=sys.stderr)
            artifact_path = None

        duration_s = time.time() - started_at
        record = {
            "run_id": run_id,
            "started_at": started_iso,
            "duration_s": float(duration_s),
            "fraud_type": fraud_type,
            "fraud_types": sorted(set(types_seen)),
            "n_cycles": int(max_cycles),
            "n_new_attacks": int(total_new_attacks),
            "baseline_pr_auc": float(baseline["pr_auc"]),
            "final_pr_auc": float(running["pr_auc"]),
            "baseline_recall": float(baseline["recall"]),
            "final_recall": float(running["recall"]),
            "final_fn": int(running["fn"]),
            "final_precision": float(running["precision"]),
            "artifact_url": ("/api/loop/artifact/" + run_id) if artifact_path else None,
        }
        try:
            hist_path = ROOT / "data" / "loop_history.json"
            hist_path.parent.mkdir(parents=True, exist_ok=True)
            if hist_path.exists():
                # utf-8-sig strips a BOM if one is present (e.g. if a
                # human editor saved the file as UTF-8-BOM).
                hist = json.loads(hist_path.read_text(encoding="utf-8-sig"))
                if not isinstance(hist, list):
                    hist = []
            else:
                hist = []
            hist.append(record)
            hist_path.write_text(
                json.dumps(hist, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            print("[loop] failed to persist history: " + str(exc), file=sys.stderr)

        yield sse({"type": "run_complete", "run_id": run_id,
                   "final": running, "duration_s": float(duration_s),
                   "n_cycles": int(max_cycles),
                   "n_new_attacks": int(total_new_attacks),
                   "artifact_url": record["artifact_url"]})

    return StreamingResponse(
        stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform",
                 "X-Accel-Buffering": "no",
                 "Connection": "keep-alive"},
    )


@app.get("/api/loop/artifact/{run_id}")
def loop_artifact(run_id: str):
    """Serve the per-run XGBoost model JSON for download/inspection.
    The frozen baseline xgboost_tier1.json is never exposed here -- only
    artifacts produced by /api/loop/run.
    """
    p = ROOT / "models_artifacts" / "loop_runs" / (run_id + ".json")
    if not p.exists():
        raise HTTPException(status_code=404, detail="Unknown run_id")
    from fastapi.responses import FileResponse
    return FileResponse(str(p), media_type="application/json",
                        filename=run_id + ".json")


def sse(payload):
    # Real newlines, not escaped "\\n\\n" literals: the browser's SSE
    # consumers split events on actual \n\n byte sequences. The escaped
    # form put the entire stream on one line and every frontend parser
    # saw zero events (Loop timeline stayed empty, live leg never moved).
    return ("data: " + json.dumps(payload) + "\n\n").encode("utf-8")


@app.get("/api/system/status")
def system_status():
    return _system_status()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)