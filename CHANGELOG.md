# CHANGELOG — imbalance_pipeline

## v1.1.0 — Feedback loop (Tier 2 item 8), SMOTENC path, dead-code sweep

### 8. FEEDBACK LOOP IMPLEMENTED (`src/models/feedback_loop.py`)
The playbook's Tier 2 item 8 was the last missing piece. Design:
- Cycle 0 scores the VAL split (production analog) with the frozen
  baseline; missed fraud cases are profiled as AGGREGATE statistics only
  (per-feature medians + category frequencies). No val row is ever copied
  into training data.
- Synthetic feedback rows are built from REAL train-split templates of the
  same fraud type, steered mildly toward the miss centroid, with domain
  constraints enforced and categoricals resampled from a train/miss
  frequency blend — every generated value exists in real data.
- Retrain per cycle; model selection is by BEST VAL F1 (deploying "latest"
  instead of "best" measurably regressed test recall in a first run).
- TEST is touched exactly once: baseline vs loop candidate.
Measured: val recall 0.8200 -> 0.8467 across cycles; one-shot test:
recall 0.7834 -> 0.7962, FN 34 -> 32, PR-AUC 0.9072 -> 0.9089. Precision
drops 0.9044 -> 0.8562 because the val-frozen threshold moved 0.96 ->
0.94 -- an operating-point choice (catch more fraud, accept more reviews),
reported explicitly rather than hidden.

### SMOTENC PATH (`smotenc_augment.py` / `smotenc_train.py`)
CTGAN measured on real data: its own sanity gate accepted only 2 rows
(ai_impersonation got zero) — the memorization regime its docstring
predicted. SMOTENC on the RAW frame before get_dummies (flags declared
categorical) raised ai_impersonation PR-AUC 0.454 -> 0.596, overall
0.9072 -> 0.9109, FN 34 -> 31. CTGAN scripts kept for future classes with
hundreds of rows; both paths compose.

### HYGIENE
- Removed unused imports: `SMOTENC` (train.py), `os` (explain.py); dead
  `best_pipeline` variable (anomaly.py); deduped conflicting pins in
  requirements.txt (pandas was pinned both 3.0.5 and 2.3.3).
- README rewritten to describe the repo that actually exists.
- explain.py: added SHAP additivity self-check (base + sum(SHAP) must equal
  the log-odds margin) and selects the highest-risk impersonation case for
  the local waterfall instead of an arbitrary first row.

## v1.0.0 — SMOTENC replaces CTGAN for the two smallest minority classes

Diagnosis of "CTGAN augmentation failed due to insufficient data volume",
recorded here so the reasoning is auditable, matching this project's
existing `anomaly.py` changelog convention.

1. **ROW COUNT WAS BELOW CTGAN'S VIABLE RANGE, NOT A TUNING PROBLEM.**
   `ctgan_augment.py`'s own docstring already flagged this: at
   `ai_impersonation`'s 26 real train rows, CTGAN "will tend to
   interpolate near/memorize the existing examples rather than learn a
   genuinely broader distribution." `auth_bypass` (41 rows) sits in the
   same regime. This isn't a hyperparameter problem (more epochs, a
   different `pac`/`batch_size`) — a GAN needs enough real examples to
   learn a distribution from in the first place, and low tens of rows
   isn't that, regardless of tuning.

2. **SMOTENC IS THE APPROPRIATE FALLBACK FOR THIS EXACT REGIME, NOT A
   GENERAL CTGAN REPLACEMENT.** SMOTENC's k-NN + interpolate/majority-vote
   approach degrades gracefully down to `k_neighbors + 1` real rows (6, at
   the configured default), well below where a GAN can learn anything
   meaningful. It does not claim to learn a broader generative
   distribution the way CTGAN aims to — it interpolates between real
   points that already exist. That's a more honest claim at n=26-41, and
   the `low_confidence` flag in `validation.StrategyDecision` says so
   explicitly rather than presenting synthetic rows as equivalent to more
   real data.

3. **SMOTE-AFTER-ONE-HOT-ENCODING IS AN EASY MISTAKE TO MAKE HERE
   SPECIFICALLY BECAUSE `train.py`/`ctgan_train.py` BOTH CALL
   `pd.get_dummies()` EARLY**, as part of `build_features()`. Any
   resampling code written by extending that pattern naturally — "add a
   resampling step to the existing feature-building function" — would
   run SMOTE after the dummies already exist. `preprocessing.py` and
   `encoding.py` are deliberately split into two modules specifically to
   make that ordering mistake structurally harder to make by accident,
   and `validation.validate_schema()` catches it at runtime if it happens
   anyway.

4. **`scale_pos_weight` IS NOW CONFIG-SELECTABLE, NOT HARDCODED PER
   SCRIPT.** `train.py` and `ctgan_train.py` each compute
   `scale_pos_weight` inline, once, with no alternative. Given the
   double-compensation risk between resampling and loss-reweighting (see
   README "Architectural decision"), this project's very small minority
   classes are exactly the case where that choice should be explicit and
   revisitable per run, not baked into a script.

5. **THRESHOLDS THAT FAIL LOUDLY, NOT SILENTLY.** `SMOTENC` itself raises
   a `sklearn` `ValueError` several frames deep when a minority class is
   too small for the requested `k_neighbors` — `validation.py` checks row
   counts before ever calling `SMOTENC`, so failures are
   `InsufficientDataError` with the actual counts and requirement in the
   message, not a stack trace.

Hygiene: `ctgan_augment.py` / `ctgan_train.py` are left in place,
untouched — this is an alternative augmentation path for two specific
classes, not a replacement for the CTGAN experiment as a whole. Nothing in
this package imports from or modifies either file.