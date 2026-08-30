# Session State — Adversarial Fraud Lab (AFL)
**Snapshot of where the project is RIGHT NOW. Read alongside FRONTEND_VISION.md when picking up in a new session.**

Written: 2026-08-28 (Day 1 of 3, deadline 2026-08-31)

---

## 1. Pipeline state — last verified

All run on the user's laptop with `python` (system Python, pyarrow 25.0.1) and `.venv\Scripts\python.exe` (XGBoost with CUDA 13.3, RTX 4050 Laptop GPU).

| Stage | State | Where |
|---|---|---|
| Raw data | **1,064,963 rows, 0.115% fraud (1,230 fraud tx across 7 types)** | `data/raw/transactions.csv` (179MB) + `data/raw/transactions.parquet` (45MB) |
| Anti-leakage audit | **All 7 fraud types PASS** (>5% overlap with normal IQR on all 4 key features) | last run: `python src/generator/anti_leakage.py` |
| Feature engineering | **1,064,963 rows x 35 cols**, pkl 357MB | `data/processed/transactions_features.pkl` |
| Trained model | **Tier 1 XGBoost on CUDA, early-stopped at 286/300 trees** | `models_artifacts/xgboost_tier1.json` |
| Test metrics | val PR-AUC **0.8073**, test PR-AUC **0.7971**, precision 0.85, recall 0.72 @ threshold 0.95 | from `python -m src.models.evaluate` |
| Splits | Train 745,474 / Val 106,496 / Test 212,993, fraud rates 0.114-0.122% (balanced) | `data/processed/{train,val,test}_df.pkl`, `data/processed/X_{train,val,test}.pkl` |
| Inference service | Exists, never exposed via HTTP. `FraudInferenceService.predict_single/predict_batch/get_business_metrics/health_check` | `src/fraud_model/inference.py` |
| Feedback loop | Exists and runnable: val recall 0.8200 -> 0.8467, FN 34 -> 32 | `src/models/feedback_loop.py`, `src/models/failure_analyzer.py` |