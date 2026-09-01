# AFL Backend ML Fixes & Enhancements — Submission-Day Priority Plan

**Scope:** Backend Python + ML/data-generation/backend inference only.

**Explicitly out of scope:** frontend code, frontend layout, frontend styling, frontend animation, LLM transcripts/conversation generation. The LLM transcript path is disabled and should remain disabled for the submission.

**Primary objective:** maximize the judged quality of the **Defend** pillar and strengthen the closed-loop **Generate → Defend → Adapt** story while keeping the current working prototype functional, numerically honest, and responsive.

**Priority order:** score/correctness first, then high-impact latency, then robustness/polish.

---

## How to use this document (read this first)

This file is one priority-ordered execution plan, not a menu of independent options — items are meant to be done in the order they appear. Before touching any code, read these four sections; they govern everything else in the file:

- **Section 21 — Guardrails the coding agent MUST obey** (hard limits: no frontend changes, no touching TEST during tuning, preserve the API contract, keep LLM transcripts disabled)
- **Section 20 — Feasibility gate for the coding agent** (how to decide whether an item is safe to attempt right now)
- **Section 24 — Highest-value shortlist if time gets extremely tight** (the 7 items to prioritize if the deadline forces a cutoff)
- **Section 25 — Exact implementation prompt for the agent** (ready-to-use prompt text)

The authoritative execution sequence is the **"Updated Submission-Day Priority Order"** at the very end of the file. Work through P0 → P1 → P2 in that order. Every item includes a current issue, a required fix, an acceptance test, and a feasibility verdict — treat the acceptance test as the definition of "done" for that item, not the code change alone.

---

## 0. Hackathon target to optimize against

The repository's `hackathon.md` states that the solution is evaluated on:

1. diversity of attacks identified
2. fidelity of simulated attacks
3. detection algorithm efficacy
4. novelty
5. real-world feasibility in live payments

The public Mastercard AI Garage description also frames the challenge as an end-to-end red-team / blue-team system: identify novel GenAI payment fraud, simulate it at scale, and defend against it in real time.

That means the best last-day work is **not** “make the code more complicated.” It is:

- repair anything that currently invalidates the model or metrics;
- improve the strongest detector with disciplined validation;
- make Isolation Forest useful as a real novelty/anomaly layer;
- make the feedback loop actually demonstrate adaptation without using the final test set as a tuning oracle;
- remove backend latency that makes the prototype appear stuck;
- preserve the endpoint contract and every number the existing UI consumes.

Mastercard has also publicly discussed hybrid fraud-defense systems combining conventional AI and newer tabular-model approaches, and emphasizes operating AI safely at scale. That makes a fast, auditable hybrid defense more aligned with the real-world feasibility criterion than a fragile “bigger model” experiment.

---

# 1. P0 — DO THESE FIRST: correctness / score blockers

These should be treated as submission blockers. They are more valuable than adding new ML ideas before submission because a broken or misleading evaluation can erase the value of a good model.

## [CRITICAL] P0.1 — Fix the Isolation Forest feature contract

**Current issue**

`src/models/anomaly.py` and `src/fraud_model/inference.py` use `select_dtypes("number")` for Tier 2 features. That is not a stable model schema. It can pull in columns such as:

- `is_fraud`
- `user_id`
- timestamp encoded as integer
- latitude / longitude
- other numeric metadata

The saved Isolation Forest artifact currently reports **26 input features**. The model is therefore coupled to whatever happened to be numeric in the dataframe at training time rather than to a deliberate anomaly-feature contract.

This is both a score problem and a production-inference problem.

**Required fix**

Create an explicit immutable `IF_FEATURE_COLS` list in `src/config.py`, containing only behaviorally meaningful numeric features.

Recommended initial set:

```text
amount
account_age_days
tx_last_1min
tx_last_1hr
tx_last_24hr
count_30d
amount_zscore_30d
new_device
new_merchant
merchant_cat_freq_user
time_since_last_s
dist_from_prev_km
geo_velocity_kmh
hour_of_day
three_ds_failures_before_result
three_ds_failures_last_30d
device_trust_age_days
burst_count_10m
is_high_amount_burst
inter_transaction_time_s
```

Do **not** include:

```text
is_fraud
fraud_type
case_id
transaction_id
user_id
ring_id
raw timestamp
```

Latitude/longitude should only be included if there is a demonstrated validation lift and they are treated as legitimate behavioral signals rather than identifiers. They should not be included merely because they are numeric.

Persist the feature list alongside the IF artifact.

**Why this matters**

A leakage-free IF with a smaller, behavior-focused feature space is much easier to reason about and often more effective than an IF polluted by identifiers and unrelated numeric metadata.

**Acceptance test**

- training and inference use exactly the same ordered feature list;
- length matches `n_features_in_`;
- `is_fraud` is absent;
- IDs and raw timestamps are absent;
- live `/api/predict` can score Tier 2 without falling back to Tier 1.

**Feasibility verdict:** **YES — very feasible and high value.**

---

## [CRITICAL] P0.2 — Fix the Isolation Forest config-path mismatch

`src/fraud_model/inference.py` looks for:

```text
isolation_forest_tier2_config.json
```

but the shipped artifact is:

```text
isolation_forest_config.json
```

The inference layer therefore cannot reliably load the frozen Tier 2 thresholds/configuration.

**Required fix**

Use `ISO_FOREST_CONFIG_JSON` from the centralized config instead of reconstructing a filename from the joblib path.

**Acceptance test**

`SERVICE.health_check()` reports a real Tier 2 threshold and does not silently use an empty/default threshold.

**Feasibility verdict:** **YES — tiny change, do immediately.**

---

## [CRITICAL] P0.3 — Eliminate test-set tuning from the API closed loop

The current `/api/loop/run` implementation explicitly scores the **TEST** split each cycle, mines misses from TEST, generates feedback from those misses, retrains, and evaluates again on TEST.

That conflicts with the stronger discipline already implemented in `src/models/feedback_loop.py`, which states:

> validation drives the loop; the final test is touched only at the end.

The two implementations must not disagree.

**Required fix**

The API loop should use:

```text
VAL_DF / X_VAL -> discover misses -> aggregate miss profile
TRAIN_DF      -> source legitimate templates
synthetic feedback -> append only to in-memory training copy
VAL_DF        -> retune threshold / verify improvement during cycles
TEST_DF       -> one-shot final comparison only
```

Do not copy individual validation rows into training. Continue using aggregated miss profiles and train-only templates, matching `src/models/feedback_loop.py`.

**Acceptance test**

A code/search audit of `src/api/main.py` shows the loop does not use TEST to create, steer, or choose training examples.

**Feasibility verdict:** **YES — critical consistency fix.**

---

## [CRITICAL] P0.4 — Make `/api/predict` actually use Tier 2 safely

The API currently tries the full inference service only if the request contains raw `timestamp`, `lat`, and `lon`. It then calls `SERVICE.predict_single()` with only `MODEL_COLS`, even though the full feature-engineering path expects additional raw fields.

Any failure falls into a silent Tier-1-only path.

This creates the dangerous state where the UI can appear to have a two-tier defense while many real requests are actually using one tier.

**Required fix**

Split inference into two explicit, stable paths:

```text
predict_from_preengineered_model_row()
predict_from_raw_transaction()
```

For `/api/predict`, always build the complete model row first, then call one canonical inference function. The Tier 2 feature builder must receive the same explicit `IF_FEATURE_COLS` used during training.

Do not silently hide a Tier-2 contract failure. Return a valid response, but include an internal diagnostic flag in logs/metrics so the failure can be caught during verification.

**Do not change the frontend-facing response keys.** Preserve at minimum:

```text
probability
threshold
label
tier2_score
used_full_service
shap
```

**Acceptance test**

The health-check transaction produces a non-null, finite Tier 2 score and the API prediction path does not raise or silently disable Tier 2.

**Feasibility verdict:** **YES — high value.**

---

## [CRITICAL] P0.5 — Fix the model/pipeline serialization contract

`src/fraud_model/pipeline/pipeline.py` can save a full pipeline with the feature transformer, but `load_model()` reconstructs the feature pipeline rather than restoring the exact fitted transformation state.

That means:

```text
train -> fit transformer -> model
save only model
load model -> rebuild transformer
```

is not guaranteed to reproduce the exact training transformation.

**Required fix**

For the production artifact, prefer one self-contained joblib artifact containing:

```text
feature_pipeline
model
training_columns / output feature schema
model version
feature-config hash
```

Keep the plain XGBoost JSON artifact for portability/comparison if needed, but make the live inference path use the exact bundled preprocessing artifact.

**Acceptance test**

For a deterministic sample batch:

```text
predict(before save/load) == predict(after save/load)
```

within floating-point tolerance.

**Feasibility verdict:** **YES, provided an existing pipeline artifact can be regenerated.**

---

## [CRITICAL] P0.6 — Fix `amount_zscore_30d` calculation

Both the lightweight feature path and the heavier transformer contain a variance calculation pattern that risks dividing the already-normalized variance by `(n-1)` again.

In `engineering.py`, the relevant path is effectively:

```text
sum2_30d = sample variance
z-score denominator = sqrt(sum2_30d / (count - 1))
```

That is mathematically inconsistent.

**Required fix**

Define one unambiguous convention:

```text
mean = trailing_amount_mean
variance = trailing_sum_squared_deviation / (n - 1)
std = sqrt(max(variance, epsilon))
z = (amount - mean) / std
```

Use the same implementation in every backend feature path.

**Why this matters**

`amount_zscore_30d` is explicitly one of the core behavioral features and can be especially useful for account takeover, bust-out, card testing and sudden-amount-shift attacks. A distorted z-score weakens both XGB and IF.

**Feasibility verdict:** **YES — important mathematical correction.**

---

## [CRITICAL] P0.7 — Remove all metric fallbacks that return fabricated numbers

`src/api/main.py` has an exception branch that returns a hardcoded PR-AUC value (`0.9072`) when metric calculation fails.

This is unacceptable for a competition artifact whose numbers are meant to be real.

**Required fix**

On calculation failure:

- retain a last-known computed cached metric only if it is explicitly stored as such;
- otherwise return a degraded/null metric plus a backend error status;
- never manufacture a metric.

**Important frontend compatibility rule:** preserve the response key and JSON type expected by the existing UI. A numeric field may be retained as `0.0` only when the API schema requires it, but also expose a backend status flag; never replace a failed computation with a false success number.

**Feasibility verdict:** **YES — tiny and essential.**

---

## [CRITICAL] P0.8 — Preserve one frozen test set and one frozen headline metric

There are currently multiple places where metrics can be calculated using different thresholds or different model variants.

Create a single `METRICS_MANIFEST`/JSON artifact containing:

```text
model_artifact
model_variant
training_data_version
feature_schema_version
validation_threshold
validation_pr_auc
validation_operating_precision
validation_operating_recall
final_test_pr_auc
final_test_precision
final_test_recall
final_test_f1
final_test_fp
final_test_fn
final_case_recall
```

The API should read the stored headline values for status/evaluation displays rather than repeatedly recomputing million-row test metrics on every request.

**Feasibility verdict:** **YES — extremely useful for both correctness and speed.**

---

# 2. P0 — Highest expected score improvement: train XGBoost better

The current baseline is already using XGBoost with `hist`, early stopping, `aucpr`, and a large `scale_pos_weight`. The largest remaining easy score opportunity is therefore **controlled validation-driven model selection**, not blindly adding more model complexity.

The captured baseline was approximately:

```text
Test PR-AUC ≈ 0.7971
Recall @ 0.95 ≈ 0.7231
Precision @ 0.95 ≈ 0.8545
FN ≈ 72
FP ≈ 32
```

The supplied artifacts also show strong degradation on several small fraud types, particularly `ai_impersonation` and `auth_bypass` in the captured baseline. The audit notes indicate generator drift and weak class signal are contributing factors.

---

## [CRITICAL] P0.9 — Run a compact XGBoost hyperparameter sweep on VAL only

Do not launch a gigantic search. Run a **small high-information sweep**.

Tune approximately:

```text
max_depth:        3, 4, 5, 6
min_child_weight: 1, 3, 5, 10
gamma:             0, 0.25, 1
subsample:         0.75, 0.9, 1.0
colsample_bytree:  0.75, 0.9, 1.0
learning_rate:     0.03, 0.05, 0.08
n_estimators:      600-1500 with early stopping
reg_alpha:         0, 0.1, 1
reg_lambda:        1, 5, 10
```

You do not need the full Cartesian product. Use 10–20 thoughtfully selected candidates.

**Selection metric**

Primary:

```text
validation PR-AUC
```

Secondary tie-breakers:

```text
recall at a fixed low-FPR operating point
precision at that operating point
per-type recall for the weakest important classes
case-level recall
```

Do not use TEST to choose the winner.

**Why this is likely better than simply increasing trees**

The current model is already near the 300-estimator ceiling (`best_iteration` around the high 200s in the captured training log). The important question is whether depth, regularization, row/column subsampling, and learning rate are currently suppressing or overfitting rare-fraud structure.

**Feasibility verdict:** **YES — one of the highest-value score experiments.**

---

## [CRITICAL] P0.10 — Search `scale_pos_weight` instead of assuming the raw class-ratio is optimal

The current trainer uses:

```text
negatives / positives
```

which produced a very large weight.

For extreme imbalance, the empirical ratio is a strong starting point, but it is not automatically optimal for PR-AUC or low-FPR business operation.

Search approximately:

```text
0.5 × empirical
0.75 × empirical
1.0 × empirical
1.25 × empirical
1.5 × empirical
```

Prefer the candidate that improves validation PR-AUC **and** does not materially worsen the chosen operating-point precision/FPR.

This is especially worth testing because the project cares about both strong detection and low false-positive rates.

**Feasibility verdict:** **YES — cheap experiment with potentially meaningful lift.**

---

## [HIGH] P0.11 — Use a business-constrained threshold objective rather than F1-only

Current threshold selection is largely F1-driven.

For payments, a more credible operating point is often:

```text
maximize recall
subject to FPR <= target
```

or:

```text
maximize F1
subject to precision >= target
```

Because the dataset is extremely imbalanced, F1 alone can prefer an operating point that is not representative of a real payment system.

Suggested validation objectives:

```text
maximize recall with FPR <= 0.0002
maximize recall with FPR <= 0.0005
maximize F1 with precision >= 0.90
maximize PR-AUC as the threshold-free ranking metric
```

Choose one frozen operating policy before final test.

**Feasibility verdict:** **YES — small change, much stronger evaluation story.**

---

## [HIGH] P0.12 — Train with the weakest fraud types receiving targeted emphasis

A global class weight treats all fraud as one minority class. The hackathon, however, explicitly cares about breadth and different emerging attacks.

Where validation evidence supports it, create a **row-level training weight** for the weakest fraud types, for example:

```text
base weight = normal class balance
ai_impersonation = base × 1.25–2.0
card_testing = base × 1.15–1.5
auth_bypass = base × 1.15–1.5
```

Do this only after observing validation behavior.

Do not fabricate class importance from the test set.

The objective is not to make one rare class dominate; it is to stop the model from effectively ignoring the classes with the highest judged novelty value.

**Feasibility verdict:** **YES — test as a controlled candidate, not blindly.**

---

## [HIGH] P0.13 — Evaluate a two-model XGBoost ensemble only if VAL improves

Train 2–3 diverse XGB candidates:

```text
Model A: current-ish depth/regularization
Model B: shallower + stronger regularization
Model C: slightly deeper + lower learning rate
```

Blend validation probabilities using a small convex search:

```text
0.5 A + 0.5 B
0.6 A + 0.4 B
0.7 A + 0.3 C
```

Choose the blend only when validation PR-AUC and the operating point improve.

Do not use an ensemble simply because it sounds stronger.

**Feasibility verdict:** **YES, but only after the single-model sweep.**

---

# 3. P0 — Fix SMOTENC so it helps rather than hurts

SMOTENC is already positioned correctly conceptually: raw model columns before one-hot encoding. Keep that design.

The question is whether the generated minority rows actually improve validation behavior.

---

## [HIGH] P0.14 — Compare SMOTENC models using validation PR-AUC and per-type recall

The current `smotenc_train.py` changes both the dataset distribution and the class weighting.

Run a controlled comparison:

```text
A. original train
B. SMOTENC train
C. SMOTENC train + tuned scale_pos_weight
```

Keep the exact same validation/test sets.

Select the best variant by validation criteria only.

**Important:** do not assume “more synthetic minority rows = better.” SMOTENC can improve rare classes while reducing precision or distorting the global decision boundary.

**Feasibility verdict:** **YES.**

---

## [HIGH] P0.15 — Use moderate, class-targeted SMOTENC rather than aggressive balancing

The current configuration targets:

```text
ai_impersonation -> 200
 auth_bypass      -> 200
```

That can be sensible, but do not force these classes toward anything resembling 50/50 or full balance.

Try one lighter candidate and one moderate candidate, then validate:

```text
original minority count × 2
original minority count × 4
```

Use validation PR-AUC + low-FPR recall to choose.

**Feasibility verdict:** **YES — very feasible.**

---

## [HIGH] P0.16 — Reject synthetic rows that become physically/business implausible

After SMOTENC and feedback synthesis, add cheap sanity checks:

```text
amount >= 0
counts >= 0
time_since_last_s >= 0
account_age_days > 0 where expected
geo_velocity_kmh not absurd
0/1 flags remain binary
categoricals remain in allowed vocabularies
```

Also check simple domain relationships such as:

```text
tx_last_1min <= tx_last_1hr <= tx_last_24hr <= reasonable upper bound
burst_count_10m <= tx_last_24hr
```

This improves training fidelity and prevents synthetic rows from teaching the model impossible patterns.

**Feasibility verdict:** **YES — strong quality multiplier.**

---

# 4. P0 — Isolation Forest: make Tier 2 actually useful

The current Tier 2 result is weak (`PR-AUC` approximately 0.005 in an earlier baseline and approximately 0.0046 in the supplied saved configuration). Therefore:

> Do not pretend IF is currently a strong classifier.

Instead, make it a **novel-behavior detector** whose job is complementary to XGB.

That is more faithful to the architecture and can still improve the overall defense.

---

## [CRITICAL] P0.17 — Train IF on normal transactions only and behavior-only features

Keep the unsupervised discipline:

```text
TRAIN_NORMAL_ONLY
```

Do not include labels or IDs.

Use the explicit IF feature contract from P0.1.

**Feasibility verdict:** **YES — required.**

---

## [HIGH] P0.18 — Add log-scaled features for heavily skewed anomaly dimensions

Isolation Forest is sensitive to large-scale numeric dimensions.

Candidate extra anomaly features:

```text
log1p_amount
log1p_tx_last_1hr
log1p_tx_last_24hr
log1p_count_30d
log1p_burst_count_10m
```

Do not just replace the existing feature; evaluate a version with and without log features.

A simple `log1p` transform is cheap and often gives an anomaly model a much saner geometry for heavy-tailed payment values.

**Feasibility verdict:** **YES — cheap experiment.**

---

## [HIGH] P0.19 — Tune IF on a small curated feature subset, not only on the whole feature set

Do three validation candidates:

```text
Behavior Core:
amount, amount_zscore_30d, tx_last_1min, tx_last_1hr,
tx_last_24hr, count_30d, time_since_last_s,
burst_count_10m, inter_transaction_time_s

Behavior + Device:
Behavior Core + new_device + device_trust_age_days

Behavior + Velocity:
Behavior Core + dist_from_prev_km + geo_velocity_kmh
```

Choose on validation PR-AUC / complementary-value criteria.

A smaller anomaly space can outperform a broad but noisy space.

**Feasibility verdict:** **YES.**

---

## [HIGH] P0.20 — Use IF as a calibrated/ranked complementary signal, not `max(prob, 0.9)`

Current inference effectively does:

```text
ensemble_proba = max(xgb_probability, 0.9 if anomaly else 0)
```

That is not a calibrated ensemble.

Use a validation-only blending method instead.

Recommended simple approach:

1. Convert XGB probability to rank/quantile or logit score.
2. Convert IF anomaly score to validation percentile/rank.
3. Search a small set of blend weights:

```text
0.9 XGB + 0.1 IF
0.8 XGB + 0.2 IF
0.7 XGB + 0.3 IF
0.6 XGB + 0.4 IF
```

4. Select on validation PR-AUC plus the chosen low-FPR operating point.

Alternatively, keep two separate decisions:

```text
XGB = primary fraud probability
IF  = novelty/anomaly escalation flag
```

This second design may be better if IF does not improve ranking.

**Feasibility verdict:** **YES — high-value only if validation proves complementarity.**

---

## [HIGH] P0.21 — Search IF `max_samples` and `max_features` around the actual data geometry

The current grid is:

```text
n_estimators: 200 / 400 / 600
max_samples: 128 / 256 / 512
max_features: 0.5 / 0.75 / 1.0
```

Once the feature contract is fixed, rerun a smaller focused search, for example:

```text
n_estimators: 200 / 400
max_samples: 256 / 512 / 1024
max_features: 0.5 / 0.75 / 1.0
```

Do not spend submission-day compute on hundreds of permutations.

**Feasibility verdict:** **YES.**

---

## [HIGH] P0.22 — Do not tune IF on contamination as if it changes ranking

Keep the correct principle already noted in `anomaly.py`:

`contamination` primarily controls the decision offset; it does not create new ordering information.

Tune:

```text
feature selection
feature transforms
n_estimators
max_samples
max_features
```

then freeze the operational threshold on validation.

**Feasibility verdict:** **YES — mostly a process correction.**

---

## [MEDIUM] P0.23 — Create an IF novelty score relative to normal validation behavior

Instead of showing the raw IF score, store a normalized percentile:

```text
novelty_percentile = percentile(rank among TRAIN_NORMAL)
```

This makes the output easier to combine with XGB and easier to explain in backend-generated results.

Preserve the existing `tier2_score` key for compatibility; you can add internal fields without requiring frontend changes.

**Feasibility verdict:** **YES.**

---

# 5. P0 — Feature engineering: one of the biggest hidden score + speed opportunities

The current heavy feature transformer contains per-user loops with repeated `past[...]` boolean masks. For a large user history, this approaches quadratic work within a user group.

This is a major backend speed opportunity.

---

## [CRITICAL] P0.24 — Replace O(n²)-style per-user rolling scans with vectorized/searchsorted windows

The current transformer repeatedly does patterns equivalent to:

```text
past = history[:j]
mask = past >= window
vals = history[:j][mask]
```

for every transaction.

That is unnecessarily expensive.

Replace with one of:

```text
pandas groupby + rolling/time-window operations
```

or a sorted NumPy two-pointer/searchsorted implementation.

For counts and sums:

```text
left_index = searchsorted(timestamp, timestamp_now - window)
count = j - left_index
sum = cumulative_sum[j] - cumulative_sum[left_index]
```

For squared sums:

```text
sum2 = cumulative_sq_sum[j] - cumulative_sq_sum[left_index]
```

This can transform feature generation from repeated per-row scans into near-linear work after sorting.

**Why this is a game changer**

The project uses around one million transactions. Faster feature generation makes:

- full regeneration faster;
- retraining iteration faster;
- closed-loop cycles faster;
- API raw-row inference less likely to stall.

It is one of the strongest speed optimizations available in the backend.

**Feasibility verdict:** **YES, but verify numerical equivalence carefully.**

---

## [HIGH] P0.25 — Replace repeated `df.assign(...).groupby(...)` feature calculations with vectorized group operations

For `merchant_cat_freq_user`, use a grouped cumulative count / cumulative row count rather than creating temporary dataframes and re-grouping.

Conceptually:

```text
same_user_category_prior_count
--------------------------------
prior_user_count
```

The result should preserve the “prior rows only” semantics.

**Feasibility verdict:** **YES — strong speed improvement.**

---

## [HIGH] P0.26 — Vectorize `device_trust_age` with grouped `shift`

Instead of maintaining a Python dictionary inside every user loop:

```text
device_trust_age = current_timestamp - previous_timestamp_for_same_device
```

sort by device/timestamp and use `groupby(device).shift()` where semantics allow it.

This can significantly reduce Python-level iteration.

**Feasibility verdict:** **YES, after carefully preserving causal ordering.**

---

## [HIGH] P0.27 — Compute geo distance/velocity only once per canonical feature pass

Avoid duplicating haversine/velocity calculations in both `engineering.py` and `transformers.py` where the same row has already been transformed.

Use one canonical backend feature implementation or a shared helper.

**Why**

Duplicate feature implementations are a correctness risk as well as a speed cost.

**Feasibility verdict:** **YES.**

---

# 6. P0 — Backend responsiveness / speed: major game changers

The goal here is not “make the UI faster by editing the UI.” The goal is to make backend endpoints return quickly and prevent long CPU work from blocking the server event loop.

---

## [CRITICAL] P0.28 — Cache all expensive evaluation results in the API

Current endpoints such as:

```text
/system/status
/eval/per-class
/eval/pr-curve
/eval/business
/eval/confusion
```

can recompute predictions/metrics over ~200k test rows each time.

That is an unnecessary repeated cost.

At startup or first request, calculate a versioned evaluation cache:

```text
XGB test probabilities
Y test labels
per-class metrics
PR curve
business table
confusion matrix
headline metrics
```

Then serve those cached arrays/metrics directly.

Invalidate the cache only when the active model artifact version changes.

**This is likely one of the largest direct responsiveness improvements.**

**Feasibility verdict:** **YES — do immediately.**

---

## [CRITICAL] P0.29 — Cache SHAP's `TreeExplainer`

Current `/api/predict` creates a new `shap.TreeExplainer(XGB_MODEL)` for each request.

That is expensive.

Use a module-level/lazy singleton:

```text
SHAP_EXPLAINER = None
```

Initialize once per model version.

**Feasibility verdict:** **YES — easy, potentially huge latency reduction.**

---

## [HIGH] P0.30 — Do not compute SHAP for every request unless required, while preserving the response contract

SHAP is explanation work, not the core fraud decision.

The backend can preserve the `shap` key but internally use a cheap explanation path for normal requests and full SHAP only when:

```text
fraud score is high
Tier 2 flags anomaly
explicit explanation requested
```

A further compatible approach is caching explanations for identical/common feature patterns only if that is actually useful.

**Important:** do not remove the existing `shap` response key if the current frontend consumes it.

**Feasibility verdict:** **YES — excellent responsiveness fix.**

---

## [CRITICAL] P0.31 — Stop loading entire train/val/test dataframes into API memory unless an endpoint actually needs them

`src/api/main.py` loads:

```text
TEST_DF
TRAIN_DF
VAL_DF
X_TEST
```

at startup.

That increases memory pressure and startup work.

Better design:

```text
startup:
  load model
  load small metric manifest
  load small attack metadata
  load only inference artifacts

lazy:
  load TRAIN/VAL/TEST dataframe only for loop/evaluation endpoints
```

If counts are needed for `/api/system/status`, store them in a small `dataset_manifest.json` generated by the pipeline.

**Feasibility verdict:** **YES — major memory and startup improvement.**

---

## [CRITICAL] P0.32 — Move long CPU/GPU work off the FastAPI event loop

`async def /api/loop/run` currently performs large synchronous model predictions, dataframe processing and XGBoost retraining inside the coroutine.

That can block all other requests.

Use a worker boundary such as:

```text
await asyncio.to_thread(cpu_bound_function, ...)
```

for appropriate work, or a dedicated background executor/process where practical.

Do not redesign the frontend. Preserve the existing SSE event format.

**Why it matters**

A backend can be computationally fast overall but still *feel frozen* if one request monopolizes the event loop.

**Feasibility verdict:** **YES — very high value.**

---

## [HIGH] P0.33 — Make loop cycle work incremental and avoid recomputing the same arrays

Within each loop cycle, cache:

```text
current_model predictions on VAL
current_model predictions on TEST only for final evaluation
feature matrices
miss masks
fraud-type group indices
```

Do not recreate or re-read the same large dataframe repeatedly.

**Feasibility verdict:** **YES.**

---

## [HIGH] P0.34 — Cap expensive demo-loop defaults while preserving the existing functionality

The API loop currently permits multiple cycles and multiple generated attacks.

Use conservative backend defaults suitable for a live demo:

```text
n_new_attacks: 20–50
max_cycles: 2–3
```

Keep caller-configured bounds valid.

The goal is not to weaken the functionality; it is to ensure one demo action does not produce minutes of server blocking.

**Feasibility verdict:** **YES — safe if response semantics stay identical.**

---

## [HIGH] P0.35 — Use mini-batches for API batch prediction

For large uploaded/internally generated batches, process in configurable chunks rather than creating one giant temporary array.

For example:

```text
chunk_size = 8192 / 16384 / 32768
```

Benchmark one or two values.

This reduces peak memory and can improve predictability.

**Feasibility verdict:** **YES.**

---

## [MEDIUM] P0.36 — Convert frequently reused dataframe slices to compact NumPy arrays

For pure numeric model paths, use:

```text
float32
```

where model precision allows it.

Do not convert categorical or timestamp data prematurely.

Potential wins:

- lower memory
- faster XGBoost transfer
- lower serialization overhead

**Feasibility verdict:** **YES, but benchmark and verify no metric regressions.**

---

## [MEDIUM] P0.37 — Warm-load XGBoost model and SHAP at startup only once

Do not repeatedly instantiate `XGBClassifier()` for the same model on every utility function.

Use one shared loaded model per model version.

**Feasibility verdict:** **YES — simple.**

---

# 7. P0 — Closed-loop training: make the submission story genuinely stronger

The core judging opportunity is not merely “we have an XGBoost model.” It is:

```text
model finds misses
→ misses become an aggregate weakness profile
→ generator creates new hard attacks from TRAIN templates
→ model retrains
→ validation verifies improvement
→ final held-out test proves the gain
```

The repository already contains much of this logic. The last-day work should make the API path match it.

---

## [CRITICAL] P0.38 — Unify `src/models/feedback_loop.py` and `/api/loop/run`

There should be exactly one feedback recipe.

The API should import the canonical functions rather than reimplementing the algorithm.

This prevents:

- test-set leakage
- feature drift
- threshold drift
- generator behavior differences
- metric inconsistencies

**Feasibility verdict:** **YES — one of the highest-value architecture fixes.**

---

## [HIGH] P0.39 — Generate hard examples from missed-pattern profiles, not by copying missed rows

Keep the existing principle:

```text
VAL miss statistics
        ↓
feature-level aggregate profile
        ↓
TRAIN templates
        ↓
steer synthetic rows toward weak region
```

Do not copy validation rows into training.

**Feasibility verdict:** **YES — already close to current design.**

---

## [HIGH] P0.40 — Use hard-negative mining as well as hard-positive mining

Fraud-only reinforcement can increase false positives if the model learns an overly broad boundary.

Add a small hard-negative profile:

```text
legitimate VAL rows with highest XGB score
```

Aggregate their feature statistics and ensure new training data still contains legitimate examples near those boundaries.

This is especially useful when optimizing for both:

```text
high recall
low FPR
```

**Feasibility verdict:** **YES — strong candidate if implementation stays simple.**

---

## [HIGH] P0.41 — Add diversity preservation to feedback synthesis

The feedback loop should not create 80 near-duplicates of one miss.

For each target fraud type, force diversity across a few axes:

```text
amount regime
channel
merchant category
3DS result
new device flag
burst intensity
velocity
transaction timing
```

A simple quota/binning strategy is sufficient; no new generative model is required.

**Feasibility verdict:** **YES — strong fit for the hackathon's diversity criterion.**

---

## [HIGH] P0.42 — Add a novelty gate before feedback rows enter training

For each candidate synthetic row, calculate a simple distance to existing TRAIN fraud examples.

Reject rows that are:

```text
identical
nearly identical across all features
physically impossible
outside allowed categorical vocabulary
```

The goal is to prevent feedback loops from collapsing into memorization.

**Feasibility verdict:** **YES — use a lightweight distance/hash gate, not a complicated model.**

---

## [HIGH] P0.43 — Track diminishing returns per cycle

For every cycle store:

```text
baseline validation PR-AUC
new validation PR-AUC
delta PR-AUC
validation recall
validation FPR
new attacks accepted
new attacks rejected
diversity score
```

Stop early when:

```text
PR-AUC gain <= epsilon
or
FPR worsens beyond tolerance
or
accepted diversity collapses
```

This saves compute and prevents overtraining the feedback loop.

**Feasibility verdict:** **YES.**

---

# 8. P0 — Improve data-generation fidelity without touching LLM transcripts

The user-requested scope explicitly excludes LLM transcripts. Keep them off.

The useful work is therefore **rule-based and statistical simulation quality**.

---

## [HIGH] P0.44 — Never sample demo generations from TEST

`/api/generate` currently prefers `TEST_DF`.

That is a poor closed-loop architecture even if the row is only used for display.

Use:

```text
TRAIN-derived template pool
or
non-test synthetic generator pool
```

The final test set should remain a protected benchmark.

**Feasibility verdict:** **YES — easy and important.**

---

## [HIGH] P0.45 — Replace `/api/generate` placeholder sampling with actual rule-generator invocation or canonical generator logic

Current `/api/generate` largely selects a real row and wraps it in a placeholder conversation.

Because transcripts are intentionally irrelevant, the endpoint should instead return a genuinely synthesized transaction generated by the rule engine.

Minimum structure:

```text
choose attack profile
choose train-derived template/state
mutate attack mechanics
build transaction
recompute dependent engineered features
quality gate
return transaction + drop_stats
```

Keep the current response contract so the existing prototype continues to work.

**Feasibility verdict:** **YES if the rule generator functions can be imported without bootstrapping the entire dataset generation script.**

---

## [HIGH] P0.46 — Recompute dependent features after mutation

If an attack generator changes:

```text
amount
timestamp/device/channel/merchant
location
3DS state
```

it must not leave stale:

```text
tx_last_1min
count_30d
amount_zscore_30d
geo_velocity_kmh
burst_count_10m
```

A stale feature vector can make generated attacks unrealistic and can make the detector learn the wrong relationship.

**Feasibility verdict:** **YES — high fidelity value.**

---

## [HIGH] P0.47 — Explicitly target the weak attack classes discovered by validation

The current baseline has particularly weak performance on some rare attack classes.

The generator should use those weaknesses as steering targets, not simply produce more rows of every class equally.

Example loop:

```text
identify weak class on VAL
→ inspect false negatives
→ derive miss profile
→ generate 20–50 harder variants
→ train candidate
→ re-score VAL
```

This is a much stronger adversarial-story mechanism than blind oversampling.

**Feasibility verdict:** **YES.**

---

# 9. P1 — Threshold, calibration and business metrics

Once the model candidate is chosen, improve how the backend selects and exposes its operating point.

---

## [HIGH] P1.48 — Store a frozen validation threshold with the model artifact

Persist:

```text
threshold
threshold_objective
validation_precision
validation_recall
validation_fpr
training timestamp
model hash
```

Inference should default to that threshold rather than hardcoding `0.5`.

**Feasibility verdict:** **YES.**

---

## [HIGH] P1.49 — Consider probability calibration only if it improves operating metrics

XGBoost probabilities need not be perfectly calibrated.

Evaluate a lightweight calibration layer on validation data:

```text
Platt/logistic calibration
or
isotonic calibration
```

Do not calibrate merely to make probabilities “look nice.”

The acceptance criterion should be whether calibration improves the chosen operational metric while preserving PR-AUC/ranking usefulness.

**Feasibility verdict:** **YES, but lower priority than the model sweep.**

---

## [MEDIUM] P1.50 — Add risk bands instead of relying on one naked probability

Backend can internally classify:

```text
low
review
high
block
```

based on the frozen operating policy.

This improves real-world feasibility and makes the defense behavior easier to reason about without requiring frontend changes.

**Feasibility verdict:** **YES.**

---

# 10. P1 — Backend robustness and artifact reproducibility

## [HIGH] P1.51 — Add an artifact manifest and dependency fingerprint

Persist:

```text
Python version
numpy version
pandas version
scikit-learn version
xgboost version
feature schema hash
model file hash
training seed
training split definition
```

The supplied IF joblib was loaded with sklearn-version mismatch warnings in the inspection environment. Re-exporting the artifact under the exact submission environment is preferable.

**Feasibility verdict:** **YES — especially important before submission.**

---

## [HIGH] P1.52 — Re-save Isolation Forest under the exact submission sklearn environment

The supplied joblib was created under a different sklearn patch environment than the one used for inspection, producing `InconsistentVersionWarning` messages.

For a reliable submission:

```text
train IF
save IF
load IF
run smoke inference
```

under the exact pinned environment in `requirements.txt`.

**Feasibility verdict:** **YES and strongly recommended.**

---

## [HIGH] P1.53 — Add a single backend smoke-test command

Create one command that verifies:

```text
models load
XGB predicts
IF predicts
/api/health equivalent check
/api/predict equivalent check
metrics manifest loads
feature dimensions match
thresholds load
```

The command should exit non-zero on any failure.

**Feasibility verdict:** **YES — excellent last-day safety net.**

---

## [MEDIUM] P1.54 — Make writes atomic for every critical model/metrics artifact

The project already does this for some files.

Extend the same pattern to:

```text
metrics manifest
IF config
threshold tables
loop history
feedback artifacts
```

**Feasibility verdict:** **YES.**

---

# 11. P1 — Keep every current frontend-facing number and endpoint correct

This section is intentionally backend-only: the agent must not edit the frontend. The backend must preserve the contract that the existing frontend depends on.

## [CRITICAL] Backend contract guardrail

Do not remove, rename or change the semantic meaning of existing response keys such as:

```text
/api/system/status
  online
  n_users
  n_transactions
  n_transactions_total
  fraud_rate
  pr_auc_test
  last_retrain_at

/api/predict
  probability
  threshold
  label
  tier2_score
  used_full_service
  shap

/api/generate
  run_id
  conversation
  transaction
  accepted
  drop_stats
  user_medians

/api/loop/run SSE
  run_start
  cycle_start
  miss_added
  metric_update
  cycle_end
  run_complete
```

The backend may improve how these values are computed, but it must not silently change their meaning.

### Numerical correctness rules

1. `pr_auc_test` must be computed from the actual frozen model/test artifact or a stored metric manifest generated from it.
2. `fraud_rate` must come from the actual evaluated split the endpoint claims to represent.
3. `n_users` must count unique users, not transactions.
4. `n_transactions_total` must reflect the documented data population and must not accidentally double-count.
5. loop metrics must indicate which dataset was used for cycle tuning and which was used for final evaluation.
6. threshold displayed by the backend must match the threshold used to compute the corresponding `label`/business metrics.
7. Tier 2 scores must be real when Tier 2 is claimed to be active.
8. No exception path may substitute a fabricated metric.

---

# 12. P1 — Evaluation improvements that can raise the judged score credibility

## [HIGH] P1.55 — Report PR-AUC prominently, not only accuracy/F1

With the project's extreme fraud imbalance, PR-AUC is materially more informative than raw accuracy.

Maintain the existing PR-AUC numbers and add:

```text
precision @ operating point
recall @ operating point
FPR @ operating point
case-level recall
per-fraud-type PR-AUC
per-fraud-type recall
```

**Feasibility verdict:** **YES.**

---

## [HIGH] P1.56 — Add case-level recall by fraud type

The current case-level recall is useful globally.

Add:

```text
bustout_identity case recall
card_testing case recall
account_takeover case recall
ai_impersonation case recall
auth_bypass case recall
...
```

This helps demonstrate the ability to catch campaigns rather than just individual transactions.

**Feasibility verdict:** **YES.**

---

## [MEDIUM] P1.57 — Add top-k capture metrics

For realistic payment operations, measure:

```text
fraud captured in top 10 alerts
fraud captured in top 50 alerts
fraud captured in top 100 alerts
```

This complements F1/PR-AUC and is useful for a human-review workflow.

**Feasibility verdict:** **YES.**

---

# 13. P1 — Data drift / anti-leakage checks

## [HIGH] P1.58 — Add train/val/test distribution-drift diagnostics

For each core numeric feature:

```text
train median
val median
test median
train std
val std
test std
```

For categorical features:

```text
train frequency
val frequency
test frequency
```

Flag extreme shifts.

This directly helps explain the currently observed generator drift and prevents the model from appearing “worse” when the actual cause is input distribution change.

**Feasibility verdict:** **YES — cheap and useful.**

---

## [HIGH] P1.59 — Keep the existing leakage guard and extend it to target-derived features

Current `leakage_guard.py` checks ID/case overlap.

Add a schema-level blocklist for training:

```text
is_fraud
fraud_type
case_id
transaction_id
ring_id
```

and assert they do not enter the XGB or IF feature matrices unless deliberately justified.

**Feasibility verdict:** **YES — highly recommended.**

---

# 14. P1 — Model error analysis that can lead directly to score improvements

## [HIGH] P1.60 — Build a compact false-negative profile by fraud type

For each validation miss class, calculate:

```text
feature mean/median for TP vs FN
feature distribution delta
categorical frequency delta
```

Then rank features by separation.

Feed those aggregate differences to the generator steering logic.

This closes the loop more rigorously than simply counting misses.

**Feasibility verdict:** **YES.**

---

## [HIGH] P1.61 — Build a compact false-positive profile

Do the same for legitimate transactions incorrectly flagged.

Use this to protect common legitimate patterns from being over-penalized by the next training cycle.

**Feasibility verdict:** **YES.**

---

## [MEDIUM] P1.62 — Slice performance by operational dimensions

Without changing the frontend, compute backend reports for:

```text
channel
merchant category
3DS result
amount bucket
hour of day
new-device state
```

This can reveal easy blind spots and guide feature weighting or generator mutations.

**Feasibility verdict:** **YES.**

---

# 15. P2 — Additional speed optimizations if the P0 work is complete

These are worthwhile but should never delay a higher-priority correctness/model improvement.

## [MEDIUM] P2.63 — Memory-map large immutable matrices where practical

For very large model matrices, consider a compact on-disk array format rather than repeatedly deserializing full DataFrames.

This is most useful for repeated loop/evaluation workflows.

**Feasibility verdict:** **ONLY if already comfortable with the data layout.**

---

## [MEDIUM] P2.64 — Use float32 for XGB feature matrices

Convert numeric training matrices to `float32` before XGBoost where supported.

This usually reduces memory and can improve data-transfer speed.

**Feasibility verdict:** **YES — verify no material score regression.**

---

## [MEDIUM] P2.65 — Reuse one-hot/categorical schema

Rather than repeatedly calling `pd.get_dummies()` on every split and every backend request:

```text
fit categorical vocabulary once
transform by schema
```

`OneHotEncoder(handle_unknown="ignore")` is a good fit for this.

This also improves consistency between training and inference.

**Feasibility verdict:** **YES.**

---

## [MEDIUM] P2.66 — Avoid Python imports inside hot endpoints

The API imports some metrics/SHAP utilities inside request handlers.

Move stable imports to module scope or lazy-load once at startup.

This is not a giant optimization by itself, but it removes repeated overhead.

**Feasibility verdict:** **YES.**

---

## [LIGHT] P2.67 — Reduce unnecessary logging of giant objects

Keep useful timing and metric logs, but avoid dumping full dataframes or full exception traces on normal successful requests.

Recommended structured timing fields:

```text
prediction_ms
feature_ms
shap_ms
iforest_ms
loop_cycle_ms
```

**Feasibility verdict:** **YES.**

---

## [LIGHT] P2.68 — Add backend timing telemetry per endpoint

Log:

```text
/api/predict p50/p95-ish rolling latency
/api/eval/* latency
/api/generate latency
/api/loop cycle duration
```

This makes bottlenecks measurable before submission.

**Feasibility verdict:** **YES.**

---

# 16. P2 — Real-world payment feasibility improvements

## [HIGH] P2.69 — Make decision latency observable

Expose internally:

```text
feature_build_ms
xgb_ms
if_ms
ensemble_ms
explanation_ms
total_ms
```

A live-payment defense claim is much stronger when the backend can demonstrate where time is spent.

**Feasibility verdict:** **YES.**

---

## [MEDIUM] P2.70 — Add fail-open/fail-review/fail-safe configuration semantics

For model failure, explicitly define what the backend does:

```text
Tier 1 unavailable
Tier 2 unavailable
explanation unavailable
```

Never confuse “explanation unavailable” with “model unavailable.”

The decision engine should degrade deterministically.

**Feasibility verdict:** **YES — good production hardening.**

---

# 17. What NOT to spend submission-day time on

## [LIGHT] Do not reactivate LLM transcripts

They are intentionally off and are not required for the core hackathon pillars.

Use the rule/statistical generator instead.

## [LIGHT] Do not add a new deep-learning model just because it is newer

A better-controlled XGBoost + IF hybrid with clean validation is more useful today.

## [LIGHT] Do not add a large hyperparameter sweep

A 10–20 candidate intelligent sweep is better than hours of blind search.

## [LIGHT] Do not tune on TEST

Not for thresholds, not for feature selection, not for loop steering, not for choosing an ensemble.

## [LIGHT] Do not inflate synthetic dataset size without fidelity checks

More rows are not automatically better.

## [LIGHT] Do not rebuild the public API contract

Preserve endpoint shapes and field meanings.

## [LIGHT] Do not modify frontend files

All improvements in this document are backend-only.

---

# 18. Recommended submission-day execution order

This is intentionally ordered by expected payoff, not conceptual elegance.

### Wave A — Must-fix blockers

1. **Fix IF feature contract + remove label/ID leakage.**
2. **Fix IF config-path loading.**
3. **Fix API loop to use VAL for adaptation and TEST only for final evaluation.**
4. **Fix `/api/predict` so Tier 2 actually runs under the canonical feature contract.**
5. **Fix `amount_zscore_30d`.**
6. **Remove fabricated metric fallbacks.**
7. **Create one metrics/model manifest.**

### Wave B — Highest expected model score gains

8. **Run compact XGBoost hyperparameter sweep.**
9. **Search `scale_pos_weight`.**
10. **Select threshold using a low-FPR constrained objective.**
11. **Evaluate moderate SMOTENC variants.**
12. **Add targeted weighting for weak fraud types if validation supports it.**
13. **Try a 2-model blend only if validation improves.**

### Wave C — Game-changing backend speed

14. **Cache all expensive evaluation results.**
15. **Cache SHAP explainer.**
16. **Move loop CPU work off the FastAPI event loop.**
17. **Stop eagerly loading all large dataframes in the API.**
18. **Vectorize feature-engineering rolling windows.**
19. **Reuse model/feature matrices between loop cycles.**

### Wave D — Make the closed loop stronger

20. **Unify API loop with canonical feedback_loop.py.**
21. **Add hard-negative mining.**
22. **Add diversity quotas.**
23. **Add synthetic novelty/quality gate.**
24. **Replace `/api/generate` TEST sampling with real TRAIN-derived rule-based generation.**
25. **Recompute all dependent features after mutation.**

### Wave E — Final verification

26. **Re-save all artifacts under the exact submission environment.**
27. **Run leakage guard.**
28. **Run backend smoke test.**
29. **Run frozen final test once.**
30. **Verify every API metric comes from the final chosen artifact.**

---

# 19. Suggested score-oriented decision rule

Do not choose the model with the highest single metric blindly.

Use this hierarchy:

```text
1. No leakage / correct artifact
2. Highest VAL PR-AUC
3. Strong recall at a very low FPR
4. Strong precision at the chosen operating point
5. Better weak-class / case-level recall
6. Better closed-loop validation improvement
7. Lower inference latency
```

A candidate that gains 0.01 PR-AUC but increases FPR dramatically may be worse for the actual challenge than a slightly lower PR-AUC candidate with much stronger precision/recall balance.

---

# 20. Feasibility gate for the coding agent

The implementation agent MUST NOT blindly execute every item.

For each proposed change, it must first perform a **brief feasibility check** answering:

```text
FEASIBILITY CHECK
- What files will change?
- What existing behavior could this break?
- Can it be implemented without changing the frontend?
- Can it preserve existing API response keys and meanings?
- Can it be validated with the current repository/artifacts?
- Is there a realistic chance of improving score, latency, correctness, or robustness?
- What is the rollback path if validation gets worse?

DECISION: IMPLEMENT / SKIP
REASON: 1–3 sentences maximum
```

Only after `IMPLEMENT` should the agent modify code.

---

# 21. Guardrails the coding agent MUST obey

## Frontend boundary

```text
DO NOT edit frontend files.
DO NOT change frontend API expectations.
DO NOT redesign frontend routes/components.
DO NOT change the meaning of data returned to the frontend.
```

## Test-set boundary

```text
TEST is read-only for tuning.
TEST is never used to create training rows.
TEST is never used to choose features.
TEST is never used to choose hyperparameters.
TEST is never used to choose the ensemble.
TEST is never used to choose the operating threshold.
TEST may be used only for final evaluation / reporting checkpoints.
```

## Model integrity

```text
Never include is_fraud as a feature.
Never include transaction_id/case_id/ring_id as model features.
Never let train/val/test feature schemas drift.
Never use a different feature order at inference.
Never silently fall back from Tier 2 without diagnostic logging.
```

## API integrity

Preserve existing endpoint paths and response keys. Improvements must be backend-internal whenever possible.

## LLM boundary

```text
LLM transcript generation stays disabled.
Do not spend implementation time on transcript activation.
```

---

# 22. Validation checklist after every significant ML change

A candidate model is not accepted until all of the following are checked:

```text
[ ] train/val/test schema matches
[ ] leakage guard passes
[ ] no forbidden identifier/label feature present
[ ] validation PR-AUC calculated
[ ] validation operating metrics calculated
[ ] per-fraud-type metrics calculated
[ ] case-level metrics calculated
[ ] synthetic-row quality gate passes where synthetic data changed
[ ] final test not used for selection
[ ] model artifact loads cleanly
[ ] API smoke prediction works
[ ] Tier 2 smoke prediction works
[ ] metric manifest regenerated
[ ] frontend-facing response keys preserved
```

---

# 23. Minimum “done” definition for the submission

The backend is ready when:

1. Tier 1 XGBoost has been selected from a disciplined validation experiment rather than arbitrary parameters.
2. The operating threshold is frozen using validation only.
3. Isolation Forest has an explicit leakage-free feature contract and actually loads at inference.
4. The API closed loop uses validation for adaptation and does not tune on TEST.
5. Evaluation results are cached rather than recomputed on every endpoint hit.
6. SHAP explainer is cached.
7. Long loop work cannot monopolize the FastAPI event loop.
8. `/api/generate` does not sample the protected test set.
9. Model/metric artifacts have reproducible version information.
10. Existing frontend-facing API fields and numerical semantics still work unchanged.

---

# 24. Highest-value shortlist if time gets extremely tight

If only a handful of changes can be completed, do these in order:

### 1. **Fix IF feature schema + config path + live inference**

This turns Tier 2 from a fragile/mostly-disabled path into a real backend component.

### 2. **Fix API loop test leakage**

This is crucial for the credibility of the closed-loop story.

### 3. **Run XGBoost validation sweep + scale_pos_weight sweep**

This is the strongest realistic path to an actual score increase.

### 4. **Freeze threshold using low-FPR validation objective**

This aligns the model with payment-defense reality.

### 5. **Cache eval + SHAP + model objects**

This can dramatically reduce “backend feels stuck” moments without touching the frontend.

### 6. **Vectorize the feature-engineering hot loops**

Potentially the largest raw speed improvement in the whole backend.

### 7. **Use canonical feedback loop and TRAIN-derived generation only**

This strengthens both methodological credibility and the hackathon's closed-loop narrative.

---

# 25. Exact implementation prompt for the agent

Use the following prompt verbatim with the coding agent:

```text
You are improving ONLY the backend Python/ML side of this project for the submission today.

IMPORTANT SCOPE BOUNDARY:
- Do NOT edit any frontend files.
- Do NOT change frontend routes/components/styling/animations.
- Do NOT redesign the frontend.
- Preserve every existing backend API endpoint path and every frontend-facing response key/semantic meaning.
- Do NOT reactivate LLM transcript generation. It is intentionally disabled and irrelevant to the required submission.

Your goal is to improve, in order:
1. correctness / leakage safety,
2. actual detection score,
3. Isolation Forest usefulness,
4. closed-loop training quality,
5. backend speed/responsiveness,
6. reproducibility and robustness.

You MUST read the relevant existing backend code and artifacts before changing them.

For EVERY proposed fix, first do this brief check:

FEASIBILITY CHECK
- files affected:
- possible breakage:
- frontend/API compatibility risk:
- measurable benefit expected:
- validation available:
- rollback:
DECISION: IMPLEMENT or SKIP
REASON: 1–3 sentences.

Only implement fixes you judge genuinely feasible today. Do not attempt speculative rewrites or huge architectural migrations.

PRIORITY 0 — FIX THESE FIRST

1. Isolation Forest feature contract
- Add one explicit IF_FEATURE_COLS list in src/config.py.
- Exclude is_fraud, fraud_type, case_id, transaction_id, ring_id, user_id and raw timestamp.
- Use the exact same ordered list in training and inference.
- Persist the feature schema with the IF artifact/config.
- Verify n_features_in_ matches the feature contract.

2. Isolation Forest config loading
- Stop constructing isolation_forest_tier2_config.json from the joblib filename.
- Use the centralized ISO_FOREST_CONFIG_JSON path.

3. Fix live Tier 2 API inference
- /api/predict must not silently become XGB-only because the raw/engineered feature contract is inconsistent.
- Build the required row once, then run Tier 1 + Tier 2 using the exact trained schemas.
- Keep existing response keys: probability, threshold, label, tier2_score, used_full_service, shap.

4. Fix closed-loop test leakage
- /api/loop/run must use VAL to discover misses and steer training.
- Use TRAIN-only templates for synthetic feedback.
- TEST must be held out and used only for final evaluation.
- Unify the API loop with src/models/feedback_loop.py instead of duplicating the algorithm.

5. Fix amount_zscore_30d
- Use one mathematically correct variance/std implementation.
- Ensure all backend feature paths use the same definition.
- Verify numerical reasonableness on sample rows.

6. Remove fabricated metrics
- Never return hardcoded PR-AUC/metrics on exception.
- Return degraded status or last-known cached real metric with explicit status.

7. Build a model/metric manifest
- Record artifact path/version, feature schema, validation threshold, validation metrics, final test metrics, environment versions and model hash.
- API status/evaluation endpoints should read cached manifest/metrics where possible.

PRIORITY 0 — SCORE IMPROVEMENT

8. Run a COMPACT XGBoost validation sweep, not a giant search.
Test around:
- max_depth 3/4/5/6
- min_child_weight 1/3/5/10
- gamma 0/0.25/1
- learning_rate 0.03/0.05/0.08
- subsample 0.75/0.9/1.0
- colsample_bytree 0.75/0.9/1.0
- modest reg_alpha/reg_lambda variations
- 600–1500 estimators with early stopping
Use only 10–20 intelligent candidate configurations, not the full Cartesian product.

Primary model-selection metric:
- validation PR-AUC.
Secondary:
- recall at low FPR,
- precision at operating point,
- weakest fraud-type recall,
- case-level recall.
NEVER use TEST to choose the winner.

9. Search scale_pos_weight around the empirical ratio:
0.5x, 0.75x, 1x, 1.25x, 1.5x.
Select on validation only.

10. Consider a small amount of fraud-type-targeted weighting only for weak classes if validation shows it helps. Do not blindly over-weight rare classes.

11. Compare baseline vs moderate SMOTENC vs tuned-SMOTENC using the same untouched VAL/TEST sets. Do not assume synthetic balancing helps.

12. Choose the operating threshold on VAL with a payment-oriented objective, preferably maximize recall subject to a low FPR constraint, while still reporting PR-AUC/F1.

PRIORITY 0 — ISOLATION FOREST

13. Retrain IF after fixing the feature contract using normal TRAIN rows only.

14. Evaluate compact IF feature sets:
- core behavior,
- behavior + device,
- behavior + velocity.

15. Consider log1p variants for heavily skewed features.

16. Tune IF structural parameters modestly: n_estimators, max_samples, max_features.
Do not waste time tuning contamination as if it changes ranking.

17. NEVER use the current `max(xgb_probability, 0.9 if anomaly else 0)` ensemble.
Instead either:
- keep IF as a novelty escalation signal,
or
- normalize/rank XGB and IF on VAL and test a tiny set of blend weights.
Only keep an ensemble if VALIDATION improves.

PRIORITY 0 — SPEED / RESPONSIVENESS

18. Cache expensive evaluation predictions and metrics in memory keyed by model version.
Do not recompute full TEST PR-AUC, PR curve, business metrics and per-class metrics on every API request.

19. Cache one SHAP TreeExplainer per model version.

20. Avoid full SHAP computation for every prediction if possible while preserving the `shap` response key and compatibility. Compute full SHAP for high-risk/explicit-explanation requests and use a cheap compatible result otherwise.

21. Do not block FastAPI's event loop with large loop retraining/prediction work. Offload long synchronous CPU/GPU operations appropriately while preserving the existing SSE event sequence and response contract.

22. Avoid loading TRAIN/VAL/TEST/X_TEST giant objects at startup unless required. Use a small manifest for counts and lazily load large data only for endpoints that need them.

23. Reuse model objects, feature matrices and cached predictions across loop cycles.

24. Vectorize the expensive per-user feature-engineering loops in engineering.py / transformers.py. Replace repeated prefix scans/masks with groupby rolling or NumPy searchsorted/two-pointer logic where possible.
This MUST preserve causality and numerical semantics. Before accepting it, compare a sample of old/new feature values.

25. Vectorize merchant-category prior-frequency and device-trust-age calculations where safe.

PRIORITY 1 — CLOSED LOOP / GENERATION QUALITY

26. /api/generate must not use TEST_DF as the source of demo attacks.
Use TRAIN-derived templates or the canonical rule generator.

27. Keep LLM generation/transcripts OFF.

28. Generated attack mutations must recompute all dependent engineered features.

29. Add simple synthetic-quality gates for impossible values, invalid categories, stale dependent features, duplicates and near-duplicates.

30. Add hard-negative mining from high-scoring legitimate VAL examples so recall improvements do not explode false positives.

31. Add lightweight diversity quotas across amount/channel/category/3DS/device/burst/timing/velocity where practical.

32. Add early stopping for feedback cycles when VAL PR-AUC stops improving or FPR degrades beyond tolerance.

PRIORITY 1 — REPRODUCIBILITY / SAFETY

33. Re-save XGB/IF/pipeline artifacts under the exact submission environment.

34. Add or extend the leakage guard so forbidden identifiers/labels cannot enter model matrices.

35. Add one backend smoke test that loads artifacts, runs Tier 1, Tier 2, health-equivalent prediction, and checks metric-manifest consistency.

36. Verify no frontend files were modified.

37. Verify all existing backend endpoint paths and frontend-facing keys remain intact.

VALIDATION RULES AFTER CHANGES

- Run leakage guard.
- Run a real validation comparison for every ML candidate.
- Keep TEST untouched during tuning.
- Only after the final candidate is frozen, run the final TEST evaluation once.
- Record before/after metrics.
- If a change reduces validation score, worsens the operating point materially, breaks an endpoint, or increases latency, revert/skip it.
- Prefer the simpler candidate when metrics are effectively tied.

IMPORTANT:
Do not claim a score improvement without actually measuring it.
Do not fabricate metrics.
Do not modify the frontend.
Do not spend time on LLM transcripts.
Do not perform broad speculative refactors.
Do not use TEST as a tuning oracle.

At the end, provide:
1. implemented fixes,
2. skipped fixes + feasibility reason,
3. before/after validation metrics,
4. final held-out test metrics,
5. API smoke-test results,
6. latency improvements,
7. exact model artifacts selected for submission.
```

---

# 26. Bottom line

The highest-return submission-day strategy is **not** to pile on new algorithms. It is to turn the existing architecture into a clean, fast, measurable adversarial defense system:

```text
clean feature contracts
        ↓
stronger XGB selected on VAL
        ↓
real IF novelty layer
        ↓
low-FPR operating point
        ↓
hard-example feedback
        ↓
more faithful synthetic attacks
        ↓
retrain
        ↓
held-out final test
```

The two biggest potential “game changer” speed wins are:

1. **vectorizing the expensive feature-engineering rolling loops**, and
2. **caching API evaluation/SHAP/model work instead of recomputing it per request**.

The two biggest potential score wins are:

1. **controlled XGBoost + `scale_pos_weight` selection on validation**, and
2. **turning the feedback loop into genuine hard-example training without TEST leakage**.

For Isolation Forest, the biggest win is first making it **correct and complementary**, then measuring whether it adds incremental signal. A weak IF should not be allowed to degrade a strong XGB just because the architecture contains two tiers.

---

# 27. [HIGH] Submission-Day One-Command Dependency Preflight in `start.cmd`

## Goal

Make the existing Windows `start.cmd` genuinely one-command for a fresh machine or a machine where part of the project's dependencies are missing.

A user should be able to double-click/run `start.cmd` and have it:

1. detect whether the project's required runtime dependencies are present,
2. report exactly what is missing or incompatible,
3. ask the user whether they want the missing dependencies installed,
4. install only after an explicit `Y`,
5. show visible progress using `*` characters while installation/checking is occurring,
6. re-check the environment after installation,
7. stop cleanly with actionable instructions when the user answers `N` or installation fails,
8. only launch the backend/frontend after the complete required environment passes preflight.

This is backend/repository usability infrastructure. Do NOT make any frontend source/UI changes.

## Why this matters

This is especially valuable for a hackathon submission because a judge, teammate, or evaluator should not have to reverse-engineer the environment before running the repository.

The current project has multiple dependency declarations and runtimes:

- `requirements.txt` for Python/pip dependencies used by the Python stack,
- `environment.yml` as an alternative Conda environment definition,
- `frontend/package.json` for the Vite/React-side Node dependencies,
- the existing `.venv` Python runtime expected by `start.cmd`,
- Node/npm required by the frontend launcher,
- Windows command-line utilities used directly by `start.cmd` such as `curl`, `netstat`, `taskkill`, and `ping`.

A simple `if exist .venv` check is therefore NOT comprehensive enough.

## [RECOMMENDATION]

Implement this before submission if it can be done without destabilizing the existing launcher. It has little effect on model score, but it dramatically reduces the probability of a failed first-run/demo environment and makes the repository substantially easier to evaluate.

## Required implementation behavior

### 27.1 Preflight must happen before killing ports

Run dependency checks before the current port cleanup section.

Do not kill existing user processes until the repository has confirmed that it can actually start.

This prevents a bad environment from unnecessarily destroying a currently running instance.

### 27.2 Resolve repository root robustly

Use:

`%~dp0`

as the source of truth and immediately normalize into a `ROOT` variable.

Every dependency/configuration path should resolve from `ROOT`, not from the caller's current working directory.

The command should work when launched by:

- double-clicking `start.cmd`,
- Command Prompt from another directory,
- PowerShell invoking the command,
- a terminal whose current directory is not the repository.

### 27.3 Detect Python itself

Check for a usable Python launcher/runtime, not merely a Python file existing somewhere.

Preferred order:

1. `%ROOT%\.venv\Scripts\python.exe`
2. `py -3`
3. `python`

The implementation should execute an actual version command such as:

`python --version`

and validate that a supported Python version is available.

Do not silently use an unrelated Python interpreter when `.venv` exists but is broken.

### 27.4 Detect broken/missing `.venv`

If `.venv\Scripts\python.exe` is missing, determine whether the repository can create it from an available Python runtime.

Ask before creating/installing:

`Python virtual environment is missing. Create .venv and install required Python dependencies? [Y/N]`

If `Y`:

- create `.venv`,
- upgrade/use its pip as appropriate,
- install the repository's declared Python requirements,
- re-run all checks.

If `N`:

- do not continue to a broken backend launch,
- print the exact manual commands needed,
- exit with a non-zero status.

### 27.5 Detect Python package dependencies comprehensively

Do not hard-code a short list such as `fastapi`, `uvicorn`, `numpy`, and `pandas`.

The preflight should use the repository's dependency declaration as the source of truth.

At minimum inspect:

`requirements.txt`

and install/verify every declared requirement in the selected Python environment.

Use pip's requirement-checking facilities where appropriate rather than maintaining a second manual package list.

Also verify project-critical imports actually used at runtime, especially packages whose import names differ from distribution names.

Examples of critical runtime imports in this project include the ML/data/API stack such as:

- numpy
- pandas
- scipy
- scikit-learn
- imbalanced-learn
- xgboost
- shap
- joblib
- fastapi
- uvicorn
- pydantic
- python-dotenv
- matplotlib where backend evaluation/import paths require it
- ctgan where the generation path requires it

Do not require optional/disabled LLM functionality merely because an old dependency remains in `requirements.txt` unless current backend imports actually require it. Dependency declarations should be reconciled with runtime imports where feasible, but the launcher must not spend time installing unused optional functionality unnecessarily.

### 27.6 Detect dependency version incompatibilities

Presence alone is insufficient.

Use pip's installed-package metadata / requirement resolution to detect cases where a package exists but fails the pinned requirement.

Examples:

- installed numpy version differs from the pinned requirement,
- xgboost is installed but the version does not satisfy the project requirement,
- scikit-learn is present but incompatible with the saved artifact/runtime,
- pydantic/fastapi dependency resolution is broken.

Do not blindly reinstall every package when one package is wrong.

Report a compact list such as:

`[MISSING] xgboost==...`

`[WRONG VERSION] pandas installed X, required Y`

`[OK] numpy`

### 27.7 Detect frontend Node/npm runtime dependencies

The existing launcher invokes `npm run dev`, so check at minimum:

- `node`
- `npm`
- a Node version compatible with the repository's frontend tooling

Then inspect `frontend\package.json` and, when present, `frontend\package-lock.json`.

Do not assume `npm` exists merely because the `frontend\node_modules` directory exists.

### 27.8 Detect missing/broken `node_modules`

The preflight should detect:

- missing `frontend\node_modules`,
- missing required package metadata,
- an invalid/incomplete install.

Prefer `npm ci` when a lockfile is present and valid because it creates a deterministic install.

Otherwise use `npm install`.

Before installing, ask:

`Frontend dependencies are missing/incomplete. Install them with npm? [Y/N]`

Although this is frontend dependency infrastructure, do not edit frontend source code or UI. The goal is simply to make the existing backend/frontend launcher reliably start.

### 27.9 Detect repository-level runtime tools used by `start.cmd`

Verify the Windows tools that the launcher directly relies upon:

- `curl`
- `netstat`
- `taskkill`
- `ping`

These are normally present on supported Windows installations and should NOT trigger package installation.

If one is missing, print a clear environment error and manual remediation instead of attempting to install an unrelated package.

### 27.10 Detect required project files before installation

Before installing anything, validate that expected project inputs exist:

- `requirements.txt`
- `frontend\package.json`
- backend entry point used by uvicorn
- required model/artifact paths/configs
- `.env` guidance if required for any enabled runtime path

Do not treat optional secrets or disabled integrations as mandatory merely because they appear in historical code.

### 27.11 Add an actual preflight script rather than making `start.cmd` enormous

Prefer one of these designs:

A. `start.cmd` → `scripts\preflight.cmd` → small Python checker

or

B. `start.cmd` → one dedicated Python preflight module

The checker should return clear exit codes:

- `0` = environment ready
- non-zero = environment not ready / user declined / installation failed

Keep `start.cmd` readable.

### 27.12 Use Python for comprehensive package inspection when practical

Do not try to parse all Python package metadata using fragile batch string manipulation.

A small repository-owned Python preflight helper can safely:

- parse `requirements.txt`,
- inspect installed distributions,
- use `importlib.metadata`,
- test important imports,
- validate versions,
- emit machine-readable or structured status,
- return appropriate exit codes.

`start.cmd` should mainly handle:

- human interaction,
- calling the checker,
- Y/N prompts,
- launching installers,
- final startup.

### 27.13 Installation consent must be explicit

Never silently install packages on the user's machine.

Use a clear prompt:

`Missing dependencies detected. Install them now? [Y/N]`

Accept case-insensitive forms such as:

`Y`, `y`, `N`, `n`

Optionally accept `yes`/`no` if the implementation remains reliable.

For invalid input, reprompt rather than guessing.

### 27.14 Show progress using `*`

The installation/check process should visibly communicate progress.

For example:

`Checking Python environment ....... ********`

`Checking Python packages .......... ******`

`Installing Python packages ....... ***************`

`Checking Node/npm ................ *****`

`Installing frontend packages ..... ************`

The exact animation may be simple. It does not need fancy terminal rendering.

The important requirements are:

- visible activity during long operations,
- no misleading claim that a package is installed before the command succeeds,
- final `SUCCESS` / `FAILED` state after each stage.

Do not implement an elaborate terminal animation that can hang because of buffering. A simple periodic `*` emitted by a helper process is preferable.

### 27.15 Do not hide installation failures

Do not redirect all installer output to `nul`.

Keep enough pip/npm output visible to diagnose failures.

A practical pattern is:

- show a short progress indicator,
- retain installer output,
- show the exact failing command if installation exits non-zero.

### 27.16 Re-run preflight after installation

After any installation attempt, do NOT assume success.

Run the complete dependency checker again.

Only continue to startup if the second pass returns success.

### 27.17 Handle network/unavailable-package failures

If pip/npm cannot reach a registry or a package cannot be installed:

- report the specific dependency,
- return to a clean stopped state,
- leave already installed dependencies intact,
- print a concise manual recovery command.

Do not continue to launch a partially installed application.

### 27.18 Prefer deterministic installs

For Python:

- install from `requirements.txt`,
- preserve pinned versions where they are intentional,
- avoid an unconstrained `pip install --upgrade` of the entire environment.

For Node:

- prefer `npm ci` when a lockfile exists,
- otherwise use `npm install`.

Do not silently upgrade model-stack dependencies during startup because that can invalidate saved artifacts or change model behavior.

### 27.19 Protect model/artifact compatibility

Dependency installation must not casually upgrade:

- xgboost,
- scikit-learn,
- numpy,
- pandas,
- scipy,
- shap,
- joblib

after the model artifacts have been created.

The preflight should install the versions declared by the repository rather than resolving to “latest”.

This is particularly important because serialized ML artifacts can be sensitive to library versions.

### 27.20 Check critical artifact/schema compatibility after dependencies pass

Before launching uvicorn, the preflight may perform a lightweight Python import/artifact smoke check, provided it stays fast.

At minimum verify that the backend can import its main modules and load the model/config metadata without a serialization/version exception.

Do not run the million-row evaluation dataset as part of startup.

### 27.21 Cache successful preflight where sensible

A lightweight marker or hash-based check may be used to avoid repeatedly performing expensive full verification when nothing changed.

The cache must invalidate when any of these change:

- `requirements.txt`
- `frontend\package.json`
- `frontend\package-lock.json`
- Python runtime path/version
- `.venv`
- node/npm version

Do not make the first-run checker dependent on a fragile cache.

### 27.22 Keep startup fast after the first run

A normal already-configured startup should remain very fast.

Do not run a complete pip dependency resolver every time if a cheap installed-package verification is sufficient.

Do not reinstall packages when the environment is already correct.

### 27.23 Output a final dependency summary

Before launch print something like:

`Environment: READY`

`Python: OK`

`Python packages: OK (N checked)`

`Node/npm: OK`

`Frontend packages: OK`

`Project files: OK`

`Model artifacts: OK`

Then proceed to the existing launcher behavior.

### 27.24 Preserve existing launcher behavior exactly

After preflight succeeds, retain the existing behavior:

- cleanup ports,
- start backend,
- start frontend,
- wait for `/api/health`,
- wait for port 5173,
- print demo URL/log locations,
- open the browser.

Do not alter endpoint paths or API responses.

### 27.25 Safe decline behavior

If the user answers `N` for a required dependency:

- do not launch the corresponding service,
- explain exactly what is missing,
- show the manual installation command,
- exit clearly.

Example:

`Backend cannot start because .venv is missing.`

`Manual fix:`

`py -3 -m venv .venv`

`.venv\Scripts\python.exe -m pip install -r requirements.txt`

Use the actual platform-correct path. Do not print malformed escaping.

### 27.26 Backend/frontend independence when practical

A missing frontend dependency should not cause Python dependencies to be reinstalled.

A missing Python package should not cause frontend packages to be reinstalled.

Track readiness separately:

`BACKEND_READY`

`FRONTEND_READY`

The existing full-stack launcher can still require both before claiming `Demo is live`.

### 27.27 Do not require Conda if the project already uses `.venv`

`environment.yml` exists, but the current launcher explicitly starts:

`.venv\Scripts\python.exe`

Do not make Conda a mandatory prerequisite unless the repository is deliberately migrated to Conda.

The simplest submission-day path should be:

Windows → Python → `.venv` → `requirements.txt`

plus:

Windows → Node/npm → `frontend` install.

`environment.yml` can remain an alternative environment definition/documentation path.

### 27.28 Optional: detect the Conda path without making it mandatory

If `conda` exists, the checker can report:

`Conda detected: optional`

but should not require it.

### 27.29 Optional secrets/API keys

Do not attempt to install or request API keys automatically.

Only mark a key as required if the currently enabled startup/runtime path genuinely cannot work without it.

Disabled LLM functionality must not make first-run setup fail.

### 27.30 Cross-check declared dependencies against actual runtime imports

For a genuinely comprehensive check, the agent should inspect the backend Python source for imported third-party modules and compare those imports against `requirements.txt` / the selected environment.

This is NOT a request to blindly install every import discovered anywhere in the repository. Classify imports into:

- required for normal backend startup,
- required only by optional/evaluation/training paths,
- disabled integrations,
- standard-library modules.

The checker should at minimum catch a case where a normal startup module imports a third-party package that is absent from `requirements.txt` or from the environment.

Do the same conceptual cross-check for `frontend` package imports against `package.json` when practical. `package-lock.json` remains the installation source for exact frontend versions.

The purpose is to catch dependency drift without turning the launcher into a slow static-analysis system.

### 27.31 Runtime import smoke test

After package checks pass, perform a lightweight import smoke test of the actual backend startup dependency graph.

For example, import the FastAPI application/module that `uvicorn` launches.

This catches situations where:

- a package is technically installed but unusable,
- binary dependencies cannot load,
- package versions are mutually incompatible,
- an import name differs from the distribution name,
- startup code references a package omitted from the requirements file.

Do not execute expensive model training, million-row evaluation, feedback loops, or full dataset feature engineering during preflight.

If the import fails, show the real exception summary and classify it as an environment/startup dependency failure rather than pretending all requirements are satisfied.

### 27.32 Native-runtime failure handling

Some ML/data wheels can fail to import because of an underlying native-runtime problem rather than a missing Python package.

When a critical import fails, distinguish:

`PACKAGE_MISSING`

`VERSION_MISMATCH`

`IMPORT_FAILURE`

`NATIVE_RUNTIME_FAILURE`

Do not attempt random package upgrades to fix native-runtime failures. Print the exact failing module and a targeted remediation hint.

### 27.33 Full project dependency inventory

The agent should build a temporary inventory during implementation containing:

- Python runtime version,
- every pinned Python distribution,
- normal-startup third-party imports,
- optional backend imports,
- Node/npm runtime versions,
- frontend package declarations,
- lockfile presence,
- required project/artifact files,
- launcher-required Windows commands.

This inventory does not necessarily need to ship as a large generated file. Its purpose is to ensure the final checker covers the real project rather than a hand-maintained subset.

### 27.34 Do not make optional training dependencies block normal demo startup

Some packages are useful for training, experimentation, notebook work, or optional generation flows but may not be required to run the submitted API.

The agent should classify these separately so a normal evaluator can start the application without unnecessary heavyweight installation where the architecture permits.

However, if the current submission's backend startup imports one of those packages unconditionally, it is a real startup dependency until the import path is changed safely.

Do not refactor imports merely to make the checker report fewer dependencies unless that refactor is independently safe and worthwhile.

### 27.35 Full-project dependency completeness acceptance test

The checker is considered comprehensive only when it can detect all of the following classes of problems:

1. Python interpreter missing or unsupported.
2. `.venv` missing or broken.
3. A declared Python package completely missing.
4. A declared Python package at the wrong pinned version.
5. A startup import missing despite the dependency file appearing complete.
6. A startup import failing because of a package incompatibility/native runtime issue.
7. Node missing.
8. npm missing.
9. Frontend dependencies missing.
10. Frontend lockfile/package installation incomplete.
11. Required project/artifact files missing.
12. Launcher-required Windows command unavailable.

The checker should NOT require unavailable optional LLM functionality when that path is intentionally disabled.

### 27.36 Final smoke launch after installation

After the dependency preflight succeeds:

- import the backend,
- optionally load lightweight model metadata,
- then start the existing backend/frontend exactly as before.

The smoke check must be cheap enough to avoid making normal startup feel slow.

## Feasibility gate for this item

Before implementation, the agent must check:

- Does the existing `start.cmd` have a stable location and root path?
- Is Python available on PATH or via `py` on the target Windows environment?
- Does `.venv` exist and work today?
- Is `requirements.txt` authoritative enough for pip installation?
- Does `frontend\package-lock.json` exist?
- Does current npm startup require only normal package installation?
- Can the project import/load its main backend without expensive dataset loading?

Implement only the portions that are reliable in the current repository.

Do not turn this into a broad installer framework.

## Acceptance tests

### Fresh machine simulation

From a Windows environment with:

- no `.venv`,
- no Python packages in the new venv,
- missing `node_modules`,

run `start.cmd`.

Expected:

1. detect missing dependencies,
2. ask for permission,
3. install after `Y`,
4. show visible `*` progress,
5. re-check successfully,
6. launch normally.

### Decline test

Answer `N`.

Expected:

- no silent installation,
- no broken service launch,
- clear manual instructions,
- non-zero exit status where startup cannot proceed.

### Already-installed test

Run `start.cmd` a second time.

Expected:

- no package reinstall,
- fast preflight,
- normal launcher behavior.

### Corrupted Python dependency test

Remove or alter one required Python package/version.

Expected:

- package is detected as missing/wrong,
- only the necessary installation path is offered,
- successful re-check afterward.

### Corrupted Node dependency test

Remove `frontend\node_modules`.

Expected:

- Node/npm still detected,
- frontend packages offered for installation,
- backend packages are not unnecessarily reinstalled.

### Version mismatch test

Install a deliberately incompatible version of one pinned package.

Expected:

- checker reports version mismatch,
- proposed install restores the declared version,
- model imports remain valid.

### Launcher regression test

After all dependencies are correct, verify:

- backend starts,
- `/api/health` returns successfully,
- frontend starts,
- existing logs still work,
- browser launch still works,
- `stop.cmd` workflow remains unchanged.

## Agent implementation prompt for this item

Before changing `start.cmd`, perform this feasibility check:

`FEASIBILITY CHECK`

`- Inspect start.cmd, requirements.txt, environment.yml, frontend/package.json, and package-lock.json if present.`

`- Determine the simplest reliable way to verify the complete runtime environment on Windows.`

`- Confirm whether a small Python preflight helper can be added without changing application behavior.`

`- Confirm that pinned package installation will not silently upgrade model-sensitive libraries.`

`- Confirm that missing Python and Node dependencies can be detected independently.`

`- Confirm the preflight can remain fast when everything is already installed.`

`DECISION: IMPLEMENT or SKIP`

`REASON: ...`

If feasible, implement a minimal, robust preflight architecture.

Do NOT edit frontend source files.

Do NOT change backend API contracts.

Do NOT alter model logic while implementing this launcher feature.

Do NOT add LLM transcript dependencies or reactivate disabled LLM behavior.

Do NOT silently install anything.

Do NOT automatically upgrade the ML stack to latest versions.

Do NOT make Conda mandatory when `.venv` is the current launcher environment.

The feature is successful only when a fresh evaluator can run `start.cmd`, receive a clear dependency diagnosis, choose `Y` or `N`, see `*` progress during installation, and reach the existing application without any functionality or numerical/API regression.

---

# Updated Submission-Day Priority Order

For the agent executing this document, the recommended implementation order is now:

`P0 correctness/leakage → P0 score optimization → P0 Isolation Forest correctness → P0 backend speed → P0 feedback-loop quality → P1 artifact/reproducibility → P1 one-command dependency preflight → P1 smoke/regression validation → lower-priority cleanup`

The dependency preflight is deliberately below score/correctness/performance fixes because those can directly affect the judged result, but it should still be completed if the implementation is low-risk and time remains before submission.
