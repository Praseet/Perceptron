# Project Changelog & Architecture Evolution
### Mastercard GenAI Payment Fraud Hackathon — Identify / Generate / Defend

This document tracks all architectural modifications, code enhancements, bug fixes, and feature additions across the project lifecycle.

---

## [2026-08-24] — LM Studio Local Generator Fix

### Fixed `LOCAL_RESPONSE_FORMAT` NameError in `src/generator/llm_generator.py`
- **Issue**: `_structured_local` referenced undefined variable `LOCAL_RESPONSE_FORMAT` during local inference (LM Studio), causing `NameError` and forcing retries to fail.
- **Resolution**: Defined `LOCAL_RESPONSE_FORMAT = LOCAL_FRAUD_RESPONSE_FORMAT` alias and connected the schema to structured generation.

---

## [2026-08-24] — Tier 2 Tabular Defenses: SHAP Explainability & Isolation Forest Anomaly Detection

### 1. SHAP Explainability Module (Playbook Tier 2, Item 6)
- **File Created**: [`src/models/explain.py`](file:///c:/Users/HP/Desktop/fraud_model/src/models/explain.py)
  - **TreeSHAP Implementation**: Built `shap.TreeExplainer` on the trained XGBoost model to fulfill regulatory compliance and transaction-level risk decisioning.
  - **Global Feature Importance**: Exported global summary bar chart ([`models_artifacts/shap_importance_bar.png`](file:///c:/Users/HP/Desktop/fraud_model/models_artifacts/shap_importance_bar.png)) and beeswarm plot ([`models_artifacts/shap_summary_beeswarm.png`](file:///c:/Users/HP/Desktop/fraud_model/models_artifacts/shap_summary_beeswarm.png)).
  - **Top Global Drivers**: `new_merchant`, `amount`, `channel_card_present`, `time_since_last_s`, `three_ds_result_not_attempted`, and `amount_zscore_30d`.
  - **Local Transaction Attribution**: Implemented single-transaction waterfall plots showing exact log-odds feature pushes for detected fraud ([`models_artifacts/shap_waterfall_detected.png`](file:///c:/Users/HP/Desktop/fraud_model/models_artifacts/shap_waterfall_detected.png)) and AI Impersonation ([`models_artifacts/shap_waterfall_impersonation.png`](file:///c:/Users/HP/Desktop/fraud_model/models_artifacts/shap_waterfall_impersonation.png)).

---

### 2. Unsupervised Anomaly Detection (Playbook Tier 2, Item 5)
- **File Created**: [`src/models/anomaly.py`](file:///c:/Users/HP/Desktop/fraud_model/src/models/anomaly.py)
  - **Zero-Label Learning**: Trained `IsolationForest(n_estimators=250, contamination=0.015)` strictly on legitimate transactions (`is_fraud == 0`, 148,533 rows) from the training set.
  - **Zero-Day Benchmark**:
    - **Test Prevalence**: $0.00251$ (0.25% fraud baseline).
    - **Isolation Forest PR-AUC**: **$0.0507$** ($\sim 20\times$ above random prevalence without using a single fraud label).
    - **Validation-Frozen Threshold @ 0.40**: Precision: $0.0619$, Recall: $0.4486$, F1: $0.1087$.
  - **Artifact Saved**: Serialized to [`models_artifacts/isolation_forest_tier2.joblib`](file:///c:/Users/HP/Desktop/fraud_model/models_artifacts/isolation_forest_tier2.joblib).

---

### 3. Unified Defend Evaluation Suite
- **File Updated**: [`src/models/evaluate.py`](file:///c:/Users/HP/Desktop/fraud_model/src/models/evaluate.py)
  - **Comparative Benchmark**: Side-by-side comparison of Supervised XGBoost (Tier 1) vs. Unsupervised Isolation Forest (Tier 2) vs. Prevalence Baseline.
  - **XGBoost Operating Metrics (@ Frozen Validation Threshold = 0.94)**:
    - **Precision**: **$0.9785$** (only 2 false positives out of 42,607 legitimate test transactions; $\text{FPR} = 0.000047$).
    - **Recall**: **$0.8505$** (91 / 107 frauds caught).
    - **F1-Score**: **$0.9100$**.
    - **Test PR-AUC**: **$0.9533$** (vs. $0.0025$ prevalence baseline).
  - **Per-Fraud-Type Breakdown**:
    - `bustout_identity`: PR-AUC = **$0.9996$** (69/70 detected).
    - `ai_impersonation`: PR-AUC = **$0.7782$** (22/37 detected).
  - **Campaign-Level Recall**: **$68.09\%$** (32 / 47 multi-transaction fraud campaigns detected).

---

## [2026-08-23] — Phase 4 & Phase 4.5: GenAI Conversational Attack Generation & Integration

### 4. Environment & API Configuration
- **File Modified**: [`.env`](file:///c:/Users/HP/Desktop/fraud_model/.env)
  - **Resolution**: Configured Google Gemini / OpenAI keys in standard environment format.

### 5. LLM Conversational Attack Generator
- **File Updated**: [`src/generator/llm_generator.py`](file:///c:/Users/HP/Desktop/fraud_model/src/generator/llm_generator.py)
  - Upgraded to single-call structured JSON generation to prevent HTTP 429 rate limiting.
  - Persists full scam dialogues to [`data/raw/transcripts.jsonl`](file:///c:/Users/HP/Desktop/fraud_model/data/raw/transcripts.jsonl).

### 6. Rule & Scenario Generator Integration
- **File Modified**: [`src/generator/rule_generator.py`](file:///c:/Users/HP/Desktop/fraud_model/src/generator/rule_generator.py)
  - Fixed imports and deduplicated AI Impersonation loop.
  - Lineage logs saved to [`data/raw/generation_log.csv`](file:///c:/Users/HP/Desktop/fraud_model/data/raw/generation_log.csv).

---

## Core Baseline Features & Defense (Tier 1)
- **Causal Feature Pipeline**: [`src/features/engineering.py`](file:///c:/Users/HP/Desktop/fraud_model/src/features/engineering.py)
- **Temporal Train/Val/Test Split & XGBoost**: [`src/models/train.py`](file:///c:/Users/HP/Desktop/fraud_model/src/models/train.py)
- **Evaluation Suite**: [`src/models/evaluate.py`](file:///c:/Users/HP/Desktop/fraud_model/src/models/evaluate.py)

---

## Upcoming / Roadmap (Tier 3 & Presentation)
- [ ] **Tier 3 / Multi-Modal: NLP Scam Transcript Classifier (`src/models/nlp_detector.py`)**: Train on `transcripts.jsonl` to detect social engineering cues.
- [ ] **Multi-Modal Decision Fusion**: Combine XGBoost Tabular Risk + NLP Transcript Risk to eliminate the AI Impersonation false negative gap.
- [ ] **Tier 2: Closed Feedback Loop**: Retrain on missed cases to demonstrate adaptive learning.
- [ ] **Interactive Pitch Demo**: Streamlit application replaying scam chat $\rightarrow$ transaction authorization $\rightarrow$ real-time SHAP explanation.
