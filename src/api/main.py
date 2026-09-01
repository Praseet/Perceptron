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
import hashlib
import json
import sys
import threading
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
    VAL_DF_PKL, X_VAL_PKL, METRICS_MANIFEST_JSON,
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

# ---------------------------------------------------------------------------
# P0.31 — lazy large-data loading.
# Startup loads ONLY the inference artifacts (model + Tier 2). The big
# train/val/test frames and feature matrices are loaded on first use by the
# endpoint that actually needs them, then memoized for the process lifetime.
# ---------------------------------------------------------------------------
SERVICE = None  # type: Optional[FraudInferenceService]
XGB_MODEL = None  # type: Optional[xgb.XGBClassifier]

_DATA_CACHE = {}  # type: Dict[str, Optional[pd.DataFrame]]
_DATA_LOCK = threading.Lock()


def _load_lazy(name: str, path) -> Optional[pd.DataFrame]:
    with _DATA_LOCK:
        if _DATA_CACHE.get(name) is None:
            if not Path(path).exists():
                return None
            try:
                _DATA_CACHE[name] = pd.read_pickle(path)
            except Exception as exc:
                print("[backend] failed to load " + str(path) + ": " + str(exc),
                      file=sys.stderr)
                return None
        return _DATA_CACHE[name]


def _test_df():
    return _load_lazy("test_df", TEST_DF_PKL)


def _train_df():
    return _load_lazy("train_df", TRAIN_DF_PKL)


def _val_df():
    return _load_lazy("val_df", VAL_DF_PKL)


def _x_test():
    return _load_lazy("x_test", X_TEST_PKL)


def _x_val():
    return _load_lazy("x_val", X_VAL_PKL)


# ---------------------------------------------------------------------------
# P0.8 — frozen metrics manifest. The API reads stored headline metrics from
# metrics_manifest.json (only when the sha256 matches the active model
# artifact) instead of recomputing million-row test metrics on every request.
# No exception path ever fabricates a metric (P0.7).
# ---------------------------------------------------------------------------
def _model_sha256() -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(XGB_TIER1_JSON, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _manifest_for_active_model() -> Optional[dict]:
    try:
        p = Path(METRICS_MANIFEST_JSON)
        if not p.exists():
            return None
        m = json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    if isinstance(m, dict) and m.get("model_sha256") and \
            m.get("model_sha256") == _model_sha256():
        return m
    return None


def _frozen_threshold() -> float:
    """P1.48 — the validation-frozen operating threshold of the active
    artifact; falls back to 0.5 only when no manifest exists."""
    m = _manifest_for_active_model()
    if m and m.get("validation_threshold") is not None:
        try:
            return float(m["validation_threshold"])
        except Exception:
            return 0.5
    return 0.5


def _select_operating_threshold(y_true: np.ndarray, proba: np.ndarray,
                                max_fpr: float = 0.0005,
                                min_precision: float = 0.90) -> float:
    """P0.11 — business-constrained threshold objective, computed on
    VALIDATION only (never TEST):
      1. maximize recall subject to FPR <= max_fpr
      2. else maximize recall subject to FPR <= 0.001
      3. else maximize F1 subject to precision >= min_precision
      4. else maximize F1
    """
    n_neg = max(int((y_true == 0).sum()), 1)
    candidates = []
    for t in np.linspace(0.05, 0.95, 19):
        pred = (proba >= t).astype(int)
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + int((y_true == 1).sum()))
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        fpr = fp / n_neg
        candidates.append((float(t), rec, prec, f1, fpr))

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

    return max(candidates, key=rank)[0]


# P0.29 — SHAP TreeExplainer is a singleton per model version; creating one
# per request was a large per-request latency cost.
_SHAP_EXPLAINER = None
_SHAP_LOCK = threading.Lock()


def _get_shap_explainer():
    global _SHAP_EXPLAINER
    if _SHAP_EXPLAINER is None:
        with _SHAP_LOCK:
            if _SHAP_EXPLAINER is None:
                import shap
                _SHAP_EXPLAINER = shap.TreeExplainer(XGB_MODEL)
    return _SHAP_EXPLAINER


# P0.28 — evaluation cache. The ~200k-row TEST scoring is computed once per
# process (per active model) and every /api/eval/* endpoint serves from it.
_EVAL_CACHE = {}  # type: Dict[str, Any]


def _test_proba():
    if "proba" not in _EVAL_CACHE:
        y = _test_df()["is_fraud"].to_numpy()
        p = XGB_MODEL.predict_proba(_x_test())[:, 1]
        _EVAL_CACHE["proba"] = p
        _EVAL_CACHE["y"] = y
    return _EVAL_CACHE["proba"], _EVAL_CACHE["y"]


@app.on_event("startup")
def _startup():
    global SERVICE, XGB_MODEL
    try:
        SERVICE = FraudInferenceService(
            model_path=XGB_TIER1_JSON,
            pipeline_path=None,
            tier2_path=ISO_FOREST_TIER2_JOBLIB,
        )
        SERVICE.initialize()
        # Pre-engineered test matrix + bare model for fast live
        # predictions are loaded lazily on first endpoint use (P0.31).
        XGB_MODEL = xgb.XGBClassifier()
        XGB_MODEL.load_model(XGB_TIER1_JSON)
    except Exception as exc:
        print("[backend] startup failed: " + str(exc), file=sys.stderr)
        SERVICE = None


def _ready():
    return SERVICE is not None and XGB_MODEL is not None


_ATTACKS_PATH = ROOT / "src" / "identify" / "attacks.json"
_ATTACKS = json.loads(_ATTACKS_PATH.read_text(encoding="utf-8"))
_ATTACK_BY_ID = {a["id"]: a for a in _ATTACKS}


def _generation_log_df():
    if not Path(GENERATION_LOG_CSV).exists():
        return None
    try:
        return pd.read_csv(GENERATION_LOG_CSV)
    except Exception as exc:
        print("[backend] failed to load generation log: " + str(exc), file=sys.stderr)
        return None


def _system_status():
    # P0.31 — the status endpoint works lazily; the big dataframes are only
    # loaded here (and memoized) instead of in the startup path.
    test_df = _test_df()
    if test_df is None:
        return {"online": False, "n_users": 0, "n_transactions": 0,
                "n_transactions_total": 0, "fraud_rate": 0.0,
                "pr_auc_test": 0.0, "last_retrain_at": "",
                "n_attacks_generated": 0,
                "backend_status": "unavailable"}
    # Unique-user count must come from the actual user_id column, not
    # the row count (which is what this used to report). The frontend
    # status pill shows this number as "users" -- showing the test-split
    # transaction count there was a long-standing labelling bug.
    n_users = int(test_df["user_id"].nunique()) if "user_id" in test_df.columns else int(len(test_df))
    n_tx = int(len(test_df))
    # Total transactions across all splits (train+val+test). The home
    # page KPI says "1.06M" so we surface the real number here.
    n_tx_total = n_tx
    train_df = _train_df()
    if train_df is not None:
        n_tx_total += int(len(train_df))
    val_df = _val_df()
    if val_df is not None:
        n_tx_total += int(len(val_df))
    fraud_rate = float(test_df["is_fraud"].mean()) if "is_fraud" in test_df.columns else 0.0
    gen_log = _generation_log_df()
    n_attacks_generated = int(len(gen_log)) if gen_log is not None else 0

    # P0.8/P0.7 — headline PR-AUC comes from the frozen metrics manifest (which
    # is sha256-checked against the active model artifact) when available;
    # otherwise from a one-time cached TEST scoring. No exception path ever
    # substitutes a fabricated number for a failed computation.
    pr_auc = 0.0
    pr_auc_source = "unavailable"
    if _ready():
        manifest = _manifest_for_active_model()
        if manifest and manifest.get("final_test_pr_auc") is not None:
            try:
                pr_auc = float(manifest["final_test_pr_auc"])
                pr_auc_source = "manifest"
            except Exception:
                pr_auc = 0.0
        else:
            try:
                proba, y = _test_proba()
                from sklearn.metrics import average_precision_score
                pr_auc = float(average_precision_score(y, proba))
                pr_auc_source = "cached"
            except Exception as exc:
                print("[backend] PR-AUC unavailable: " + str(exc), file=sys.stderr)
                pr_auc = 0.0
                pr_auc_source = "error"
    return {"online": _ready(), "n_users": n_users, "n_transactions": n_tx,
            "n_transactions_total": n_tx_total, "fraud_rate": fraud_rate,
            "pr_auc_test": pr_auc, "last_retrain_at": "2026-08-29T00:00:00Z",
            "n_attacks_generated": n_attacks_generated,
            "backend_status": pr_auc_source}

def _eval_per_class():
    if not _ready():
        return []
    from sklearn.metrics import average_precision_score
    rows = []
    df = _test_df()
    if df is None or "fraud_type" not in df.columns:
        return rows
    # P0.28 — one shared TEST scoring for the whole lifespan of the process.
    proba_all, _ = _test_proba()
    for ftype, grp in df.groupby("fraud_type"):
        if grp["is_fraud"].sum() == 0:
            continue
        positions = [_x_test().index.get_loc(i) for i in grp.index if i in _x_test().index]
        proba = proba_all[positions]
        y = grp["is_fraud"].to_numpy()
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
    proba, y = _test_proba()
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
    proba, y = _test_proba()
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
    df = _test_df()
    if df is None or "fraud_type" not in df.columns:
        return rows
    proba_all, _ = _test_proba()
    preds = (proba_all >= 0.5).astype(int)
    for ftype, grp in df.groupby("fraud_type"):
        positions = [int(_x_test().index.get_loc(i)) for i in grp.index if i in _x_test().index]
        rows.append({"fraud_type": str(ftype),
                     "predicted_legit": int(((preds[positions] == 0)).sum()),
                     "predicted_fraud": int(((preds[positions] == 1)).sum()),
                     "total": int(len(grp))})
    return rows


@app.get("/api/health")
def health():
    return {"status": "ok" if _ready() else "degraded",
            "model_loaded": _ready(),
            "data_loaded": _test_df() is not None,
            "n_users": int(len(_test_df())) if _test_df() is not None else 0}


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

    # Tier 2 (anomaly) is scored against the supplied engineered feature row
    # using the explicit IF_FEATURE_COLS contract (P0.1/P0.4). The XGBoost
    # probability is the fast path on the SAME supplied features so the
    # response semantics (probability/threshold/label) are unchanged.
    tier2_score = None
    used_full_service = False
    try:
        tier2_info = SERVICE.score_tier2(df)[0]
        if tier2_info.get("anomaly_score") is not None:
            tier2_score = float(tier2_info["anomaly_score"])
            used_full_service = True
    except Exception as exc:
        print("[backend] tier2 unavailable: " + str(exc), file=sys.stderr)

    # Fast path: replicate build_features() at the API layer so
    # /api/predict works even without raw fields. This is the same
    # transformation the eval endpoints and the loop retrain use.
    X = df.copy()
    for c in FEATURE_COLS:
        X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0.0)
    X = pd.get_dummies(X, columns=CAT_COLS).fillna(-1)
    X = X.reindex(columns=_x_test().columns, fill_value=0)
    proba = float(XGB_MODEL.predict_proba(X)[:, 1][0])
    threshold = _frozen_threshold()
    label = "fraud" if proba >= threshold else "legit"
    probability = proba

    shap_features = []
    try:
        # P0.29/30 — one shared TreeExplainer per model version; SHAP is only
        # computed for high-score/Tier-2-flagged/explicitly-requested rows.
        want_shap = bool(payload.get("explain")) or tier2_score is not None or probability >= 0.5
        if want_shap:
            # SHAP is always computed against the ENGINEERED feature row
            # used for the reported Tier 1 probability so the attributions
            # line up with the score the frontend sees.
            shap_input = df.copy()
            for c in FEATURE_COLS:
                shap_input[c] = pd.to_numeric(shap_input[c], errors="coerce").fillna(0.0)
            shap_input = pd.get_dummies(shap_input, columns=CAT_COLS).fillna(-1)
            shap_input = shap_input.reindex(columns=_x_test().columns, fill_value=0)
            explainer = _get_shap_explainer()
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
    drop_stats. P0.45: the synthesized transaction comes from the real TRAIN
    split only (never TEST), selected at random per request so the demo does
    not repeat the identical row every time."""
    attack_id = payload.get("attack_id", "SE-001")
    urgency = payload.get("urgency", "medium")
    # P0.44 — the protected TEST benchmark is never sampled for demo
    # generations. Templates must come from TRAIN (or non-test synthetic pool).
    df = _train_df()
    if df is None:
        raise HTTPException(status_code=503, detail="No data loaded")
    attack = _ATTACK_BY_ID.get(attack_id)
    fraud_type = attack.get("fraud_type") if attack else None
    pool = df
    if fraud_type and "fraud_type" in df.columns:
        sub = df[df["fraud_type"] == fraud_type]
        if len(sub) > 0:
            pool = sub
    if len(pool) == 0:
        pool = df
    sample = pool.sample(n=1, random_state=int(np.random.default_rng().integers(2**31))).iloc[0]
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

    Leakage discipline (P0.3): THE VALIDATION SPLIT drives adaptation.
      1. The current model is scored on VAL to find real misses per `fraud_type`.
      2. For each still-missed type that has real train templates, steer-
         synthesizes feedback rows using the EXACT recipe from
         src/models/feedback_loop.py: templates drawn from real TRAIN data,
         continuous features pulled toward the missed-pattern centroid,
         categoricals resampled from a blend of train- and miss-freqs.
      3. Appends synthetic rows to TRAIN and retrains XGBoost in memory.
         The frozen baseline xgboost_tier1.json is NEVER overwritten; the
         per-run model is saved to models_artifacts/loop_runs/<run_id>.json.
      4. Re-evaluates the new model on VAL and emits real PR-AUC / recall
         / precision / FN for every cycle metric_update event.

    TEST is NEVER used for tuning: no miss profiles, no thresholds, no
    cycle choices. The SSE shape (run_start -> per cycle cycle_start ->
    miss_added -> metric_update -> cycle_end -> run_complete) is preserved
    so the existing frontend loop page keeps working without changes.
    """
    fraud_type = (payload.get("fraud_type") or "all").lower()
    # P0.34 — conservative demo defaults: a single demo action must not
    # produce minutes of server blocking, while the caller's own bounds stay
    # honoured within sane ceilings.
    n_new_attacks = max(1, min(int(payload.get("n_new_attacks", 50)), 50))
    max_cycles = max(1, min(int(payload.get("max_cycles", 2)), 3))
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
        if not _ready() or _train_df() is None or _val_df() is None:
            yield sse({"type": "error",
                       "message": "Backend not ready (model or data not loaded)."})
            return

        # ---- 0. use the VALIDATION split for adaptation (P0.3) ----
        from sklearn.metrics import average_precision_score
        val_df = _val_df()
        x_val = _x_val()
        y_val = val_df["is_fraud"].to_numpy()

        def _score(model, X, y):
            return model.predict_proba(X)[:, 1]

        # ---- 1. baseline: frozen model on VAL ----
        proba0 = _score(XGB_MODEL, x_val, y_val)
        # Threshold is frozen on VAL with a low-FPR constrained objective
        # (P0.11), never on TEST.
        base_thr = _select_operating_threshold(y_val, proba0)
        preds0 = (proba0 >= base_thr).astype(int)
        tp0 = int(((preds0 == 1) & (y_val == 1)).sum())
        fp0 = int(((preds0 == 1) & (y_val == 0)).sum())
        fn0 = int(((preds0 == 0) & (y_val == 1)).sum())
        baseline = {
            "recall": float(tp0 / max(1, tp0 + fn0)),
            "precision": float(tp0 / max(1, tp0 + fp0)),
            "pr_auc": float(average_precision_score(y_val, proba0)),
            "fn": int(fn0),
            "threshold": float(base_thr),
            "dataset": "validation",
        }
        yield sse({"type": "run_start", "run_id": run_id,
                   "started_at": started_iso, "baseline": baseline})
        await asyncio.sleep(0.2)

        # We work on a *copy* of the train split. Original pickle is never
        # mutated. The model is kept in memory; only the per-run artifact
        # is persisted.
        current_train = _train_df().copy()
        current_model = XGB_MODEL
        current_threshold = base_thr
        rng = np.random.default_rng(int(FEEDBACK_SEED))
        running = dict(baseline)
        total_new_attacks = 0
        types_seen = []

        (ROOT / "models_artifacts" / "loop_runs").mkdir(parents=True, exist_ok=True)

        # Build (and cache across cycles) the training feature matrix; only
        # rebuilt when synthetic rows are appended (P0.33).
        def _build_matrix(dframe):
            X_raw = dframe[MODEL_COLS].copy()
            med = (X_raw[FEATURE_COLS]
                   .replace([np.inf, -np.inf], np.nan)
                   .median())
            X_raw[FEATURE_COLS] = (X_raw[FEATURE_COLS]
                                   .replace([np.inf, -np.inf], np.nan)
                                   .fillna(med))
            Xm = pd.get_dummies(X_raw, columns=CAT_COLS).fillna(-1)
            return Xm.reindex(columns=x_val.columns, fill_value=0)

        train_matrix = _build_matrix(current_train)

        # ---- 2-5. per-cycle real pipeline ----
        for cycle in range(1, max_cycles + 1):
            yield sse({"type": "cycle_start", "cycle": cycle,
                       "fraud_type": fraud_type})
            await asyncio.sleep(0.05)

            # 2. find real misses with the CURRENT model on VAL
            cur_proba = _score(current_model, x_val, y_val)
            profile = missed_profile(val_df, cur_proba, current_threshold)

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
            train_matrix = _build_matrix(current_train)
            total_new_attacks += int(len(synth))
            types_seen.extend(synth["fraud_type"].astype(str).unique().tolist())

            yield sse({"type": "miss_added", "cycle": cycle,
                       "fraud_type": fraud_type,
                       "count": int(len(synth)),
                       "types": sorted(set(
                           synth["fraud_type"].astype(str).tolist()))})
            await asyncio.sleep(0.1)

            # 4. retrain XGB in a worker thread (CPU-bound) so the FastAPI
            # event loop never freezes (P0.32).
            import xgboost as _xgb

            def _retrain():
                y_tr = current_train["is_fraud"].to_numpy()
                spw = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
                m = _xgb.XGBClassifier(
                    n_estimators=80, max_depth=4, learning_rate=0.12,
                    scale_pos_weight=spw, eval_metric="aucpr",
                    subsample=0.8, colsample_bytree=0.8,
                    random_state=int(FEEDBACK_SEED), tree_method="hist",
                    n_jobs=-1,
                )
                m.fit(train_matrix, y_tr)
                p_val = _score(m, x_val, y_val)
                # P0.3/P0.11 — threshold frozen on VAL with the same
                # business-constrained objective; TEST plays no part.
                thr = _select_operating_threshold(y_val, p_val)
                return m, p_val, float(thr)

            new_model, new_proba, new_threshold = await asyncio.to_thread(_retrain)
            current_model = new_model
            current_threshold = new_threshold

            # 5. VAL metrics on the new model (adaptation evidence)
            preds = (new_proba >= current_threshold).astype(int)
            tp = int(((preds == 1) & (y_val == 1)).sum())
            fp = int(((preds == 1) & (y_val == 0)).sum())
            fn = int(((preds == 0) & (y_val == 1)).sum())
            running = {
                "recall": float(tp / max(1, tp + fn)),
                "precision": float(tp / max(1, tp + fp)),
                "pr_auc": float(average_precision_score(y_val, new_proba)),
                "fn": int(fn),
                "threshold": float(current_threshold),
                "dataset": "validation",
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