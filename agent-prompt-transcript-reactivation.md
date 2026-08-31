# Task Brief: Transcript Pipeline Reactivation (for coding agent)

> This is not a numbered phase in either the backend's RECOVERY_LOG.md rounds
> or the frontend's Phase 0–12 sequence — it's a separate, cross-cutting task
> that touches both repos. Do not label your work "Phase 12" (that name is
> already taken by `afl_phase12_signature_motion_and_polish.md` in the
> frontend repo). Log backend work as a new dated round in `RECOVERY_LOG.md`
> and frontend work as a new dated entry in `PROGRESS.md`, matching the
> existing format in each file.

## 0. What this task is

Two constants in `src/generator/rule_generator.py` currently disable LLM
transcript generation entirely:

```python
LLM_IMPERSONATION_TARGET = 0  # LLM DISABLED - pure rule-based generation   (line ~526)
BENIGN_TARGET = 0             # LLM DISABLED - pure rule-based generation   (line ~662)
```

The generator and validator behind them (`src/generator/llm_generator.py`)
are already fully built: batched local-model calls via LM Studio,
JSON-schema-constrained output, a semantic validator
(`validate_fraud_case` / `validate_benign_case`) that checks the generated
dialogue actually demonstrates its assigned label, and an LLM-judge fallback
for phrasing the keyword lists miss. Every rejected case is logged to
`transcripts.jsonl` with a specific `rejection_reason` — nothing is silently
dropped or fabricated.

The task is: (1) re-enable generation, (2) diagnose real yield using the
existing rejection-reason logging (not guesswork), (3) build the
transcript classifier that `RECOVERY_LOG.md` already proposed and that a
comment in `rule_generator.py` already names but that does not exist yet
(`src/models/transcript_classifier.py`), (4) integrate its output as a new
feature for `ai_impersonation` specifically, and (5) surface real generated
transcripts in the frontend using the **existing** Generate-page transcript
display, not a new one.

## 1. Standing rules — apply to every checkpoint below

- **Work in checkpoints. Stop and report after each one.** Do not chain
  checkpoints together and present a finished result — I want to see the
  output of each step before you proceed to the next, the same way this
  project's own `RECOVERY_LOG.md` documents one round at a time with
  evidence, not a single end-to-end summary.
- **Before any call that actually invokes the local model** (pilot or full
  batch — see Checkpoint 2), stop and explicitly ask me to start LM Studio
  and confirm the `qwen3.5-4b` model (or whatever `LOCAL_MODEL` is currently
  set to in `.env`) is loaded and serving at `LOCAL_BASE_URL`. Do not assume
  it's already running. Wait for my confirmation before sending the first
  real generation request.
- **Do not modify, refactor, or "clean up" any existing working code path
  without asking me first**, even if you believe the change is small or
  obviously correct. This specifically includes:
  - Anything under `src/generator/rule_generator.py` outside the two
    `LLM_IMPERSONATION_TARGET` / `BENIGN_TARGET` constants and the
    generation-loop code that already exists to call them.
  - `src/generator/llm_generator.py`'s validator logic (`validate_fraud_case`,
    `validate_benign_case`, the keyword marker lists, `JUDGE_SYSTEM`,
    `BATCH_SYSTEM`) — if you think a validator or prompt change is needed to
    fix a real yield problem, propose the specific change and your reasoning
    and wait for my go-ahead. Do not loosen a check just to raise the
    acceptance number.
  - Anything for the other six fraud types (`account_takeover`, `auth_bypass`,
    `bustout_identity`, `card_testing`, `synthetic_identity`, `bnpl_abuse`) —
    their generator code, `FRAUD_TYPE_TARGETS`, `AVG_TX_PER_CASE`, or trained
    artifacts in `models_artifacts/`.
  - Any frontend file outside `src/features/generate/` and
    `src/lib/api/demo-client.ts` / `types.ts` (see Checkpoint 5).
  - `.env` — I already know it has a live key checked in; that's a
    revoke-and-rotate action on my end, not something for you to touch.
- **No fabricated results anywhere.** If generation yield is low, if the
  classifier's metrics are weak, or if a retrain regresses another fraud
  type, report the real number and stop — do not tune parameters until a
  number looks good without telling me what you changed and why, and do not
  present a partial run as complete.
- After every checkpoint, run whatever the project's own verification
  standard already calls for before you report done: `leakage_guard --strict`
  after any retrain, `npx tsc --noEmit` + relevant Playwright specs after any
  frontend change. Report the actual command output, not "should pass."

---

## Checkpoint 1 — Recon (read-only, no edits)

Read, in this order, and summarize back to me in 5–10 lines total (not a
restatement of each file):

1. `RECOVERY_LOG.md` — specifically the `ai_impersonation` root-cause
   analysis and the two proposed features (`impersonation_urgency`,
   `transcript_risk_score`).
2. `src/generator/llm_generator.py` — the `BATCH_SYSTEM` / `BENIGN_BATCH_SYSTEM`
   prompts, `validate_fraud_case`, `validate_benign_case`, `OUTCOME_STATES` /
   `OUTCOME_WEIGHTS`, and `generate_llm_case_batch` / `generate_benign_case_batch`.
3. `src/generator/rule_generator.py` — the block from `# ---- 5. AI-Assisted
   Impersonation` through `# ---- 6. Benign transcripts`, including the
   `IMPERSONATION_MIN_TOTAL` rule-based fallback that tops up short LLM yield.
4. `.env` — confirm `USE_LOCAL`, `LOCAL_BASE_URL`, `LOCAL_MODEL`,
   `LOCAL_MAX_TOKENS`, `LOCAL_TEMPERATURE` current values.
5. Confirm whether `data/transcripts.jsonl` (or wherever `TRANSCRIPT_PATH`
   points in `config.py`) already has old data in it from a prior run — if
   so, tell me its size/row count before touching it. Don't delete or
   truncate it without asking.

Do not proceed past this checkpoint until I confirm your summary matches
what I expect.

---

## Checkpoint 2 — Pilot generation (small, before committing to volume)

**Stop here and ask me to start LM Studio and confirm the model is loaded
before sending any request.**

Once I confirm:

1. Temporarily set `LLM_IMPERSONATION_TARGET = 10` and `BENIGN_TARGET = 10`
   (pilot size only — not the final 200/200) as the only edit to
   `rule_generator.py` for this checkpoint.
2. Run the generation path (however it's normally invoked — check for an
   existing entry point/script that calls `rule_generator.py`'s generation
   block; if none exists as a standalone runnable script, tell me before
   improvising one).
3. Report exact numbers: `n_accepted` / `n_rejected` for both fraud and
   benign, and **the full breakdown of `rejection_reason` values** from
   `transcripts.jsonl` for anything rejected — this is the actual diagnostic
   data the project already logs, use it instead of guessing.
4. If yield is very low (say, under ~40%), tell me what the dominant
   rejection reason actually is (e.g., judge-fallback failures because the
   judge call itself is failing, vs. genuine label/content mismatches, vs.
   benign contamination markers) and propose a specific, minimal fix with
   your reasoning. Do not apply the fix yourself — wait for my sign-off,
   since this touches the validator/prompt rules covered under the standing
   rules above.

Stop here and wait for my go-ahead before scaling up.

---

## Checkpoint 3 — Full-volume generation

Once I approve the pilot results (and any fix from Checkpoint 2, if one was
needed and approved):

1. Set `LLM_IMPERSONATION_TARGET = 200` and `BENIGN_TARGET = 200`.
2. **Note for me, don't just silently proceed**: these are *input* targets
   (cases attempted), not guaranteed accepted output — a prior run in this
   project's own history saw yield as low as ~36%. Tell me your realistic
   expected accepted count based on the Checkpoint 2 pilot rate before
   running the full batch, so I'm not surprised by the final number.
3. Run the full batch. This will take a while on a local 4B model — give me
   a rough time estimate first based on the pilot's per-case latency.
4. Report final accepted/rejected counts for both classes, same
   rejection-reason breakdown as Checkpoint 2, and confirm
   `transcripts.jsonl` now has the new records appended (not overwritten).

Stop here and report before touching the classifier.

---

## Checkpoint 4 — Build the transcript classifier (new file, isolated)

Only after I confirm the Checkpoint 3 volume/quality is acceptable:

1. Create `src/models/transcript_classifier.py` (this path is already
   referenced by a comment in `rule_generator.py` but the file doesn't exist
   yet — you're building it fresh, not resurrecting something).
2. Approach: TF-IDF vectorization of the transcript text
   (`transcripts.jsonl`'s `transcript` field, both fraud and benign rows,
   `label` field as the target: 1 for fraud, 0 for benign) + a simple linear
   classifier (logistic regression). Keep it lightweight — this is a same-day
   deliverable, not a transformer fine-tune.
3. Output: a `transcript_risk_score` in `[0, 1]` per `case_id` — this must
   match the field name and shape `RECOVERY_LOG.md` already proposed, so it
   plugs into the join described in Checkpoint 5 without a schema mismatch.
4. Only train/evaluate on the **accepted** records (`"accepted": true`) —
   rejected records are logged for diagnostics, not for training.
5. Do a simple train/test split and report real metrics (accuracy, and
   ideally precision/recall/F1 or ROC-AUC given this is binary) — do not
   report training accuracy as if it were held-out performance.
6. **Do not touch any existing training file yet.** This checkpoint is the
   classifier in isolation only.

Stop here and show me the metrics before integrating anything into the main
pipeline.

---

## Checkpoint 5 — Integrate into the tabular pipeline

This is the highest-risk step — it touches files that currently produce
working results for 6/7 fraud types. Ask me to explicitly confirm before you
start, even though I'm pre-approving the overall plan here — the specific
diff needs a second look before it runs.

1. Add `transcript_risk_score` as a new column, joined by `case_id`, at the
   same point `case_id` already exists on the fraud dataframe in
   `src/models/train.py` (it's already used there for the case-aware
   temporal split — join alongside that, don't invent a new merge point).
   For `case_id`s with no transcript (every non-`ai_impersonation` row, and
   any rejected/missing case), the join must produce an explicit,
   documented default (e.g. a neutral score or a flag column indicating
   "no transcript available") — never a silent `NaN`-fill, per this
   project's own existing discipline against exactly that failure mode.
2. Add the new column to `FEATURE_COLS` in `config.py`.
3. Retrain (`python -m src.models.train` or however the project's actual
   entry point works — confirm from Checkpoint 1 recon).
4. Run `python -m src.models.leakage_guard --strict` — must exit 0.
5. Report a **full before/after PR-AUC table for all 7 fraud types**, not
   just `ai_impersonation` — matching the exact table format already used in
   `RECOVERY_LOG.md`'s "Final summary table." If any of the other six
   regress, stop and flag it — do not ship a change that trades one fraud
   type's score for another's without me seeing that trade explicitly.
6. Append a new dated round to `RECOVERY_LOG.md` in the same format as the
   existing rounds (files changed, root cause, before/after numbers, leakage
   guard result).

Stop here and wait for my confirmation the numbers are acceptable before
touching the frontend.

---

## Checkpoint 6 — Frontend: show real transcripts, using what already exists

Read before writing any code:

- `src/features/generate/conversation-log.tsx` — the existing component that
  renders a role-keyed transcript (currently `fraudster` / `judge` roles,
  styled with `LOOP_LEGS` accent colors and left-border turn cards). This is
  the pattern to reuse, not replace.
- `src/lib/api/types.ts`'s `GenerateResult` interface (`conversation: {
  role: string; content: string }[]`, `accepted`, `rejection_reason`,
  `drop_stats`).
- `src/lib/api/demo-client.ts`'s `demoConversation()` / `demoTransactionFor()`
  — this is how the Generate page currently gets its data, since the real
  API (`src/api/main.py`) is still a Phase-0 stub with only `/api/health`
  implemented. **Default to extending the demo-mode fixture path, not
  building new FastAPI endpoints** — that's a much bigger, separate task and
  isn't what today's checkpoint is for. Only build a real endpoint if I
  explicitly tell you to after seeing this checkpoint's proposal.

Before writing code:

1. Propose, in plain language, exactly how you'll adapt real generated
   transcripts (attacker/target speaker roles, from `transcripts.jsonl`) into
   the existing `conversation: {role, content}[]` shape `ConversationLog`
   already renders. The real schema's roles (`attacker`/`target`) don't match
   the demo's current roles (`fraudster`/`judge`) — decide and tell me
   whether you're remapping labels, extending the component's role→style
   lookup, or something else. **Do not silently redesign the component or
   introduce new visual styling** — same borders, same `LOOP_LEGS` token
   colors, same icon pattern, matching every other page in this design
   system.
2. Wait for my sign-off on the approach before implementing.

Once approved:

3. Implement by extending `demo-client.ts`'s fixture data with a small set of
   real accepted transcripts from `transcripts.jsonl` (a handful, not all
   200+ — this is for demo/showcase purposes, not a live data feed).
4. Run `npx tsc --noEmit` and the existing `generate.spec.ts` Playwright spec
   — report actual pass/fail, not an assumption.
5. Append a dated entry to the frontend's `PROGRESS.md` in the existing
   format (files changed, what changed, test results).

---

## What "done" looks like

- `transcripts.jsonl` has ~200 attempted fraud + ~200 attempted benign
  generation attempts logged, with real accept/reject outcomes and reasons.
- `src/models/transcript_classifier.py` exists, trained only on accepted
  records, with honestly-reported held-out metrics.
- `transcript_risk_score` is joined into the tabular pipeline by `case_id`
  with an explicit no-transcript default, `FEATURE_COLS` updated, and a
  full 7-type before/after PR-AUC table showing no unreported regressions.
- `leakage_guard --strict` exits 0.
- The Generate page shows a small number of real LLM-generated transcripts
  through the existing `ConversationLog` component, with no new visual
  patterns introduced.
- `RECOVERY_LOG.md` and `PROGRESS.md` each have a new dated entry in their
  existing format.
- At every checkpoint above, you stopped and I confirmed before you moved on.
