# fraud_model — Mastercard GenAI Payment Fraud Hackathon
## Identify / Generate / Defend

Temporal-split fraud detection on synthetic transaction data with a
two-tier detector, three data-generation paths, explainability, and a
closed retraining feedback loop.

## Pipeline order (run from repo root)

```
python src/features/engineering.py        # raw CSV -> transactions_features.pkl
python src/models/train.py                # temporal split + FROZEN baseline xgboost_tier1.json
python src/models/anomaly.py              # Tier 2: isolation forest (unsupervised)
python src/models/evaluate.py             # evaluation suite for frozen artifacts
python src/models/explain.py              # Tier 2: SHAP global + local explanations
python src/models/impersonation_diagnostics.py   # forensic audit of ai_impersonation misses

# Imbalance experiments (all write NEW files; nothing frozen is modified)
python src/models/smotenc_augment.py      # SMOTENC resampling of tiny fraud classes
python src/models/smotenc_train.py        # head-to-head: baseline vs SMOTENC vs CTGAN

# Feedback loop (Tier 2 item 8)
python src/models/feedback_loop.py        # missed val cases -> generator -> retrain -> test once
```

Data regeneration (only if you have LLM API/local access configured via .env):
`python src/generator/rule_generator.py` rebuilds `data/raw/transactions.csv`
and `transcripts.jsonl` end-to-end (rule-based simulator + LLM transcripts).

## Layout

```
data/raw/          transactions.csv, transcripts.jsonl, generation_log.csv
data/processed/    feature pickles + *_smotenc / *_ctgan / synthetic_feedback_rows audit files
models_artifacts/  xgboost_tier1.json (FROZEN baseline), *_smotenc/_ctgan/_feedback variants,
                   isolation_forest_tier2.joblib, shap_*.png
src/features/      engineering.py -- trailing-window velocity/aggregation features only
src/generator/     rule_generator.py (orchestrator + statistical attack simulators)
                   llm_generator.py (LLM transcript generation + validation)
src/models/        train / evaluate / anomaly / explain / impersonation_diagnostics
                   ctgan_augment, ctgan_train        -- CTGAN path (kept; see decision below)
                   smotenc_augment, smotenc_train    -- SMOTENC path (primary)
                   feedback_loop                     -- closed loop, playbook Tier 2 item 8
```

## Leakage discipline (enforced everywhere)

- Temporal train/val/test split (70/10/20 by timestamp) — never shuffled.
- Medians, encoders, scalers: fit on TRAIN only; val/test only transform.
- Thresholds frozen on VAL; TEST touched exactly once at final evaluation.
- Synthetic rows enter the TRAIN split only, and are auditable as files.
- Feature engineering uses trailing windows / prior-row state exclusively.

## Imbalance decision: SMOTENC primary, CTGAN kept for larger classes

Measured on the real run: CTGAN's own range-sanity gate rejected nearly
everything it generated at this row count — `train_df_ctgan.pkl` contains
only 2 accepted rows over the 149,546-row train set (ai_impersonation got
zero). A GAN cannot learn a distribution from tens of examples; SMOTENC's
k-NN interpolation degrades gracefully down to k+1 rows and honestly claims
interpolation, not new signal.

- `smotenc_augment.py` resamples the RAW frame BEFORE `pd.get_dummies()`
  (categoricals + 0/1 flags declared via `categorical_features`, so
  majority-vote keeps them valid — never "37% online / 63% POS" rows).
- Result: ai_impersonation PR-AUC 0.454 -> 0.596, overall PR-AUC
  0.9072 -> 0.9109, FN 34 -> 31 on the untouched test split.
- CTGAN scripts stay for classes that one day reach hundreds of real rows;
  both paths write separate pickles and compose cleanly.

## Feedback loop (playbook Tier 2 item 8)

`feedback_loop.py`: score the VAL split (production analog) -> extract
AGGREGATE missed-pattern stats -> synthesize new attack rows from REAL
train-split templates steered toward those misses -> retrain -> repeat ->
evaluate ONCE on test. Val rows are never copied into training; TEST never
informs anything until the final one-shot comparison. See CHANGELOG.md.

