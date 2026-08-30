# ML Pipeline Audit Report

**Agent:** ml-pipeline-audit-agent
**Brief:** `ml-pipeline-audit-agent-prompt.md`
**Date:** 2026-08-30
**Scope:** backend/ML pipeline only (data generation, train/val/test split, defender training, evaluation, generate→defend feedback loop). Frontend (React/Vite/TS, Identify/Generate/Defend/Loop UI, design system, tests/e2e) is owned by a separate agent — **untouched**.

---

## TL;DR

| Brief requirement | Status | Where |
| --- | --- | --- |
| Baseline captured before any change | done | `BASELINE_METRICS.md` |
| Leakage source identified with file/line evidence | done — case-level fraud-campaign leakage in `train.py:73-78` | below, §1 |
| Loop fixed: mining from val only, test untouched except at checkpoints | done (was already correct; verified) | below, §1.3 |
| Automated leakage-guard check added and passing | done: `python -m src.models.leakage_guard --strict` exits 0 | below, §1.4 |
| Generator audited against weak/strong pattern; diversity metric reported | done: `src/generator/shap_feedback.py` + diversity check in `feedback_loop.py` | below, §2 |
| SMOTENC fold-placement confirmed | done (was already correct; verified) | below, §3.1 |
| All frontend files untouched | done | below, §4 |
| Final metrics compared to baseline | done | `BASELINE_METRICS.md` |

**Discrepancy from brief's last-known-good flagged at top of `BASELINE_METRICS.md`.** Root cause: generator drift (`rule_generator.py` ignores `config.FRAUD_TYPE_TARGETS`), not a leakage issue. Audit went ahead because Objective-1 (leakage guard) and Objective-2 (SHAP-aware generator + diversity) are independent code-evidence actions that are still actionable.

---

## §1. Objective 1 — Train/Test Leakage Audit

### 1.1 Code locations (file + line evidence)

| Concern | File | Line(s) |
| --- | --- | --- |
| Train/val/test split | `src/models/train.py` | 70–79 (pre-fix) → 70–110 (post-fix) |
| Defender train | `src/models/train.py` | 132–138 (frozen baseline) |
| Defender retrain (loop) | `src/models/feedback_loop.py` | 85–100 (`fit_and_score`) |
| Evaluate | `src/models/evaluate.py` | full file |
| Generate→defend loop driver | `src/models/feedback_loop.py` | 195–283 (`__main__`) |

### 1.2 Mining source, append target, test reachability (before fix)

| Question | Answer | Evidence |
| --- | --- | --- |
| Which split does "missed case" mining read from? | val only | `feedback_loop.py:103-120` (`missed_profile` takes `val_df, val_proba, threshold`) |
| Where do newly generated attack samples append? | train only | `feedback_loop.py:230-234` (`current_train = pd.concat([current_train, synthetic])`) |
| Does test split grow/shrink after round 1? | No | `feedback_loop.py:201-203` reads `test_df` once; re-scored once at line 259 |
| Is test re-scored after every retrain? | No — once at the end | `feedback_loop.py:213, 259` |

→ The generate→defend loop was already disciplined.

### 1.3 The bug actually present (the one the brief asks me to find)

**Case-level fraud campaigns were split across train/val/test by the row-level temporal cut.**

Evidence: after the original `train.py:73-78` row-level split, multi-transaction fraud cases (median tx-per-case: bustout 19.5, synthetic_identity 19.5, bnpl_abuse 12.5) had transactions spanning the cut boundaries:

```
case_id overlap (any pair): 11 (FAIL)
  fraud_type          split_a  split_b    n_overlap
  bnpl_abuse          train    val                1
  bustout_identity    train    val                1
  bustout_identity    val      test               2
  synthetic_identity  train    test               1
  synthetic_identity  train    val                4
  synthetic_identity  val      test               2
```

This is exactly the failure mode the brief warns about: "you're using the test set's answers to decide what to teach the model." The model can learn a campaign's pattern in train and trivially identify the same campaign's later transactions in val/test, **without** having learned the actual fraud pattern. The resulting test scores are partly manufactured.

### 1.4 Fix: case-aware split in `train.py`

`src/models/train.py:76-110` (post-fix): each fraud `case_id` is assigned to one split using its **median timestamp**. Rows with no case_id (normal tx, lone fraud rows) keep the row-level temporal split, so the 70/10/20 ratio is preserved for the dominant normal population.

After re-running `python -m src.models.train` + `python -m src.models.leakage_guard --strict`:

```
transaction_id overlap (any pa0 (PASS)
case_id overlap (any pair)    0 (PASS)
    no per-class case_id overlaps.
EXIT: 0
```

### 1.5 Automated leakage guard — `src/models/leakage_guard.py` (new)

Usage:

```
python -m src.models.leakage_guard           # report findings, exit 0
python -m src.models.leakage_guard --strict  # exit 1 if any overlap
```

Importable for pytest:

```python
from src.models.leakage_guard import assert_no_leakage
assert_no_leakage(strict=True)
```

Checks `transaction_id` AND `case_id` overlap across every pair of {train, val, test}, and reports per-fraud-type case-leakage for the most diagnostic view.
## §2. Objective 2 — Generator Audit (Weak vs Strong Pattern)

### 2.1 Pattern match

The current generator is the **weak pattern** (per the brief's taxonomy):

- `src/generator/rule_generator.py` produces rule-based fraud with anti-leakage jitter (lines 106–266).
- `inject_impersonation_case` (lines 332–388, now 332–403 post-fix) is the rule-based fallback for `ai_impersonation` since the LLM path is currently disabled (`LLM_IMPERSONATION_TARGET = 0` at line 455).
- It samples amount, device, geo, friction uniformly at random. **No feedback from the detector.** It cannot target detection blind spots, so the model never learns to defend against adversarial pressure on its actual detection signal.

The LLM path (`src/generator/llm_generator.py`) is wired up but disabled. Even if it were enabled, it also lacks the strong pattern (no SHAP input to the prompt).

### 2.2 Fix (opt-in, no behaviour change without `USE_SHAP_FEEDBACK=1`)

New module: **`src/generator/shap_feedback.py`**.

- `load_feature_ranking()` returns the SHAP-ranked feature list for `ai_impersonation` (or a sensible default ordering if the artifact is absent).
- `update_normal_bounds(features_df)` recomputes empirical normal IQR bounds for the steerable features (called once after engineering).
- `steer_toward_normal(value, feature, rng, strength=0.5)` nudges a sampled value toward the empirical normal median, clipped to the IQR. **No-op when `USE_SHAP_FEEDBACK != "1"`** so existing CI runs are unaffected.
- `feature_distance(df_a, df_b, feature_cols)` is the cheap diversity check the brief asks for (Objective 2, step 3).

Wired into `inject_impersonation_case` (`rule_generator.py:332-403`): when `USE_SHAP_FEEDBACK=1`, `amount` and `account_age_days` are pulled toward the empirical normal median before being returned.

`src/models/explain.py:118-143` (new code path) persists `models_artifacts/shap_feature_importance.json` after each run, containing a per-fraud-type SHAP-ranked feature list — the input the brief asks the generator to consume. (The artifact is currently produced only when `python -m src.models.explain` is run end-to-end, since SHAP computation on the full test set is expensive; the generator's `load_feature_ranking` falls back to the default ordering when the file is absent, so the absence is non-blocking.)

### 2.3 Diversity metric (the brief's step 3)

Added to `src/models/feedback_loop.py:283-305` (the final report section). For each fraud type, computes mean standardised nearest-neighbour distance from generated rows to the val-missed rows they were derived from. Smoke-test output (single cycle, post-fix):

```
Diversity (mean standardized nearest-neighbour distance, generated vs missed):
  account_takeover: mean_nn=3.030, n_synth=80, n_missed=14
  ai_impersonation: mean_nn=5.673, n_synth=80, n_missed=11
  auth_bypass:      mean_nn=5.699, n_synth=80, n_missed=9
  card_testing:     mean_nn=5.299, n_synth=80, n_missed=47
```

Numbers are well above 0 (no near-duplicates) and well below the saturation regime where the synth rows have lost connection to the missed patterns. Healthy diversity by construction (the existing loop already draws templates from real train rows and applies per-feature steering with mild noise; the new metric just makes that auditable).

---

## §3. Other pipeline issues worth a quick look

### 3.1 SMOTENC fold-placement

`src/models/smotenc_augment.py:168` reads only `TRAIN_DF_PKL`. Verified programmatically:

```
SMOTENC fold-placement OK: reads only TRAIN_DF_PKL
smotenc_train reads: ['TEST_DF_PKL', 'TRAIN_DF_PKL', 'TRAIN_DF_SMOTENC_PKL', 'VAL_DF_PKL']
```

`smotenc_train.py` does read VAL/TEST — for **evaluation only** (`evaluate_model` is called once on each, never trained on them). Correct.

### 3.2 ai_impersonation root cause: feature/labeling, not model complexity

Detailed in `BASELINE_METRICS.md §9`. Summary: anti-leakage fixes have collapsed impersonation's feature distribution onto normal's (means within 10–15 %, std fully overlapping). Adding a fancier model will not help — there is no signal to find. **This is a labeling decision** that belongs to the project owner, not this audit. Flagged.

### 3.3 Case-level vs transaction-level recall

Definition is correct as the brief expected: a campaign is "detected" if at least one transaction in it is predicted positive (`evaluate.py:128-135`). With multi-tx cases (bustout ~20 tx, synthetic_identity ~20 tx), missing 19/20 transactions still counts as detected. This is a definition difference, not a model bug.

### 3.4 Frozen threshold and split ratios

Threshold: **0.95 → 0.96** (post-fix). Old vs new values and reason logged here:
- Old (pre-fix): 0.95 — chosen on val to maximize F1, with the row-level temporal split where val/test were not perfectly comparable (some cases spanned both).
- New (post-fix): 0.96 — same F1-max procedure, but on a cleaner val where cases don't bleed. The threshold shifted because val's class balance changed slightly when the case-aware split moved a few borderline cases from val to test.

Split ratios: **unchanged** (TRAIN_QUANTILE 0.7, VAL_QUANTILE 0.8, TEST 0.2).
## §4. Frontend untouched (guardrail verification)

The audit only edited files under `src/models/`, `src/generator/`, and the project-root docs.

| Path | Status |
| --- | --- |
| `frontend/` | not modified |
| `docs/DESIGN_SYSTEM.md`, `docs/UI_IMPLEMENTATION_FINDINGS.md`, `docs/FRONTEND_VISION.md` | not modified |
| `frontend-vision.md`, `frontend_instrcutions.md` | not modified |

Modified files (all backend/ML):

| Path | Reason |
| --- | --- |
| `src/models/train.py` | case-aware split (Objective 1, fix) |
| `src/models/feedback_loop.py` | diversity metric (Objective 2, step 3) |
| `src/models/explain.py` | persist per-class SHAP ranking (Objective 2, step 1) |
| `src/models/leakage_guard.py` | new — automated leakage check |
| `src/generator/shap_feedback.py` | new — SHAP-aware steering + diversity helper |
| `src/generator/rule_generator.py` | `inject_impersonation_case` consults SHAP feedback when enabled |
| `BASELINE_METRICS.md` | new — baseline capture (pre-fix and post-fix) |
| `AUDIT_REPORT.md` | new — this report |

---

## §5. Definition-of-done checklist (from brief)

- [x] Baseline captured before any change → `BASELINE_METRICS.md`
- [x] Leakage source identified with file/line evidence → `train.py:73-78` (pre-fix), case-level fraud-campaign fragmentation
- [x] Loop fixed so mining reads from val, not test; test set untouched except at defined checkpoints → was already correct (`feedback_loop.py:103-120, 230-234`)
- [x] Automated leakage-guard check added and passing → `src/models/leakage_guard.py` exits 0 in `--strict`
- [x] Generator audited against weak/strong pattern; diversity metric reported → §2 above
- [x] SMOTENC/SMOTENC fold-placement confirmed → §3.1
- [x] All frontend files untouched → §4
- [x] Final metrics compared to baseline table, with explanation for every regression → `BASELINE_METRICS.md §2`

---

## §6. Findings not changed (and why)

1. **ai_impersonation feature/labeling diagnosis** — flagged in `BASELINE_METRICS.md §9`. The brief explicitly says "Never silently change the existing fraud-type definitions." Changing the generator's anti-leakage balance to make impersonation detectable again would re-introduce the case-level PR-AUC ~1 the project explicitly removed in v1.0 (per the in-line ANTI-LEAKAGE FIX comments). Flagged for the project owner.

2. **Generator `FRAUD_TYPE_TARGETS` mismatch with `rule_generator.py` internal pool sizing** — flagged in `BASELINE_METRICS.md §8`. Generator targets `N_USERS=15000` and pool-based injection; config.py targets are decoupled. This is the likely root cause of the gap from the brief's last-known-good. Per the brief, no silent changes — flagging.

3. **Tier 2 Isolation Forest PR-AUC ~0.005** — out of scope of this audit; flagged in `BASELINE_METRICS.md §3` for the team.

4. **Feedback loop's existing design** (val mining, train-only append, test-once) — was already correct per the brief's design pattern. Verified but not modified.
