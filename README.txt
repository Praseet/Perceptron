# fraud_model — Mastercard GenAI Payment Fraud Hackathon
## Identify / Generate / Defend

Temporal-split fraud detection on synthetic transaction data with a
two-tier detector, SMOTENC augmentation, explainability, and a closed
retraining feedback loop.

## Pipeline order (run from repo root)

```
python src/features/engineering.py        # raw CSV -> transactions_features.pkl
python src/models/train.py                # temporal split + FROZEN baseline xgboost_tier1.json
python src/models/anomaly.py              # Tier 2: isolation forest (unsupervised)
python src/models/evaluate.py             # evaluation suite for frozen artifacts
python src/models/explain.py              # Tier 2: SHAP global + local explanations

# Imbalance experiments (all write NEW files; nothing frozen is modified)
python src/models/smotenc_augment.py      # SMOTENC resampling of tiny fraud classes
python src/models/smotenc_train.py        # head-to-head: baseline vs SMOTENC

# Feedback loop (Tier 2 item 8)
python src/models/feedback_loop.py        # missed val cases -> generator -> retrain -> test once
```

Data regeneration (only if you have LLM API/local access configured via .env):
`python src/generator/rule_generator.py` rebuilds `data/raw/transactions.csv`
and `transcripts.jsonl` end-to-end (rule-based simulator + LLM transcripts).

## Layout

```
data/raw/          transactions.csv, transcripts.jsonl, generation_log.csv
data/processed/    feature pickles + *_smotenc / synthetic_feedback_rows audit files
models_artifacts/  xgboost_tier1.json (FROZEN baseline), *_smotenc/_feedback variants,
                   isolation_forest_tier2.joblib, shap_*.png
src/features/      engineering.py -- trailing-window velocity/aggregation features only
src/fraud_model/   pipeline.py -- FraudPipeline (feature engineering + XGBoost)
                   inference.py -- production inference service
src/generator/     rule_generator.py (orchestrator + statistical attack simulators)
                   llm_generator.py (LLM transcript generation + validation)
src/models/        train / evaluate / anomaly / explain
                   smotenc_augment, smotenc_train    -- SMOTENC path (primary)
                   feedback_loop                     -- closed loop, playbook Tier 2 item 8
```

## Baseline metrics (frozen reference — DO NOT MODIFY)

**Dataset:** 213,638 total transactions
- normal: 212,387
- bustout_identity: 484
- card_testing: 363
- auth_bypass: 240
- account_takeover: 91
- ai_impersonation: 73

**Split (70/10/20 temporal by timestamp):**
- Train: 149,546
- Validation: 21,364
- Test: 42,728

**Tier 1 (XGBoost):**
- Validation PR-AUC: 0.9458
- Test PR-AUC: 0.9072
- Frozen threshold: 0.96
- Test Precision: 0.9044, Recall: 0.7834, F1: 0.8396
- FP: 13, FN: 34

**Tier 2 (Isolation Forest):**
- Test PR-AUC: 0.3356
- AI-impersonation PR-AUC: 0.0168 (hardest class for unsupervised)

**Observation:** AI impersonation is the hardest fraud type — only 12 test
transactions, 5 false negatives, PR-AUC 0.4538. SMOTENC augmentation
raises this to 0.596 (see CHANGELOG.md v1.1.0).

## Leakage discipline (enforced everywhere)

- Temporal train/val/test split (70/10/20 by timestamp) — never shuffled.
- Medians, encoders, scalers: fit on TRAIN only; val/test only transform.
- Thresholds frozen on VAL; TEST touched exactly once at final evaluation.
- Synthetic rows enter the TRAIN split only, and are auditable as files.
- Feature engineering uses trailing windows / prior-row state exclusively.

## Imbalance decision: SMOTENC primary

Measured on the real run: CTGAN's own range-sanity gate rejected nearly
everything it generated at this row count — it cannot learn a distribution
from tens of examples. SMOTENC's k-NN interpolation degrades gracefully
down to k+1 rows and honestly claims interpolation, not new signal.

- `smotenc_augment.py` resamples the RAW frame BEFORE `pd.get_dummies()`
  (categoricals + 0/1 flags declared via `categorical_features`, so
  majority-vote keeps them valid — never "37% online / 63% POS" rows).
- Result: ai_impersonation PR-AUC 0.454 -> 0.596, overall PR-AUC
  0.9072 -> 0.9109, FN 34 -> 31 on the untouched test split.

## Feedback loop (playbook Tier 2 item 8)

`feedback_loop.py`: score the VAL split (production analog) -> extract
AGGREGATE missed-pattern stats -> synthesize new attack rows from REAL
train-split templates steered toward those misses -> retrain -> repeat ->
evaluate ONCE on test. Val rows are never copied into training; TEST never
informs anything until the final one-shot comparison. See CHANGELOG.md.
