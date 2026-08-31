# `fraud_model` — Deep Audit & Hackathon-Readiness Plan

Audited directly from the uploaded repository contents (all `src/**`, configs, docs). Every
finding below is anchored to a real file/line — nothing here is generic advice. Where I say
"verified," I mean I traced the actual code path, not the README's description of it.

**Context check:** per our prior conversation, your submission deadline is ~Aug 30, 2026 and
today is Aug 27 — so this plan is triaged for **~3 days left**, not a full rebuild. Section 8
gives you the literal order of operations.

---

## 0. TL;DR

The core, actually-used pipeline (`config.py` → `engineering.py` → `train.py` →
`evaluate.py`/`anomaly.py`/`explain.py`, plus the SMOTENC path) is methodologically solid —
temporal split, train-only fitting, honest reporting of a threshold-shift tradeoff, a real SHAP
additivity self-check. That part reflects good judgment and is worth keeping almost as-is.

But the repo has three serious, hidden problems that will hurt you at demo time or under judge
scrutiny:

1. **A real data-leakage bug** in the feature everyone will ask about first (`amount_zscore_30d`), introduced
   specifically because `engineering.py` runs on the *whole* dataset before the temporal split.
2. **A parallel "production" package (`src/fraud_model/`) that is completely non-functional** —
   corrupted file, missing classes, broken imports — despite two summary docs confidently
   describing it as finished. If you plan to demo a UI on top of this, it currently cannot run at all.
3. **`config.py` is decorative.** Its own docstring claims 8 files import from it; only 1 actually
   does. The other 7 hand-copy stale constant lists, and at least one of those stale copies is
   missing 5 features the real frozen model uses — which almost certainly makes
   `smotenc_train.py`'s baseline comparison crash on a feature-count mismatch.

None of this is visible from running `evaluate.py` and reading the printed metrics — which is
exactly why it's worth fixing before a judge (or a live demo) hits it.

---

## 1. What's actually in this repo right now

```
fraud_model/
├── .env                          # populated (Gemini key set) — gitignored, good. Rotate the key anyway (see 2.E).
├── README.txt                    # UNRESOLVED GIT MERGE CONFLICT — see 2.D-1
├── CHANGELOG.md                  # describes files that no longer exist — see 2.D-2
├── FULL_PIPELINE_IMPLEMENTATION_SUMMARY.md   # describes code that was never actually written this way — see 2.D-3
├── VALIDATION_IMPLEMENTATION_SUMMARY.md      # accurate, but describes 100%-dead code — see 2.F-4
├── append_config.py              # broken one-off script, syntax-invalid, hardcoded Windows path — DELETE
├── src/config.py                 # 212 lines, has a real duplicate-import bug, and 3 path constants
│                                  #   that don't match what the scripts actually write to disk
├── src/config.py.tmp             # leftover scratch file, stale PROJECT_ROOT logic — DELETE
├── src/features/engineering.py   # THE feature builder. Contains the leakage bug (2.A).
├── src/models/train.py           # only file that imports config.py. Correct temporal-split logic.
├── src/models/evaluate.py        # top-level script (no main()), hardcoded paths, duplicates config's
│                                  #   threshold-search constants instead of using them
├── src/models/anomaly.py         # well-reasoned Tier 2, but writes to filenames config.py doesn't know about
├── src/models/explain.py         # solid — SHAP with an additivity self-check. Least to fix here.
├── src/models/smotenc_augment.py # good design, BUT hardcodes a stale 14-feature list (config has 19)
├── src/models/smotenc_train.py   # same stale list — likely crashes re-scoring the frozen baseline (2.B-4)
├── src/models/ctgan_augment.py   # same stale-constants pattern; kept intentionally per README, that's fine
├── src/models/feedback_loop.py   # same stale-constants pattern
├── src/validation.py             # 479 lines, well-written, ZERO callers anywhere in the repo (2.F-4),
│                                  #   and its category whitelists don't match the actual generator output
├── src/generator/rule_generator.py   # 432 lines, runs as an unguarded top-level script (2.F-5)
├── src/generator/llm_generator.py    # 1326 lines, actually a solid diversity engine already (section 5)
├── src/fraud_model/inference.py      # SYNTACTICALLY BROKEN — see 2.B-1
├── src/fraud_model/pipeline/pipeline.py     # imports classes that don't exist — see 2.B-2
├── src/fraud_model/pipeline/transformers.py # missing classes referenced by pipeline.py — see 2.B-2
├── src/utils/                    # empty directory — DELETE or use it
├── notebooks/                    # empty directory
├── requirements.txt              # fine (double-checked httpx2/httpcore2 — those are the real
│                                  #   anthropic-SDK-1.0.0-era deps, not a typo)
└── environment.yml               # conda-forge lockfile w/ build hashes — not cross-platform, low priority
```

**Not present anywhere in the upload:** `data/raw/`, `data/processed/`, `models_artifacts/`,
anything under `notebooks/`. That means **the frozen baseline model, the raw transactions, and
the transcripts don't exist in the repo as given to me.** See 2.E — this is a hackathon-readiness
blocker, not just hygiene.

---

## 2. Critical findings, ranked by how much damage they can do

### 2.A — Data leakage (verified, concrete, fixable in <20 minutes)

**Where:** `src/features/engineering.py`, lines 128–134 (and the byte-identical logic duplicated
correctly-scoped in `src/fraud_model/pipeline/transformers.py::RollingFeatureExtractor.fit`,
ironically inside the *broken* package).

```python
mean_amt = np.mean(amount)          # <-- computed over the WHOLE df: train+val+test combined
std_amt = max(np.std(amount), 1e-9) # <-- same
...
df["amount_zscore_30d"] = np.where(count_30d > 0,
                                   (amount - sum_30d) / denom,
                                   (amount - mean_amt) / std_amt)   # fallback branch uses the global stat
```

`add_features(df)` is called **once, on the full raw CSV, before `train.py` ever splits by
time** (per the documented pipeline order: `engineering.py` runs first, `train.py` runs second).
So for every row where a user has no trailing-30-day history yet (`count_30d == 0` — this is
disproportionately **first-ever transactions**, which is exactly where several fraud types like
`account_takeover` and `bustout_identity` concentrate), the z-score fallback is computed against
a mean/std that includes every future val/test transaction. This directly violates the rule your
own README states: *"Medians, encoders, scalers: fit on TRAIN only; val/test only transform."*
The rolling/trailing parts of `engineering.py` (the per-user windowed loop) are genuinely fine —
they're causal by construction — it's specifically this one global fallback that's the problem.

**Why it matters for the hackathon:** this is the one leakage class a technical judge will
specifically probe for in a fraud project, because it's the classic mistake. Right now the
honest answer to "did you check for this?" would be "we have one instance of it."

**Fix (concrete):**
1. Split first, engineer features second — reverse the current pipeline order — OR
2. Keep the current order but compute `mean_amt`/`std_amt` only over rows that belong to the
   train split (you already compute the split cutpoints in `train.py`; pass them into
   `engineering.py`, or better, refactor so `add_features` takes a `fit_mask` for the fallback
   stats and nothing else).
3. Cleanest long-term fix: delete the duplicate/broken logic in `engineering.py` and
   `transformers.py`, and standardize on **one** `RollingFeatureExtractor`-style class with a
   proper `.fit(train_only)` / `.transform(any_split)` contract, used by both training and
   inference. This is already 90% written correctly in `transformers.py` — see 2.B-2 for why you
   can't use it as-is yet.
4. After the fix, re-run `train.py` and diff the frozen baseline's PR-AUC. If it moves
   meaningfully, that's your evidence the leak was real and material — document the before/after
   in `CHANGELOG.md` the same way you documented the SMOTENC-vs-CTGAN decision. Judges reward
   "we found and fixed a leak, here's the delta" far more than a number that's silently 0.3%
   inflated.

### 2.B — Code that will not run (verified by reading the actual bytes, not assuming)

**2.B-1. `src/fraud_model/inference.py` is not valid Python.**
- `predict_batch` (defined at line 112) has its body cut off after `self.initialize()` — the
  next line in the file (125) is `def get_business_metrics(...)`, a sibling method.
- The *actual* rest of `predict_batch`'s body (feature transform, tier-2 scoring, etc.) is
  orphaned at the **bottom of the file**, lines 264–284, sitting at 8-space indentation directly
  after an `if __name__ == "__main__":` block that's indented 4 spaces — this is a hard
  `IndentationError` the moment Python parses the file.
- The import `from fraud_model.pipeline.pipeline import FraudPipeline, create_inference_pipeline`
  is stranded at line 285, *after* the class and CLI code that use those names.
- There's a stray BOM character on the final line.
- **Net effect: `import fraud_model.inference` throws immediately.** Nothing downstream of this
  file works, including any UI you'd plug into it.

**2.B-2. `src/fraud_model/pipeline/pipeline.py` imports names that don't exist.**
```python
from .transformers import (
    DateTimeFeatureExtractor, AmountFeatureExtractor, CustomerAggregator,
    MerchantAggregator, CategoricalEncoder, FeatureSelector, NumericScaler,
    FeaturePipeline
)
```
`transformers.py` defines `DateTimeFeatureExtractor`, `RollingFeatureExtractor`,
`CategoricalEncoder`, `FeatureSelector`, `NumericScaler`, `FeaturePipeline` — **no**
`AmountFeatureExtractor`, `CustomerAggregator`, or `MerchantAggregator`. This import fails on its
own, independent of 2.B-1.

**2.B-3. This isn't a small oversight — it's undocumented divergence from the project's own
paper trail.** `FULL_PIPELINE_IMPLEMENTATION_SUMMARY.md` confidently describes "7
Sklearn-Compatible Transformers" and lists `AmountFeatureExtractor` / `CustomerAggregator` /
`MerchantAggregator` with specific behaviors ("Stores global_mean_, global_std_ with 1e-9
floor"... "Fits on sorted user+timestamp, stores user_stats_"). None of that code exists in the
file it claims to describe. Someone (or some AI-assisted session) wrote the summary for a design
that was then replaced by the actual `RollingFeatureExtractor` implementation, and the docs were
never reconciled. **Treat both implementation summary `.md` files as unreliable for anything
about `src/fraud_model/`.**

**2.B-4. `smotenc_train.py` almost certainly crashes comparing against the frozen baseline.**
`config.py`'s `FEATURE_COLS` has 19 entries (it includes the "v1.1" features:
`three_ds_failures_last_30d`, `device_trust_age_days`, `burst_count_10m`, `is_high_amount_burst`,
`inter_transaction_time_s`). The frozen `xgboost_tier1.json` was trained via `train.py`, which
uses that 19-feature config list. But `smotenc_train.py` (lines 25–28) hardcodes its **own**
14-feature `FEATURE_COLS` — missing exactly those 5 columns — and then uses it to rebuild
`X_val_baseline`/`X_test_baseline` (line 103) to re-score the *already-trained* baseline model.
Reloading an XGBoost model and calling `.predict_proba()` on a matrix with 5 fewer/different
columns than it was trained on will raise a feature-mismatch error in modern XGBoost — this
script's "head-to-head" comparison table is very likely never actually completing successfully
end-to-end. (I can't execute it here without the data, but the column-count/name mismatch is
unambiguous from the code alone.) The same stale 14-column list appears in `smotenc_augment.py`,
`feedback_loop.py`, and `ctgan_augment.py` — see 2.C for the root cause.

**2.B-5. `append_config.py` is not valid Python at all** — it's a one-off local script (visible
Windows path `C:/Users/HP/Desktop/fraud_model/...`) whose string literals lost their quote
characters somewhere along the way (`pathlib.Path( C:/Users/HP/...)` with no quotes). It's dead,
broken, and leaks a local filesystem path. Delete it — its one useful side effect (appending the
"Processed data files" / "Augmented data files" sections) already landed in `config.py` at some
point in the past, so nothing is lost by removing it.

### 2.C — `config.py` is not actually the single source of truth it claims to be

`config.py`'s own docstring says: *"This module consolidates all constants... to eliminate
duplication across `train.py`, `evaluate.py`, `explain.py`, `feedback_loop.py`,
`smotenc_augment.py`, `smotenc_train.py`, and `anomaly.py`."*

Verified by grep — actual imports of `config.py`:

| File | Imports config.py? |
|---|---|
| `train.py` | **Yes** |
| `validation.py` | Yes (unused module, see 2.F-4) |
| `evaluate.py` | No — hardcodes `"data/processed/X_val.pkl"` etc. |
| `explain.py` | No — hardcodes `"models_artifacts/xgboost_tier1.json"` |
| `anomaly.py` | No — hardcodes paths, and see filename mismatches below |
| `smotenc_augment.py` | No — hardcodes a **stale, shorter** `FEATURE_COLS` |
| `smotenc_train.py` | No — same stale list, likely-crashing consequence (2.B-4) |
| `feedback_loop.py` | No — same stale list |
| `ctgan_augment.py` | No — same stale list |
| `engineering.py` | No |
| `rule_generator.py` / `llm_generator.py` | No (their own constants are the source-of-record for generation, which is a defensible design choice — but they *also* silently diverge from `config.py`'s `CATEGORIES`/`N_USERS`/etc. that supposedly mirror them) |

This single fact explains almost every other bug in this document. Two concrete filename drifts
that fall out of it:

- `config.py` declares `ISO_FOREST_CONFIG_JSON = MODELS_ARTIFACTS / "isolation_forest_config.json"`,
  but `anomaly.py` actually writes to `"isolation_forest_tier2_config.json"` (line 69). Anything
  that later reads the config constant (e.g. `inference.py`'s `.with_name("isolation_forest_config.json")`)
  will silently find nothing and skip loading tier-2 thresholds.
- `config.py` declares `ISO_FOREST_THRESHOLDS_CSV = "isolation_forest_thresholds.csv"`, but
  `anomaly.py` writes `THRESHOLD_TABLE_PATH = "isolation_forest_threshold_table.csv"` (line 70).

**Fix:** this is the highest-leverage single change you can make. Make every script under
`src/models/` and `src/features/` import its constants from `config.py` — no exceptions, no
locally re-declared `FEATURE_COLS`. Where a script currently writes to a path that differs from
`config.py`'s constant, pick the constant as ground truth and fix the script (or vice versa,
just pick one and delete the other). Budget ~1–2 hours; it eliminates an entire class of "silent
drift" bugs at once and is exactly the kind of refactor a judge who opens your repo will notice
favorably (it shows engineering discipline, not just a working notebook).

### 2.D — Documentation that actively misdescribes the code

**2.D-1. `README.txt` has an unresolved git merge conflict** — literally contains `<<<<<<< HEAD`
(line 1), `=======` (line 80), and `>>>>>>> 03cc991b...` (line 126) with two entirely different
documents stacked on top of each other (a proper README above the marker, a raw experiment log
below it). This is the very first file a judge opens. Fix immediately — see 3 for what to keep
from each half.

**2.D-2. `CHANGELOG.md` references files that don't exist in this codebase:**
`impersonation_diagnostics.py` (README's run order also lists this — line 17 of README), `ctgan_train.py`,
`validation.StrategyDecision`, `InsufficientDataError`. Confirmed via `__pycache__`: compiled
`.pyc` files for `ctgan_train.cpython-314.pyc` and `impersonation_diagnostics.cpython-314.pyc`
**do exist**, meaning these files were real and ran at some point, then were deleted from the
source tree without updating the docs that reference them. Either restore them from git history
(`git log --all --full-history -- '*impersonation_diagnostics*'`) or scrub every reference to
them from README/CHANGELOG so the documented pipeline order actually matches what's runnable.

**2.D-3. `FULL_PIPELINE_IMPLEMENTATION_SUMMARY.md`** describes `src/fraud_model/` as a finished,
production-ready package. It is not (2.B-1 through 2.B-3). Either rewrite this doc after you fix
the package, or delete it now and regenerate an accurate one once `src/fraud_model/` actually
runs. Do not leave it as-is — a judge who reads this doc and then imports the module will find a
`SyntaxError` inside a minute of looking, which is a worse impression than not documenting it at all.

### 2.E — Reproducibility gap (this one is about the hackathon, not the code)

No `data/raw/`, `data/processed/`, or `models_artifacts/` directory exists anywhere in what you
gave me. `.gitignore` only excludes `models_artifacts/*.joblib` and `data/processed/` — it does
**not** exclude `data/raw/` or the frozen `.json` model — so if those aren't in your repo either,
it's not a `.gitignore` side-effect, they were simply never committed.

Practically, this means: **a judge who clones your repo can run nothing.** `train.py` fails at
`pd.read_pickle(TRANSACTIONS_FEATURES_PKL)` before it does anything else, because that file only
exists after running `engineering.py`, which only exists after running `rule_generator.py`,
which requires a populated `.env` with a working LLM key (and API spend/time) to produce the
`ai_impersonation` transcripts at all.

**Fix, in priority order for the next 3 days:**
1. Commit the generated `data/raw/transactions.csv` and `data/raw/transcripts.jsonl` (these are
   the *output* of an expensive generation step — commit the artifact, not just the recipe).
   At ~213K rows this is a few tens of MB at most — fine for git.
   Amend `.gitignore` to stop excluding `data/processed/` too, or at minimum commit
   `transactions_features.pkl` and the three split pickles so `evaluate.py`/`anomaly.py` are
   runnable without re-running feature engineering.
2. Commit `models_artifacts/xgboost_tier1.json` (this is your frozen baseline — it's small, a
   few hundred KB, and it's the one artifact your whole README calls "FROZEN" and treats as
   ground truth. It should be the most protected file in the repo, not the most likely to be
   missing).
3. Also rotate the `GEMINI_API_KEY` currently sitting in your `.env`. It's correctly gitignored
   (good instinct), but it was shared with me in this session and has plausibly been shared with
   teammates via other channels too (Slack, zip files, etc.) — cheap insurance to rotate it once,
   regardless of what did or didn't leak.
4. Add a `Makefile` or single `scripts/reproduce.sh` that runs the whole pipeline in order (the
   README's "Pipeline order" section, minus the LLM regeneration step) so "does it run" is a
   one-command answer for both your team and the judges.

### 2.F — Dead code inventory (safe to delete outright)

| File / thing | Why it's dead | Action |
|---|---|---|
| `append_config.py` | Broken syntax, one-off, already applied. See 2.B-5. | Delete |
| `src/config.py.tmp` | Stale scratch copy of config.py with a *different* (wrong) `PROJECT_ROOT` calc (`parent.parent.parent` vs the real file's `parent.parent`) — a landmine if anyone ever imports it by accident. | Delete |
| `src/utils/` | Empty directory, no files. | Delete, or actually put the "should be shared" helpers here per section 4 |
| `notebooks/` | Empty directory. | Delete, or start using it for the EDA you'll want for the demo deck |
| `src/validation.py` | 479 lines, zero callers anywhere in the repo (grepped for every public function name — no hits outside the file itself). Also its `VALID_MERCHANT_CATEGORIES` (`grocery, restaurant, retail, online, travel, entertainment, utilities, healthcare, education, other`) barely overlaps with the categories the generator actually produces (`config.CATEGORIES` / `rule_generator.CATEGORIES`: `grocery, restaurant, fuel, ecommerce, utility, travel, electronics, pharmacy, entertainment, clothing`) — only 3 of 10 words match. If you wire this in as-is it will immediately fire false-positive warnings on legitimate data. | Either (a) delete it, or (b) fix the category/channel/3DS-result whitelists to match the real generator output and actually call it from `train.py`/`engineering.py` as a pre-flight check — it's genuinely well-built machinery, it's just unplugged and slightly out of sync |
| Duplicate `from pathlib import Path` | `config.py` lines 9 and 14 — harmless but sloppy | One-line fix |
| Duplicate `scale_pos_weight` computation | `train.py` lines 51 and 77 compute the identical expression twice | Compute once, reuse |
| `rule_generator.py` has no `if __name__ == "__main__":` guard | The entire generation pipeline (including real LLM API calls) runs as a side effect of `import rule_generator`. Makes the module untestable/unimportable-for-reuse without triggering full (paid) generation. | Wrap the script body in `main()` / guard it |

---

## 3. What to actually do with `README.txt` right now

Keep the top half (the clean, well-written README above the conflict marker) as
`README.md`. From the bottom half (the raw baseline experiment log), extract the numbers into a
`RESULTS.md` or a table inside `CHANGELOG.md` — those numbers (Test PR-AUC 0.9072, frozen
threshold 0.96, per-fraud-type breakdown) are valuable and shouldn't be thrown away, they just
don't belong interleaved with a git conflict marker in the project's front door. Delete
`README.txt`, add `README.md`. Takes 10 minutes, immediately fixes the worst first impression in
the repo.

---

## 4. Restructure proposal

Given 3 days left, don't do a full package reorganization — the value/risk ratio is bad this
close to deadline. Do this instead, which is contained and directly fixes 2.B and 2.C:

```
src/
├── config.py                 # fix duplicate import; keep as-is otherwise
├── features/
│   └── engineering.py        # fix leakage (2.A); import FEATURE_COLS etc. from config
├── generator/
│   ├── rule_generator.py     # add main() guard
│   └── llm_generator.py      # unchanged — this one's in good shape (section 5)
├── models/
│   ├── train.py              # already correct
│   ├── evaluate.py           # switch hardcoded paths -> config constants
│   ├── anomaly.py            # fix ISO_FOREST_* filename drift; switch to config constants
│   ├── explain.py            # switch hardcoded paths -> config constants (low priority, works today)
│   ├── smotenc_augment.py    # DELETE local FEATURE_COLS/CAT_COLS/MODEL_COLS, import from config
│   ├── smotenc_train.py      # same — this fixes the likely crash in 2.B-4
│   ├── ctgan_augment.py      # same
│   └── feedback_loop.py      # same
├── serving/                  # NEW — replaces the broken src/fraud_model/ package
│   ├── __init__.py
│   ├── feature_pipeline.py   # ONE correct implementation of the rolling-feature transformer,
│   │                         #   ported from transformers.py's RollingFeatureExtractor (it's
│   │                         #   already close to correct — fit() properly scopes global stats
│   │                         #   to whatever's passed in, which is the fix for 2.A if wired
│   │                         #   through train-only data)
│   ├── inference_service.py  # a from-scratch, syntactically-valid rewrite of inference.py's
│   │                         #   actual intent: load frozen XGBoost json + iso-forest joblib,
│   │                         #   expose predict_one(dict) and predict_batch(df)
│   └── api.py                # FastAPI wrapper (section 6)
└── validation.py             # fix category whitelists to match config.CATEGORIES, or delete
```

Delete `src/fraud_model/` entirely rather than trying to salvage the corrupted files — you'd
spend more time forensically reconstructing `inference.py`'s intended logic than writing 80
clean lines against the now-fixed `config.py`. Salvage `transformers.py`'s
`RollingFeatureExtractor` logic (the fit/transform split is the right idea) into the new
`serving/feature_pipeline.py`.

---

## 5. Making the generated transcripts more diverse

Good news: `llm_generator.py` already has real diversity infrastructure, and it's more mature
than the docs let on — worth knowing what's already there before adding more:

- **10 target personas** (`TARGET_PERSONAS`, lines 433–443) covering trust profiles from
  "trusts authority" to "pushes back hard," sampled per-case with `random.choice`.
- **14 social-engineering pretexts** (`PRETEXTS`, lines 413–428) and **14 separate benign
  pretexts** (`BENIGN_PRETEXTS`, lines 1080–1095) for negative/control examples.
- **6 weighted outcome states** (`OUTCOME_STATES`/`OUTCOME_WEIGHTS`, lines 458–470) —
  refused / deferred / engaged-no-action / credential-shared / payment-attempted /
  payment-completed — assigned *before* generation so the model dramatizes a fixed outcome
  instead of "deciding" one mid-generation (this was a real, documented fix for a prior failure
  mode where contradictory instructions caused the local model to reasoning-loop past its token
  budget — good engineering, keep it).

What's actually thin, and where I'd spend the diversity budget you have left:

1. **Persona × pretext × outcome are sampled independently and uniformly.** There's no
   correlation structure — an "eager to comply fast, anxious" persona and a "pushes back hard,
   skeptical" persona currently have the *same* probability of landing on `payment_completed`.
   In reality that correlation is exactly the signal a detector should learn to be robust
   against. Add a small weighting table (persona → outcome-weight multiplier) so susceptible
   personas skew toward compliance outcomes and skeptical personas skew toward refusal/deferral —
   this makes the synthetic data more realistic *and* gives you a second, richer fraud-analysis
   claim for the "Identify" pillar write-up ("we modeled persona-outcome correlation, not just
   independent sampling").
2. **Channel/medium is implicit.** All 14 `PRETEXTS` read as phone-call social engineering
   ("bank security team callback," "family emergency payment request"). Consider adding a
   `CHANNEL` dimension (SMS/smishing, email/phishing-then-call, voice-clone callback, chat-app
   impersonation) since payment fraud red-teaming rubrics generally reward attack-surface
   breadth, not just conversational variety within one surface.
3. **Randomness isn't seeded.** `random.choice(TARGET_PERSONAS)` / `random.choices(OUTCOME_STATES, ...)`
   (lines 852, 931) use the unseeded global `random` module, while everything else in this
   project is disciplined about `SEED = 42` reproducibility (`rng = np.random.default_rng(SEED)`
   in `rule_generator.py`, `SMOTENC_SEED`, `FEEDBACK_SEED`, etc. in `config.py`). Pass a seeded
   `random.Random(SEED)` instance through instead — cheap fix, makes your generated dataset
   exactly reproducible for judges who want to re-run it, and is consistent with the
   reproducibility discipline you've already shown everywhere else.
4. **Length/style variance exists for benign transcripts** ("Vary wording and tone... some
   customers are brief, some chatty, some slightly annoyed") but the fraud-case system prompt
   doesn't have an equivalent explicit instruction as far as the visible prompt text goes for
   `PRETEXTS`-driven cases — worth double-checking `BATCH_SYSTEM`'s prompt (search for it near
   line ~450–520) has the same "vary length/register" instruction the benign one does, so fraud
   transcripts don't all converge on one register just because personas vary but style
   instructions don't.

---

## 6. UI plan (you said this needs a UI eventually)

Given 3 days, keep this minimal and demo-focused — don't build a SPA.

**Backend:** `src/serving/api.py`, FastAPI, 3 endpoints:
- `POST /predict` — single transaction JSON in, `{fraud_probability, decision, tier, top_shap_features}` out.
  This is where the *fixed* `serving/inference_service.py` gets used — load the frozen
  `xgboost_tier1.json` + `isolation_forest_tier2.joblib` once at startup, not per-request.
- `GET /health` — model-loaded check, useful for judges poking at a live demo without needing a
  full transaction payload.
- `POST /batch` — CSV upload → CSV of scored predictions, for a "run this on our test set live"
  demo moment.

**Frontend:** a single static HTML+JS page (no build step — you don't have time for a
React toolchain right now) that:
- Has a form for the 22 model columns (or a "load a sample transaction" button that pulls a few
  canned examples per fraud type from `test_df.pkl`, since typing 22 fields live is a bad demo).
- Shows the fraud probability as a gauge/bar, the tier-1 vs tier-2 verdict, and — this is your
  differentiator — **renders the top-5 SHAP feature contributions for that specific prediction**,
  since you already generate this in `explain.py`. A live, per-transaction "here's *why* the
  model flagged this" panel is exactly what a "Defend" pillar judge wants to see, and you already
  have 90% of the machinery (`shap.TreeExplainer`, the additivity check) — it just needs to run
  on one row instead of a batch and get serialized to JSON.

This is achievable in the time you have specifically *because* fixing `src/fraud_model/`
properly (2.B) is a prerequisite you need to do anyway — the UI plan and the bug-fix plan share
almost all their work.

---

## 7. Robustness roadmap (post-hackathon, or stretch if day 3 goes well)

- **Tests.** Zero test files exist anywhere in the repo. At minimum, before the demo, write one
  smoke test that: builds a tiny synthetic DataFrame, runs it through the (fixed) feature
  pipeline, and asserts no NaNs/infs reach the model input — this single test would have caught
  2.A immediately if it asserted "train-only stats" as a property rather than trusting the code.
- **CI.** Even a single GitHub Action that runs `python -c "import src.models.train"` etc. for
  every file would have caught 2.B-1/2.B-2 (a straight `SyntaxError`/`ImportError`) before it sat
  in the repo for however many days it's been broken.
- **Schema contract test.** Assert `config.FEATURE_COLS` is imported (not re-declared) in every
  file under `src/models/` — literally `grep -L "from config import" src/models/*.py` should
  return an intentionally-short list (right now it returns almost everything).
- **Threshold/artifact provenance.** Store the frozen threshold (0.96) and the model's training
  data hash/row-count inside the saved model's metadata (XGBoost supports custom attributes) so
  "which version of the data trained this frozen artifact" is answerable from the artifact alone,
  not from tribal memory.
- **Case-level (not just row-level) train/val/test isolation.** Worth a quick audit: confirm no
  `case_id` (a single simulated attack campaign, which can span multiple transactions/timestamps)
  ever has some of its rows in train and others in val/test purely because its timestamps happen
  to straddle the split cutpoint. `evaluate.py` already reports "case-level recall" as a metric —
  good instinct — but that's different from confirming case-level *split* isolation. If a
  multi-transaction attack case is ever split across train and test, the model gets to see part
  of the same attack pattern during training, which is a leakage vector even with a
  correctly-timestamped split. Quick check: `train_df.case_id.isin(test_df.case_id).any()` should
  be `False`.

---

## 8. What to do, in order, for the next 3 days

**Today (Day 1 — fix what's silently wrong):**
1. Resolve the `README.txt` merge conflict → `README.md` (10 min, section 3).
2. Fix the `amount_zscore_30d` leakage in `engineering.py` (2.A) and re-run
   `engineering.py` → `train.py` → `evaluate.py`. Record the before/after PR-AUC delta in
   `CHANGELOG.md`.
3. Delete `append_config.py`, `src/config.py.tmp` (2.F).
4. Make every script under `src/models/` and `src/features/` import from `config.py` instead of
   redeclaring `FEATURE_COLS`/`CAT_COLS`/`MODEL_COLS` (2.C). This alone fixes the likely
   `smotenc_train.py` crash (2.B-4) and the `anomaly.py` filename drift.
5. Commit `data/raw/transactions.csv`, `data/raw/transcripts.jsonl`,
   `models_artifacts/xgboost_tier1.json`, and the processed pickles (2.E). Rotate the Gemini key.

**Day 2 (build the serving layer + UI):**
6. Delete `src/fraud_model/`. Write `src/serving/feature_pipeline.py` (port the correct
   `RollingFeatureExtractor` logic, now leakage-free because it's fit on train-only data),
   `src/serving/inference_service.py` (clean rewrite, ~80–120 lines, no corruption), and
   `src/serving/api.py` (FastAPI, 3 endpoints per section 6).
7. Build the single-page frontend with the SHAP-explanation panel.
8. Smoke-test the whole thing end-to-end: raw CSV in → API prediction out, on a machine that
   only has the committed artifacts (no regeneration, no `.env` needed) — this is your
   reproducibility proof for judges.

**Day 3 (polish + diversity + demo):**
9. Add the persona→outcome correlation weighting and the channel dimension to
   `llm_generator.py` (section 5, items 1–2) — regenerate a modest batch (don't regenerate the
   whole 213K-row dataset this late; a few hundred new `ai_impersonation`/attack-scenario rows
   for demo variety is enough, especially if you don't have time to re-freeze the baseline).
10. Fix or delete `validation.py`'s category drift (2.F) — cheap, and "we validate our data
    contracts" is a good line in a judge Q&A.
11. Final pass: delete `src/utils/` and `notebooks/` if still empty, delete
    `FULL_PIPELINE_IMPLEMENTATION_SUMMARY.md` or rewrite it to match reality, rewrite
    `CHANGELOG.md`'s references to files that no longer exist (2.D-2).
12. Dry-run the whole demo on a clean clone of the repo (not your local machine with cached
    pickles) — this is the single highest-value 30 minutes you can spend before submission,
    because it's the only step that catches "works on my machine."

---

## 9. Quick sanity checks you can run to confirm each fix

- Leakage fix: `train_df["amount_zscore_30d"]`'s distribution stats should not change at all if
  you delete val+test rows from the input to `engineering.py` and only feed it train rows for
  the fallback stat — if they do change, the fallback is still leaking.
- Config drift fix: `grep -L "from config import" src/models/*.py src/features/*.py` should
  return an empty or near-empty list.
- `src/fraud_model` replacement: `python -c "from src.serving.inference_service import *"` should
  exit 0.
- Reproducibility: `git clone` into a scratch directory, run only the committed artifacts through
  `evaluate.py` (no regeneration), confirm it reproduces the numbers in `CHANGELOG.md`.
- Case-isolation: `assert not train_df.case_id.isin(val_df.case_id).any()` and same for
  `train_df`/`test_df` and `val_df`/`test_df`.  





  Fully fixed and verified (compiled clean):

src/config.py — removed the duplicate from pathlib import Path.
src/features/engineering.py — fixed the core data-leakage bug (2.A). add_features() now takes a fit_mask param; the amount_zscore_30d global fallback stat is computed only over train-only rows (auto-derived via config.TRAIN_QUANTILE when no mask is passed, so it's safe even run standalone). Also wired in validation.validate_raw_data() as a non-fatal pre-flight check in __main__.
src/models/train.py — deduped the repeated scale_pos_weight computation.
src/models/evaluate.py — now imports all paths/thresholds from config.py instead of hardcoding them.
src/models/explain.py — same config-import fix for all hardcoded model/data/output paths.
src/models/anomaly.py — now imports ISO_FOREST_CONFIG_JSON / ISO_FOREST_THRESHOLDS_CSV etc. from config.py, which eliminates the filename-drift bug (2.C) by construction.
src/models/smotenc_augment.py — replaced the stale, 14-column hardcoded FEATURE_COLS/CAT_COLS/BINARY_FLAG_COLS with imports from config.py (the fix for the likely smotenc_train.py crash, 2.B-4), and switched to config's path constants.

Still outstanding (not yet touched in this pass):

smotenc_train.py, feedback_loop.py, ctgan_augment.py — need the same stale-constants → config-import fix.
src/validation.py — category/channel/three_ds_result whitelists still need correcting to match the real generator output (I confirmed the actual values: channels are card_present/ecom, not online/pos/atm/mobile; three_ds results are passed_first_try/failed_then_passed/not_attempted).
src/generator/rule_generator.py — needs the if __name__ == "__main__": guard (I traced through the whole file and confirmed nothing else imports it, so this is safe to do, just not yet done).
src/fraud_model/ — still broken as-is; not yet deleted/replaced with the proposed src/serving/ package (feature_pipeline.py, inference_service.py, api.py).
append_config.py, src/config.py.tmp — not yet deleted.
README.txt merge conflict — not yet split into README.md + results extraction.
CHANGELOG.md / FULL_PIPELINE_IMPLEMENTATION_SUMMARY.md — not yet rewritten to remove stale references.






Completed this session (compiled clean, sanity-tested where possible):

smotenc_train.py — replaced the stale 14-column hardcoded FEATURE_COLS/CAT_COLS/MODEL_COLS/SEED with imports from config.py, and swapped every hardcoded path (data/processed/*.pkl, models_artifacts/*.json) for the corresponding config constant. This directly fixes the 2.B-4 feature-count-mismatch crash.
feedback_loop.py — same fix: stale constants and hardcoded paths replaced with config imports (FEATURE_COLS, CAT_COLS, MODEL_COLS, STEERABLE_COLS, FEEDBACK_ROWS_PER_TYPE, FEEDBACK_MAX_CYCLES, FEEDBACK_SEED, all path constants).
ctgan_augment.py — same fix, plus corrected DISCRETE_COLS to use config.BINARY_FLAG_COLS (now correctly includes is_high_amount_burst, which the old hardcoded list predated). Added two missing constants to config.py (TRAIN_DF_CTGAN_PKL, SYNTHETIC_MINORITY_ROWS_CTGAN_PKL) since config didn't have them yet, and updated smotenc_train.py to use the new constant too instead of building the path inline.
Verified the fix: grep -L "from config import" src/models/*.py src/features/*.py now returns empty — every model/feature script imports from the single source of truth, closing 2.C.
src/validation.py — fixed the category/channel/3DS whitelists. Traced the real generator output in rule_generator.py and confirmed: merchant_category uses config.CATEGORIES (now imported directly instead of a hand-copied list), channel is card_present/ecom, three_ds_result is passed_first_try/failed_then_passed/not_attempted. Ran a sanity check with realistic rows through validate_raw_data() — zero false positives on category/channel/3DS now (previously would have flagged every row).

Still outstanding (not reached yet):

rule_generator.py's missing __main__ guard — I was in the middle of checking this. It's a bigger lift than a one-liner: the entire 432-line file is top-level script code (only two small helper functions exist), so wrapping it in main() means indenting the whole body and checking for scoping issues. I confirmed nothing else imports from rule_generator.py (only comment references in llm_generator.py and validation.py), so it's safe to do, just not yet done.
src/fraud_model/ deletion + src/serving/ replacement package (feature_pipeline.py, inference_service.py, api.py)
Deleting append_config.py, src/config.py.tmp
README.txt merge-conflict split into README.md + results extraction
CHANGELOG.md / FULL_PIPELINE_IMPLEMENTATION_SUMMARY.md rewrites