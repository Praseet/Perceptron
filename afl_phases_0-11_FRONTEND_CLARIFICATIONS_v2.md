# Adversarial Fraud Lab (AFL) — Phases 0–11 (Complete Build Bible)

> Combined in strict serial phase order from the phase prompts supplied in this conversation. This is now a **self-contained** document: the "Build Bible Reference" section immediately below reconstructs every shared section and appendix the phase prompts point to as "above" (`Appendix A` through `G`, the Multi-Model Handoff Protocol, the API client interface, the Judging Criteria Alignment Matrix, and so on) — sourced from the actual project files in the uploaded repo (`docs/ATTACK_TAXONOMY.md`, `src/config.py`, `src/fraud_model/inference.py`, `CHANGELOG.md`, and the never-fully-flushed-to-disk `docs/UI_IMPLEMENTATION_FINDINGS.md`, recovered in full from `docs/write_part1.ps1`–`write_part8.ps1`), not invented. Anywhere the source material was genuinely silent, that gap is completed transparently and flagged as such rather than presented as pre-existing lock — see Appendix D's note on the 5-tier risk spectrum for the one place this happens.
>
> Phases 10–11 complete the 12-phase plan named in Phase 0 (§4c: "12-phase plan") and Phase 0's `.env.example` note ("flips to `false` only in Phase 11, on demo day itself"). **There is no Phase 12** — see "Phase Sequencing" below. Phases 10–11 are written in the same voice and against the same conventions as Phases 0–9 — same `PROGRESS.md` protocol, same "verify against the running app, not your own summary" standard — and assume Phases 0–9 are DONE per `frontend/PROGRESS.md`.
>
> Both phases are deliberately exhaustive rather than quick. Whatever AI coding agent runs them (Cline or otherwise) should expect each to occupy several hours of continuous, self-verifying work — not a single pass — and should use every tool actually available to it (a real browser via Playwright or an MCP browser/screenshot tool, a terminal for Lighthouse/bundle-analysis CLIs, grep/AST search across `src/`) rather than reasoning about correctness from memory. Where a step says "verify," that means drive the running app and read the actual output, the same standard every earlier phase already holds itself to.

---

---

# Build Bible Reference — Shared Sections and Appendices

> This section is the material every phase prompt above (and below) points to as "above." It was reconstructed for this combined document from the actual project files in the repo — `docs/ATTACK_TAXONOMY.md`, `src/config.py`, `src/fraud_model/inference.py`, `CHANGELOG.md`, `docs/FRONTEND_VISION.md`, and the (never-fully-flushed-to-disk) `docs/UI_IMPLEMENTATION_FINDINGS.md`, whose actual intended content is recovered in full from `docs/write_part1.ps1` through `write_part8.ps1` — rather than re-derived from a general sense of what a fraud-detection dashboard "should" contain. Every number, field name, and endpoint shape below traces to one of those files; anywhere the source material was genuinely silent, that gap is called out explicitly as a completion made now, not presented as if it were always locked. Treat this section as a peer of Phases 0–11 above and below it — the phase prompts assume it exists verbatim.

## 0. Judging Criteria Alignment Matrix

Every screen in the prototype exists to answer one of the five scoring axes from the Mastercard brief. Any screen that doesn't map to a row below doesn't earn its place (per FRONTEND_VISION §1.1).

| Scoring axis | Primary page | Secondary evidence |
|---|---|---|
| **Diversity** | Identify (25-attack taxonomy browser, 5 categories) | Home's "Attacks generated: 1,390" tile (sum of `FRAUD_TYPE_TARGETS`, Appendix F) |
| **Fidelity** | Generate (paired narrative ↔ transaction, honest drop-rate readout) | Identify's "wired to a generator?" badge on the 4 implemented profiles |
| **Detection efficacy** | Defend (live predictor, per-class PR-AUC table, PR curve, business thresholds) | Home's "PR-AUC: 0.9072" tile |
| **Novelty** | Loop (closed-loop retraining with live before/after deltas) | Home's 4-node loop diagram; Identify's `NOVEL` badge on AI-004/AI-005 |
| **Real-world feasibility** | Loop (measured, repeatable recall/FN improvement) | Defend's business-threshold table (precision/recall tradeoff a real ops team would set) |

## 0.1 Submission Checklist

Three deliverables, per the brief and FRONTEND_VISION §1.1 / §5:

- [ ] **Code repo** — frozen at the Phase 11 tag, `README.md` opening with the homepage screenshot, `frontend/PROGRESS.md` complete for all 12 phases (0–11), no `TODO(Phase` markers anywhere in `src/`.
- [ ] **Solution walkthrough (docx)** — structured per `docs/SOLUTION_OUTLINE.md`'s 8 sections (Executive Summary, Identify, Generate, Defend, Closed-Loop, Real-World Feasibility, Novel Contributions, Appendices), 15–20 pages, compact and pointing to the prototype rather than re-explaining it (FRONTEND_VISION §0 decision 5).
- [ ] **Web prototype** — runnable locally via `npm run dev` (frontend) + `uvicorn src.api.main:app` (backend), demo-safe by default (`VITE_DEMO_MODE=true` in the committed `.env.example`), all five pages reachable from the global nav.

## 0.2 Phase Sequencing

This is a **12-phase plan: Phase 0 through Phase 11.** There is no Phase 12. Phases 0–5 build the shared foundation (scaffold, tokens, primitives, patterns, lib, chrome/home); Phases 6–9 build the four feature pages, in judge-attention priority order (Defend, Generate, Identify, Loop), so that if the 3-day clock runs out, the cut order is Loop → Generate → Identify, per FRONTEND_VISION §8 — the homepage, Defend, and the loop animation are the only non-negotiables. Phases 10–11 hold everything to that standard, prove it against live data, and freeze it. A phase's prompt referencing "Phase N is DONE" means Phase N's own acceptance-criteria checklist is fully checked in `frontend/PROGRESS.md`, not merely that code exists.

> **Post-Phase-9 addendum (see H.69):** an additive Phase 9.5 ("Motion & Visual De-Genericization Pass") was inserted between Phase 9 and Phase 10 after Phase 9 was reported nearing completion, in response to an explicit request to bring the finished pages closer to the visual register of Stripe/Darktrace/Wiz/Datadog rather than a generic AI-dashboard template. This makes the plan 13 phases in practice (0–9, 9.5, 10–11). The "12-phase plan" language above is left untouched as the historical record of the original sequencing decision, not a claim that the addendum doesn't exist — see H.69 for why it was added this way instead of renumbering.

## 1. The Multi-Model Handoff Protocol

`frontend/PROGRESS.md` is the only channel between AI coding sessions — no session has memory of a prior one. Every phase, without exception, reads it in full before starting and appends to it (never rewrites a prior entry) before finishing. Header, created once by Phase 0:

```markdown
# AFL Frontend — Progress Log

Append-only. Do not edit or delete a prior entry — if something in an
earlier entry turns out to be wrong, add a new entry noting the
correction and why. Each entry is written by whichever model/session
completed that phase.

---
```

Each phase's entry follows this exact shape:

```markdown
## Phase <N> — <Phase Name> — <ISO date> — <model/session identifier>

**What exists now:** <literal list of files created/modified this phase>

**Deviations / assumptions:** <anywhere this phase's prompt was silent
and a call had to be made — what was decided and why. "None" if
genuinely none — don't manufacture one to fill the section.>

**Acceptance criteria verified:** <which checklist items were personally
verified against the running app, and how — not "all of them," the
specific method for each>

**Known issues / left for next phase:** <anything incomplete, deferred,
or flagged for later — "None" if genuinely none>
```

## 2. Demo Mode and the Fixture Data Layer

`VITE_DEMO_MODE` (Phase 0's `.env.example`) is the single switch that decides whether `lib/api/client.ts` (Phase 4) calls the real `http://localhost:8000/api/*` backend or returns canned data from `lib/demo-data/` (also Phase 4). It defaults to `true` for the entire build (Phases 0–10) and flips to `false` only locally, only in Phase 11, only in a gitignored `.env` — the committed `.env.example` never changes, so a fresh clone (including a judge's) always gets the safe, always-works, fixture-backed experience without needing a live model loaded. Every fixture in `lib/demo-data/` is shaped identically to its corresponding live API response (Appendix C) — this is what makes the switch safe: no component should ever need to know or care which mode it's in. The one asymmetry: every real backend endpoint (per Appendix C) *also* independently accepts a per-request `?demo=true` query param and returns the same canned data server-side — a second, backend-owned safety net for the specific case where the model or a generator fails to load live, so a live demo degrades to fixture-quality data automatically rather than erroring.

## 3. The API client interface — the seam that makes "flexible" real

`lib/api/client.ts` (Phase 4) exports one function, `getApiClient()`, returning an object whose shape never changes regardless of `VITE_DEMO_MODE`:

```ts
interface ApiClient {
  getHealth(): Promise<HealthResponse>;
  getAttacks(): Promise<Attack[]>;
  getAttack(id: string): Promise<Attack>;
  generate(req: GenerateRequest): Promise<GenerateResult>;
  predict(req: PredictRequest): Promise<PredictResult>;
  getEvalPerClass(): Promise<EvalPerClassRow[]>;
  getEvalPrCurve(): Promise<PrCurveResponse>;
  getLoopHistory(): Promise<LoopHistoryEntry[]>;
  // runLoop does not return a Promise — it opens a stream and hands back
  // an unsubscribe function directly, synchronously
  runLoop(req: LoopRunRequest, onEvent: (e: LoopEvent) => void): () => void;
  getSystemStatus(): Promise<SystemStatus>;
}
```

Every feature's `use-*.ts` hook (Phases 6–9) calls `getApiClient()` and never imports `fetch`, `EventSource`, or a demo-data file directly — that indirection is the entire point: swapping `VITE_DEMO_MODE` swaps the implementation behind this interface without touching a single component. `runLoop`'s streaming half is backed by `lib/use-event-stream.ts` (Phase 4), which wraps a real `EventSource` in live mode and a `setInterval`-driven fake emitter in demo mode, exposing the same `(event) => void` callback and the same unsubscribe-function-returned-synchronously contract either way — this is the exact seam Phase 9's leak-prevention acceptance criteria test against.

## 4. Empty, Loading, and Error States

Three states, one pattern each, used identically everywhere in the app — no page invents its own variant:

- **Loading:** a skeleton (Phase 2's `Skeleton` primitive) shaped like the content that's coming, pulsing `--bg-panel` → `--bg-elevated` over 1.5s. Never a spinner — there are no spinners anywhere in this codebase.
- **Empty:** the `EmptyState` pattern (Phase 3) — an icon (Lucide, never emoji), a one-line explanation of *why* it's empty (not just "no data"), and where applicable a single action to resolve it (e.g. Loop's "No cycles run this session" empty state before the first run).
- **Error:** a `Toast` (Phase 2) for a transient failure (a single failed request that a retry might fix) or an inline banner within the affected panel for a persistent one (e.g. the backend genuinely unreachable) — never a blank screen, never a silently-frozen skeleton, never an unhandled promise rejection surfaced only in the console. A stream disconnecting mid-run (Loop page) gets its own explicit final state per Phase 9: a terminal timeline row reading "Connection lost — showing results through the last received cycle."

## 5. Appendix A — The Full Attack Taxonomy (25 entries)

Source: `docs/ATTACK_TAXONOMY.md`. `feasibility` converts the taxonomy's star ratings 1:1 (5 stars = 5); where the source gives no explicit rating, it defaults to `3` per Phase 0 step 4c's instruction, marked `(default)` below. `status` maps the taxonomy's symbols: `✅ Implemented` → `implemented`; `🔜 ... TO IMPLEMENT` / a named priority tier → `partial`; `🔜 Conceptual` / `⏸️ Future` → `conceptual`. `fraud_type` is populated only where the taxonomy or `docs/EXECUTION_STATUS.md` explicitly names the mapping (e.g. "Partial (ai_impersonation)", or EXECUTION_STATUS's "Added `synthetic_identity` fraud type (KYC-002)") — everywhere else it is `null`, per Phase 0's explicit instruction not to invent mappings the source doesn't state. `generator_profile_id` is non-null for exactly the four IDs Phase 0 locks: `SE-001`, `KYC-002`, `PR-003`, `AI-004`.

| id | name | category | status | feasibility | fraud_type | generator_profile_id |
|---|---|---|---|---|---|---|
| SE-001 | Voice Clone Impersonation | A | partial | 5 | ai_impersonation | voice_clone_scam |
| SE-002 | CEO Fraud Deepfake | A | conceptual | 3 | null | null |
| SE-003 | Romance Scam Automation | A | partial | 5 | ai_impersonation | null |
| SE-004 | Customer Service Impersonation | A | partial | 5 | ai_impersonation | null |
| SE-005 | Investment Scam Bot | A | partial | 5 | ai_impersonation | null |
| SE-006 | Charity Fraud at Scale | A | implemented | 5 | null | null |
| KYC-001 | Deepfake Identity Verification | B | conceptual | 3 | null | null |
| KYC-002 | Synthetic Identity Creation | B | partial | 5 | synthetic_identity | synthetic_identity_basic |
| KYC-003 | Document Forgery Automation | B | conceptual | 3 | null | null |
| KYC-004 | Account Farming Botnet | B | partial | 4 | null | null |
| KYC-005 | Biometric Spoofing | B | conceptual | 2 | null | null |
| PR-001 | UPI Intent Hijacking | C | conceptual | 3 (default) | null | null |
| PR-002 | QR Code Poisoning | C | conceptual | 3 (default) | null | null |
| PR-003 | BNPL Identity Abuse | C | partial | 3 (default) | bnpl_abuse | bnpl_max_out |
| PR-004 | Cross-Border Arbitrage | C | conceptual | 3 (default) | null | null |
| PR-005 | Subscription Creep | C | partial | 3 (default) | null | null |
| AI-001 | Prompt Injection Fraud | D | conceptual | 3 (default) | null | null |
| AI-002 | Model Extraction Attack | D | conceptual | 3 (default) | null | null |
| AI-003 | Adversarial Transaction Crafting | D | conceptual | 3 (default) | null | null |
| AI-004 | LLM-Jacking | D | conceptual | 3 (default) | null | llm_jacking |
| AI-005 | Autonomous Fraud Agent | D | conceptual | 3 (default) | null | null |
| BM-001 | Urgency Engineering | E | implemented | 3 (default) | null | null |
| BM-002 | Trust Calibration | E | conceptual | 3 (default) | null | null |
| BM-003 | Timing Optimization | E | conceptual | 3 (default) | null | null |
| BM-004 | Multi-Channel Orchestration | E | conceptual | 3 (default) | null | null |

**Category legend** (for the Identify page's filter chips, Phase 6): A = AI-Generated Social Engineering (6), B = Synthetic Identity & KYC Fraud (5), C = Payment Rail Exploitation (5), D = AI-Specific Attacks — the taxonomy's own "NOVEL" category (5), E = Behavioral Manipulation (4). AI-004 and AI-005 additionally carry a `NOVEL` badge per the taxonomy's own "Novel Contributions" section — judges should be able to find them in under 5 seconds (FRONTEND_VISION §3.2).

## 6. Appendix B — Fraud Types and Model Columns

Source: `src/config.py`. This is the single source of truth for the Generate page's profile picker, the Loop page's fraud-type-focus selector, and the Defend page's transaction builder form.

**`FRAUD_TYPE_TARGETS`** (7 keys — the exact spelling every `Select` component must match character-for-character):

| key | target count (train split) |
|---|---|
| `account_takeover` | 120 |
| `ai_impersonation` | 80 |
| `auth_bypass` | 220 |
| `bustout_identity` | 450 |
| `card_testing` | 340 |
| `synthetic_identity` | 100 |
| `bnpl_abuse` | 80 |
| **Total** | **1,390** |

**`MODEL_COLS`** (23 fields — 20 numeric `FEATURE_COLS` + 3 categorical `CAT_COLS`), the exact shape of the Defend page's transaction builder and of every `transaction` object anywhere in the API contract:

Numeric (`FEATURE_COLS`, 20): `amount`, `account_age_days`, `tx_last_1min`, `tx_last_1hr`, `tx_last_24hr`, `count_30d`, `amount_zscore_30d`, `new_device` (0/1), `new_merchant` (0/1), `merchant_cat_freq_user`, `time_since_last_s`, `dist_from_prev_km`, `geo_velocity_kmh`, `hour_of_day`, `three_ds_failures_before_result`, `three_ds_failures_last_30d`, `device_trust_age_days`, `burst_count_10m`, `is_high_amount_burst` (0/1), `inter_transaction_time_s`.

Categorical (`CAT_COLS`, 3): `merchant_category` (one of the 10 values below), `channel`, `three_ds_result`.

`merchant_category` values (from `CATEGORIES`): `grocery`, `restaurant`, `fuel`, `ecommerce`, `utility`, `travel`, `electronics`, `pharmacy`, `entertainment`, `clothing`.

**Business thresholds** (`BUSINESS_THRESHOLDS`, used by Defend's business-threshold table, Phase 8): `0.30`, `0.50`, `0.70`, `0.90`.

## 7. Appendix C — The Full API Contract

Source: `docs/UI_IMPLEMENTATION_FINDINGS.md` §4 (recovered from `docs/write_part1.ps1`–`write_part4.ps1`), reconciled with `FraudInferenceService`'s real method signatures in `src/fraud_model/inference.py`. This supersedes the shorter version in `docs/FRONTEND_VISION.md` §4 with per-endpoint implementation notes; where they differ only in prose, this is the authoritative wording.

```text
GET  /api/health
  -> { status: "ok" | "degraded", model_loaded: bool, data_loaded: bool, n_users: int }

GET  /api/attacks
  -> [{ id, name, category, status, feasibility, fraud_type, generator_profile_id,
       description }]   // all 25, per Appendix A

GET  /api/attacks/{id}
  -> single attack (same shape as above, plus full prose description) or 404

POST /api/generate
  body: { attack_id: str, user_id: int | "random", urgency: "low"|"medium"|"high" | null }
  -> { run_id, conversation: [...], transaction: {...},   // MODEL_COLS-shaped, Appendix B
       accepted: bool, rejection_reason?: str, drop_stats: { [reason: string]: number } }
  streams as SSE if the run takes > 2s; otherwise returns the full payload directly.
  Wraps rule_generator.generate_case_batch (rule path) or llm_generator's
  generate_llm_case_batch + materialize_llm_transaction (LLM path, gated by
  AFL_USE_LLM, silently falls back to rule-based on any error).

POST /api/predict
  body: { transaction: {...} }   // MODEL_COLS-shaped dict, Appendix B
  -> { probability: float, threshold: float, label: "legit"|"fraud",
       shap: [{ feature: string, value: float, impact: "positive"|"negative" }, ...] }
       // top 10 by |SHAP value|, signed
  Wraps FraudInferenceService.predict_single, then a per-row
  shap.TreeExplainer(model)(X_row) call (per-transaction SHAP is new work —
  the existing src/models/explain.py only writes static batch PNGs).

GET  /api/eval/per-class
  -> [{ fraud_type, count, precision, recall, pr_auc, fpr }]   // one row per
     FRAUD_TYPE_TARGETS key, Appendix B

GET  /api/eval/pr-curve
  -> { precision: [...], recall: [...], thresholds: [...],
       operating_point: { precision, recall, threshold } }

GET  /api/loop/history
  -> [{ run_id, started_at, duration_s, final_pr_auc, n_cycles, n_new_attacks }]

POST /api/loop/run
  body: { fraud_type: "all" | <one of the 7 FRAUD_TYPE_TARGETS keys>,
           n_new_attacks: int, max_cycles: int }
  -> streams SSE; each event is one of:
       { type: "cycle_start", cycle: int }
       { type: "miss_added", cycle: int, fraud_type: string, count: int }
       { type: "metric_update", cycle: int, metric: "recall"|"pr_auc"|"fn"|"precision",
         value: number }
       { type: "cycle_end", cycle: int }
  Wraps src/models/feedback_loop.py's main loop with a tee callback yielding
  these events as they happen; a StreamingResponse with
  media_type="text/event-stream", data: {json}\n\n lines.

GET  /api/system/status
  -> { online: bool, n_users: int, n_transactions: int, fraud_rate: float,
       pr_auc_test: float, last_retrain_at: string }
  n_transactions is a real row count of data/raw/transactions.csv (Appendix F);
  pr_auc_test is loaded from the frozen xgboost_tier1.json baseline.
```

Every endpoint additionally accepts `?demo=true` and returns canned data shaped identically to its live response — this is the backend-side half of "Demo Mode and the Fixture Data Layer" above; the frontend's own `VITE_DEMO_MODE` switch is the client-side half, and the two are independent safety nets, not the same mechanism.

## 8. Appendix D — The Full Design Token Sheet

Source: `docs/FRONTEND_VISION.md` §2.2–§2.4, identically reproduced in `docs/UI_IMPLEMENTATION_FINDINGS.md` §3.1–§3.3. This is the literal Tailwind v4 `@theme` block Phase 1 implements verbatim in `src/index.css` — hex values, not `oklch()` (see Phase 1's own note on why). The five-tier risk spectrum used by Phase 2's `Badge` component (`risk-critical`/`risk-high`/`risk-medium`/`risk-low`/`risk-minimal`) is **not** independently specified in any locked source — only the 3-tier `status-safe`/`status-warn`/`status-threat` set is. The two additional bands below (`risk-high`, `risk-low`) are completed here, now, by interpolating within the same locked hue family so the 5-tier badge and the 3-tier status system read as one consistent spectrum rather than two competing palettes; they are marked `(completed here)` and should be treated as a real decision to review, not as pre-existing lock the way everything else in this appendix is.

```css
@theme {
  /* Background */
  --bg-base:          #0A0E1A;   /* page background, deep navy-black */
  --bg-panel:          #0F1626;  /* card / panel background */
  --bg-elevated:       #161E33;  /* hover, focused, modals */
  --bg-grid:           #0D1322;  /* subtle grid texture layer */

  /* Borders */
  --border-subtle:     #1F2A44;
  --border-strong:     #2E3D5F;

  /* Text */
  --text-primary:      #E6ECFF;
  --text-secondary:    #8B9DC3;
  --text-muted:        #5A6B8A;
  --text-mono:         #B8C5DD;  /* IDs, hashes, tx_ids */

  /* Brand accent */
  --accent-cyan:       #00D4FF;  /* links, focus rings */
  --accent-cyan-dim:   #0088AA;  /* hover/disabled */

  /* 3-tier status (locked) */
  --status-safe:       #00FF88;
  --status-warn:       #FFB800;
  --status-threat:     #FF3D5A;

  /* 5-tier risk spectrum (minimal/low/medium/high/critical) */
  --risk-minimal:      #00FF88;  /* = --status-safe */
  --risk-low:          #7ED957;  /* (completed here) green→amber midpoint */
  --risk-medium:       #FFB800;  /* = --status-warn */
  --risk-high:         #FF6B35;  /* (completed here) = --loop-attack, amber→red midpoint */
  --risk-critical:     #FF3D5A;  /* = --status-threat */

  /* Loop diagram legs */
  --loop-attack:       #FF6B35;  /* Generate leg */
  --loop-defend:       #00D4FF;  /* Defend leg */
  --loop-identify:     #B47AFF;  /* Identify leg */
  --loop-improve:      #00FF88;  /* Improve/feedback leg */

  /* Typography */
  --font-sans:    "Inter", system-ui, -apple-system, sans-serif;
  --font-mono:    "JetBrains Mono", "Fira Code", monospace;
  --font-display: "Space Grotesk", "Inter", sans-serif;

  /* Layout */
  --radius-card:  8px;
  --radius-input: 4px;
  --radius-node:  0px;   /* loop diagram nodes only — sharp = technical */
  --max-w-home:   1280px;
  --max-w-docs:   1024px;
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Spacing is an 8px multiple everywhere (4px permitted only inside table cells) — expressed via Tailwind's default spacing scale, not a custom token, since the default scale is already 4px-based and a multiple-of-8 discipline is a usage convention, not a new token set. Motion timing (not a color/spacing token, but locked alongside them): loop diagram intro ~2.4s once on mount then a 4s pulse cycle; KPI count-ups 1.2s on first viewport entry, only one visible at a time; chart reveals 600ms left-to-right, easing `cubic-bezier(0.22, 1, 0.36, 1)`; hover transitions 150ms on borders/text only, no scale transforms.

## 9. Appendix E — TypeScript Type Definitions

Hand-typed interfaces for `lib/api/types.ts` (Phase 4), matching Appendix C field-for-field:

```ts
export type FraudType =
  | "account_takeover" | "ai_impersonation" | "auth_bypass"
  | "bustout_identity" | "card_testing" | "synthetic_identity" | "bnpl_abuse";

export type AttackCategory = "A" | "B" | "C" | "D" | "E";
export type AttackStatus = "implemented" | "partial" | "conceptual";

export interface Attack {
  id: string;                       // e.g. "SE-001"
  name: string;
  category: AttackCategory;
  status: AttackStatus;
  feasibility: 1 | 2 | 3 | 4 | 5;
  fraud_type: FraudType | null;
  generator_profile_id: string | null;
  description: string;
}

// MODEL_COLS-shaped — Appendix B
export interface TransactionRow {
  amount: number; account_age_days: number; tx_last_1min: number;
  tx_last_1hr: number; tx_last_24hr: number; count_30d: number;
  amount_zscore_30d: number; new_device: 0 | 1; new_merchant: 0 | 1;
  merchant_cat_freq_user: number; time_since_last_s: number;
  dist_from_prev_km: number; geo_velocity_kmh: number; hour_of_day: number;
  three_ds_failures_before_result: number; three_ds_failures_last_30d: number;
  device_trust_age_days: number; burst_count_10m: number;
  is_high_amount_burst: 0 | 1; inter_transaction_time_s: number;
  merchant_category: string; channel: string; three_ds_result: string;
}

export interface GenerateRequest {
  attack_id: string;
  user_id: number | "random";
  urgency: "low" | "medium" | "high" | null;
}
export interface GenerateResult {
  run_id: string;
  conversation: { role: string; content: string }[];
  transaction: TransactionRow;
  accepted: boolean;
  rejection_reason?: string;
  drop_stats: Record<string, number>;
}

export interface PredictRequest { transaction: TransactionRow }
export interface ShapFeature { feature: string; value: number; impact: "positive" | "negative" }
export interface PredictResult {
  probability: number; threshold: number; label: "legit" | "fraud";
  shap: ShapFeature[];
}

export interface EvalPerClassRow {
  fraud_type: FraudType; count: number;
  precision: number; recall: number; pr_auc: number; fpr: number;
}
export interface PrCurveResponse {
  precision: number[]; recall: number[]; thresholds: number[];
  operating_point: { precision: number; recall: number; threshold: number };
}

export interface LoopHistoryEntry {
  run_id: string; started_at: string; duration_s: number;
  final_pr_auc: number; n_cycles: number; n_new_attacks: number;
}
export interface LoopRunRequest {
  fraud_type: FraudType | "all"; n_new_attacks: number; max_cycles: number;
}
export type LoopEvent =
  | { type: "cycle_start"; cycle: number }
  | { type: "miss_added"; cycle: number; fraud_type: FraudType; count: number }
  | { type: "metric_update"; cycle: number; metric: "recall" | "pr_auc" | "fn" | "precision"; value: number }
  | { type: "cycle_end"; cycle: number };

export interface SystemStatus {
  online: boolean; n_users: number; n_transactions: number;
  fraud_rate: number; pr_auc_test: number; last_retrain_at: string;
}
export interface HealthResponse {
  status: "ok" | "degraded"; model_loaded: boolean; data_loaded: boolean; n_users: number;
}
```

## 10. Appendix F — The Real Numbers (Demo Data Source)

Every number below is real, sourced from `CHANGELOG.md`, `src/config.py`, and `data/raw/transactions.csv`'s actual row count — none is invented, per the forbidden-list rule "no fake numbers" (§Forbidden list above). This is the data `lib/demo-data/` (Phase 4) fixtures against, and what the Home page's KPI tiles and the Loop page's before/after panel display.

| Metric | Value | Source |
|---|---|---|
| Transactions scored | `1,064,963` | real row count, `data/raw/transactions.csv` |
| Baseline test PR-AUC (Tier 1 XGBoost) | `0.9072` | `CHANGELOG.md` |
| Attacks generated (sum of `FRAUD_TYPE_TARGETS`) | `1,390` | Appendix B |
| Val recall, before → after one feedback cycle | `0.8200 → 0.8467` | `CHANGELOG.md` |
| Test recall, before → after | `0.7834 → 0.7962` | `CHANGELOG.md` |
| False negatives, before → after | `34 → 32` | `CHANGELOG.md` |
| PR-AUC, before → after | `0.9072 → 0.9089` | `CHANGELOG.md` |
| Precision, before → after (threshold moved 0.96 → 0.94) | `0.9044 → 0.8562` | `CHANGELOG.md` — an operating-point tradeoff (catch more fraud, accept more manual review), not a regression; Defend's business-threshold table is where this tradeoff is made legible |
| `ai_impersonation` PR-AUC, SMOTENC-augmented run | `0.454 → 0.596` | `CHANGELOG.md`, a separate experiment track — cite only if the Loop page's demo fixture specifically exercises the SMOTENC path; the primary before/after pair above is the feedback-loop track |
| Tier 2 Isolation Forest PR-AUC | `~0.006` (near-random, documented deliberately) | `docs/FRONTEND_VISION.md` §1.2 — Defend's per-class table should make clear Tier 1 is the real detector, not silently omit Tier 2's weakness |

**Demo fixture transaction** (a real, valid `TransactionRow` — the exact dict `FraudInferenceService.health_check()` uses to smoke-test the model — use this as `lib/demo-data/`'s canonical "legit-looking" seed row rather than hand-inventing values that might not actually validate against the pipeline):

```json
{
  "amount": 100.0, "account_age_days": 365,
  "tx_last_1min": 0, "tx_last_1hr": 1, "tx_last_24hr": 5,
  "count_30d": 50, "amount_zscore_30d": 0.0,
  "new_device": 0, "new_merchant": 0,
  "merchant_cat_freq_user": 0.5,
  "time_since_last_s": 3600, "dist_from_prev_km": 0.0,
  "geo_velocity_kmh": 0.0, "hour_of_day": 12,
  "three_ds_failures_before_result": 0,
  "three_ds_failures_last_30d": 0, "device_trust_age_days": 30,
  "burst_count_10m": 0, "is_high_amount_burst": 0,
  "inter_transaction_time_s": 3600,
  "merchant_category": "grocery", "channel": "card_present", "three_ds_result": "success"
}
```

## 11. Appendix G — Explicitly Out of Scope / Future Work

Named in Phase 1 as "future, non-required work" and elsewhere as items a reviewer might reasonably ask about — listed here once so no phase re-litigates them:

- Migrating Appendix D's hex tokens to `oklch()` — a pure format refactor with zero visual change, worth doing eventually, out of scope for this build (Phase 1).
- The 12 taxonomy entries marked `conceptual` with no `generator_profile_id` (everything in Appendix A except the 4 wired IDs) — building real generator profiles for them is future work, not something any phase 0–11 does.
- Tier 2 Isolation Forest's near-random PR-AUC (~0.006) — documented honestly rather than hidden, and explicitly not this build's job to fix; the prototype's job is to represent it accurately, not to improve it.
- KYC-001/003/005 (deepfake KYC verification, document forgery, biometric spoofing) and the four `Future`/`Conceptual` Behavioral Manipulation attacks (BM-002/003/004) — real attack classes with no simulation or detection work planned in this hackathon window.
- Any hosted/deployed version of the prototype (Vercel, Netlify, etc.) — FRONTEND_VISION §7 locks this as local-only for the submission; a public deployment is future work if the project continues past the hackathon.
- CTGAN-based synthetic augmentation (scripts exist per `CHANGELOG.md`, kept for future classes) — not part of the frontend's demo path; the Loop page's live run exercises the feedback-loop track (Appendix F), not the CTGAN track.

---

# Phase 0 — Scaffold

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

You are one of potentially several different AI coding models that will work
on this codebase across several sessions. You have no memory of any prior
session. Everything you need is either in this prompt, in the project's
existing files, or in `frontend/PROGRESS.md` if it already exists (it does
not yet, for this phase — you are about to create it).

PROJECT: "Adversarial Fraud Lab" (AFL) — a closed-loop red-team/blue-team
web prototype for the Mastercard Innovation Challenge @ GFF 2026 (a payment
fraud hackathon). Three pillars — Identify, Generate, Defend — plus a
closed feedback Loop connecting them. This phase builds nothing visual; it
builds the ground everything else stands on: a clean Vite/React/TypeScript
scaffold at the exact dependency versions already proven to work together,
the folder skeleton every later phase will fill in, and a thin FastAPI
backend skeleton so the frontend has something real to talk to from day one.

GOVERNING PRINCIPLE FOR THIS ENTIRE BUILD ("bare minimum but very flexible
and scalable"): no dependency, folder, or abstraction exists unless a named
later phase needs it. Every folder you create in this phase maps to exactly
one concern from the tree below. Feature folders (created empty in this
phase, filled in later) never import from each other — only from
`design-system/`, `chrome/`, and `lib/`. If you are ever unsure whether to
add something "just in case," don't — a later phase will ask for it
explicitly if it's needed, and adding it now violates "bare minimum."

BEFORE YOU START: confirm the existing `frontend/` folder has already been
deleted (the user has been instructed to do this before Phase 0 runs). If it
still exists, delete it entirely — nothing in it is reused. The one exception
is intellectual, not literal: the deleted folder's `src/index.css` had
independently drifted toward a light, Stripe-style token system before being
abandoned in favor of the eventually-locked (and now further-revised) dark
"cyber-command" direction. That instinct was correct even though the file
itself is being deleted — Phase 1 (not this phase) re-derives it properly
from this document's own token spec, not from the old file's literal values.
Do not copy any file, value, or class name forward from the deleted folder.

YOUR TASK, IN ORDER:

1. Scaffold the frontend. From the repository root:
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   Then install every dependency below at the stated major version (use
   `npm install <pkg>@<major>` per row, or add them to package.json and run
   `npm install` once — either approach is fine, but install ALL of them
   before verifying anything, so version resolution happens once):

   Runtime dependencies:
   - react@19, react-dom@19
   - react-router-dom@7
   - @tanstack/react-query@5
   - @tanstack/react-table@9
   - zustand@5
   - lucide-react@1
   - recharts@3
   - reactflow@11
   - framer-motion@13   (npm package name for the "Motion" library)
   - react-hook-form@7
   - zod@3
   - date-fns@4
   - date-fns-tz@3
   - cmdk@latest         (NEW — not in any prior scaffold, needed for the
     command palette; small, ~2KB gzip)

   Dev dependencies:
   - typescript@~6.0 (should already match the Vite template's default —
     confirm, don't downgrade if the template ships newer)
   - tailwindcss@4, @tailwindcss/vite@4
   - @types/node, @types/react@19, @types/react-dom@19
   - oxlint (keep whatever the Vite template scaffolds — do not replace with
     eslint; oxlint is a deliberate choice, fast and zero-config)
   - prettier@latest (NEW — add a minimal `.prettierrc` with 2-space indent,
     double quotes false i.e. use double quotes matching the Vite template
     default, semi true, printWidth 100 — pick sane defaults and move on,
     this is explicitly a "no bikeshedding" decision)
   - @playwright/test@latest (NEW, dev-only — do not run any tests yet,
     Phase 10 writes and runs them; this phase only installs the package and
     creates an empty `playwright.config.ts` pointing at `tests/e2e/`)

   Do NOT install: Next.js, Tremor, Redux/Redux Toolkit, any CSS-in-JS
   library, GraphQL/Apollo, any prebuilt admin dashboard template, any
   additional icon set beyond lucide-react, any additional chart library
   beyond Recharts. If you find yourself wanting one of these to make a
   later step easier, stop — it is explicitly out of scope for this project,
   for reasons already decided and not open for re-litigation in this phase.

2. Configure Tailwind v4. Use the `@tailwindcss/vite` plugin in
   `vite.config.ts` (not the PostCSS plugin path). Do not write a
   `tailwind.config.ts` with a `content` array or a `theme.extend` block —
   Tailwind v4's CSS-first `@theme` directive is where all tokens live, and
   that file is Phase 1's job, not this phase's. For this phase, leave
   `src/index.css` as whatever the Vite template generated (Phase 1 replaces
   it entirely) but DO wire the Tailwind Vite plugin into `vite.config.ts` so
   `@import "tailwindcss";` will work the moment Phase 1 adds it.

3. Create the exact folder tree below. Every folder listed gets created,
   even if empty (use a `.gitkeep` file in any directory with zero files, so
   git tracks it and the next phase can see the intended structure). Do NOT
   create any file inside `design-system/`, `chrome/`, `features/`, or `lib/`
   beyond what's listed — those are later phases' work; this phase
   only creates the empty containers plus the handful of root-level config
   files explicitly listed.

   frontend/
   ├── index.html                  (Vite default, unmodified)
   ├── package.json
   ├── tsconfig.json
   ├── tsconfig.app.json
   ├── tsconfig.node.json
   ├── vite.config.ts              (with @tailwindcss/vite wired in)
   ├── .prettierrc
   ├── .env.example                (see step 5 below)
   ├── playwright.config.ts        (skeleton only, points at tests/e2e/)
   ├── PROGRESS.md                 (see step 6 below — created THIS phase)
   ├── public/
   │   └── favicon.svg             (Vite default is fine for now)
   ├── tests/
   │   └── e2e/                    (empty, .gitkeep — Phase 10 fills this)
   └── src/
       ├── main.tsx                (Vite default — Phase 5 rewrites it with
       │                            providers; leave the default App render
       │                            for now so `npm run dev` boots)
       ├── App.tsx                 (Vite default — Phase 5 rewrites entirely)
       ├── index.css               (Vite default — Phase 1 rewrites entirely)
       ├── design-system/
       │   ├── primitives/         (empty, .gitkeep)
       │   ├── patterns/           (empty, .gitkeep)
       │   └── icons.ts            (do NOT create yet — Phase 2's file)
       ├── chrome/                 (empty, .gitkeep)
       ├── features/
       │   ├── home/               (empty, .gitkeep)
       │   ├── identify/           (empty, .gitkeep)
       │   ├── generate/           (empty, .gitkeep)
       │   ├── defend/             (empty, .gitkeep)
       │   └── loop/               (empty, .gitkeep)
       └── lib/
           ├── api/                (empty, .gitkeep)
           ├── demo-data/          (empty, .gitkeep)
           └── (store.ts, use-event-stream.ts, format.ts, constants.ts —
                do NOT create yet, Phase 4's files)

   Note the deliberate omission: `design-system/icons.ts` is listed in the
   final tree in "Folder & File Structure" above, but you do not create it
   this phase — creating an empty or stub barrel file now just means Phase 2
   has to remember to check whether it's a stub or real. Leave the container
   folder empty and let the phase that actually needs the file create it.

4. Backend handshake. Do NOT build out the full FastAPI contract this
   phase — that is implicit in every later phase's `use-*.ts` hooks calling
   a real endpoint, but the actual endpoint *logic* (wrapping
   `FraudInferenceService`, the generators, the feedback loop) is ongoing
   work alongside the frontend, not a Phase 0 deliverable. This phase's
   backend responsibility is narrower and more urgent, because it blocks the
   Identify page entirely if skipped:

   a. Create `src/api/main.py` — a FastAPI app instance, mounted so that
      running `uvicorn src.api.main:app --reload --port 8000` serves
      `GET /api/health` returning
      `{ "status": "ok", "model_loaded": false, "data_loaded": false, "n_users": 0 }`
      as a literal stub for now (later phases' backend work fills in the
      real values — this phase only proves the process boots and CORS is
      configured so `http://localhost:5173` — Vite's default dev port — can
      call it without a browser CORS error).
   b. Add permissive CORS middleware scoped to local dev origins only
      (`[http://localhost:5173]`, `[http://127.0.0.1:5173]`) — do not open it to
      `*` even though there's no auth, as a matter of not-sloppy default
      practice, not because judges will ever hit this from another origin.
   c. UNIFY THE ATTACK TAXONOMY — this is the one piece of non-frontend work
      that must happen in this phase specifically, because it blocks the
      Identify page (Phase 6) and the Generate page's attack-picker (Phase
      7) entirely, and doing it once now prevents a third drifting copy.
      Two sources currently disagree: `docs/ATTACK_TAXONOMY.md` (25 entries,
      prose/markdown, human-readable — see Appendix A for the full extracted
      table) and `src/identify/attack_profiles.py` (4 machine-readable
      profiles: `voice_clone_scam` → SE-001, `synthetic_identity_basic` →
      KYC-002, `bnpl_max_out` → PR-003, `llm_jacking` → AI-004). Produce
      `src/identify/attacks.json` (or `.yaml`, your choice, but `.json` is
      simpler for both a Python reader and the frontend's demo fixture to
      share byte-for-byte) containing all 25 entries from Appendix A, each
      with: `id`, `name`, `category` (A–E), `status`
      (`implemented`/`partial`/`conceptual`), `feasibility` (1–5, from the
      star ratings in Appendix A — where Appendix A has no explicit rating,
      default to 3 and note it as an assumption in this phase's
      `PROGRESS.md` entry, per "don't assume anything as understood" — a
      genuinely silent default is exactly the failure mode that principle
      exists to prevent), `fraud_type` (the underlying `FRAUD_TYPE_TARGETS`
      key it maps to, where one exists — several conceptual attacks have no
      `fraud_type` mapping yet, which is fine, leave that field `null`), and
      `generator_profile_id` (one of the four keys above, or `null` for the
      21 entries with no wired profile). This file is the new single source
      of truth — a future edit to `docs/ATTACK_TAXONOMY.md` alone, without
      touching this file, is now the kind of drift this phase exists to
      prevent, and is worth a one-line comment at the top of the new file
      saying so.
   d. Wire `GET /api/attacks` to read and return `src/identify/attacks.json`
      as a JSON array, and `GET /api/attacks/{id}` to return one entry by
      `id` or a 404. These two endpoints are genuinely simple — a static
      file read, no model inference involved — so there's no reason to defer
      them to a "backend phase" that doesn't formally exist in this
      12-phase plan. Every other endpoint in the full contract (Appendix C)
      remains a TODO for whoever is driving the backend in parallel with the
      rest of this plan; this phase does not implement `/api/predict`,
      `/api/generate`, `/api/eval/*`, or `/api/loop/*` — it only proves the
      process boots, CORS works, and the two attack-list endpoints are real.

5. Create `.env.example` with exactly two variables, both commented with a
   one-line explanation:
   VITE_API_BASE_URL=http://localhost:8000
   VITE_DEMO_MODE=true
   Do NOT create a real `.env` file with secrets — there are none needed for
   the frontend. `VITE_DEMO_MODE=true` is the correct default for this
   phase and for most of the build, per "Demo Mode and the Fixture Data
   Layer" above — it flips to `false` only in Phase 11, on demo day itself.

6. Create `frontend/PROGRESS.md` with the exact header and format shown in
   "The Multi-Model Handoff Protocol" above, then append this phase's own
   entry to it (you are the first entry, so the file will contain the header
   plus exactly one entry when you're done).

7. Update `docs/DESIGN_SYSTEM.md`'s body (leave the file path and name
   unchanged) to a single pointer: replace everything below its title with
   one line stating that the authoritative design system now lives in this
   document (`docs/afl_frontend_spec.md` or wherever your team saved this
   Build Bible — use its actual path) and that `docs/DESIGN_SYSTEM.md` is
   kept only as a redirect so a future editor doesn't independently revise a
   third copy. This closes the exact documentation-drift loop named in "A
   verification note before Phase 0 begins" above.

DO NOT, IN THIS PHASE:
- Write any component, page, or visual code. This phase produces zero pixels
  on screen beyond whatever Vite's default template renders unmodified.
- Touch `docs/FRONTEND_VISION.md`, `frontend-vision.md`, or
  `docs/UI_IMPLEMENTATION_FINDINGS.md` — they are historical record, not
  live documents; only `docs/DESIGN_SYSTEM.md` gets the redirect treatment,
  because it's the one still actively claiming to be a source of truth.
- Implement `/api/predict`, `/api/generate`, `/api/eval/*`, or `/api/loop/*`
  — real or stubbed. Leave them entirely absent from `main.py` for now
  rather than adding placeholder stubs for them; an absent route is honest
  about what doesn't exist yet, a stub route that returns fake data risks
  being mistaken for real later.
- Add a `tailwind.config.ts` with a `content`/`theme.extend` block. All
  tokens live in `src/index.css`'s `@theme` block starting in Phase 1.
- Change any dependency version from the table above "because a newer one is
  available" — these versions are the ones already proven to install and
  resolve together correctly; treat them as pinned unless a specific later
  phase tells you to bump one for a specific, named reason.

ACCEPTANCE CRITERIA — verify every one of these yourself, against the
running app and the actual files, not against your own summary:
[ ] `cd frontend && npm install && npm run dev` boots with zero console
    errors and zero terminal warnings about peer-dependency conflicts.
[ ] `npm run build` completes successfully (proves the TypeScript config
    and Tailwind wiring are both sound, even though there's no real content
    yet).
[ ] The exact folder tree in step 3 exists, verified with a recursive
    directory listing — every named folder is present, `.gitkeep` files are
    in every empty one, and nothing beyond what's listed exists.
[ ] `frontend/PROGRESS.md` exists, matches the header format exactly, and
    has exactly one entry (this phase's).
[ ] `docs/DESIGN_SYSTEM.md` now contains only the redirect pointer, not its
    old v3.0.0 body.
[ ] `uvicorn src.api.main:app --reload --port 8000` boots; `curl
    http://localhost:8000/api/health` returns the literal stub JSON in step
    4a; a browser fetch from a page served on `http://localhost:5173` to
    `http://localhost:8000/api/attacks` succeeds with no CORS error in the
    console (you can verify this with a one-line temporary `fetch()` call
    typed into the running Vite app's console — do not leave that call in
    any committed file).
[ ] `src/identify/attacks.json` exists, contains exactly 25 entries, and
    every entry has all six fields (`id`, `name`, `category`, `status`,
    `feasibility`, `fraud_type`, `generator_profile_id` — seven fields,
    correcting the count) with `generator_profile_id` populated for exactly
    the four IDs `SE-001`, `KYC-002`, `PR-003`, `AI-004` and `null`
    everywhere else.
[ ] `GET /api/attacks` returns all 25 entries as JSON; `GET
    /api/attacks/SE-001` returns exactly that one entry; `GET
    /api/attacks/does-not-exist` returns a 404.

BEFORE YOU FINISH: append your entry to `frontend/PROGRESS.md` per "The
Multi-Model Handoff Protocol" format above — what exists now (be literal:
list the files), any decision you had to make because this prompt was
silent (the feasibility-default-to-3 case in step 4c is the likely one),
what's left for Phase 1, and which acceptance-criteria items you personally
verified and how.

---

# Phase 1 — Design Tokens

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. It should show
Phase 0 as DONE, with a working Vite/React/TypeScript scaffold, an empty
folder skeleton, and a FastAPI stub serving two real endpoints
(`/api/health`, `/api/attacks`). If `PROGRESS.md` says something that looks
wrong against the live code, trust the code, fix `PROGRESS.md`, and note the
correction in your own entry.

PROJECT: "Adversarial Fraud Lab" (AFL) — see Phase 0's context block above
for the one-paragraph project summary if you need it; it is not repeated
here in full to keep this phase prompt focused, but you do not need it to
do this phase's work, which is narrow and precise: this phase writes exactly
one file, `frontend/src/index.css`, and writes it completely, correctly, and
verbatim from Appendix D ("The Full Design Token Sheet") below. There is no
design judgment to exercise in this phase — the judgment was already
exercised when this document's "Design Tokens: The Final Aesthetic
Decision" section was written. Your job is precise, faithful transcription,
not reinterpretation.

WHY THIS MATTERS MORE THAN IT LOOKS LIKE IT SHOULD: every single visual
decision in every later phase (Phase 2 through Phase 9) references a token
by name from this file — `var(--color-accent)`, `var(--text-page-title)`,
`var(--space-6)`, and so on. If this phase introduces even one typo in a
token name, or silently "improves" a value, every later phase either breaks
visibly or — worse — silently falls back to a browser default that looks
almost, but not quite, right. Treat this file the way you'd treat a
generated API type file: it is meant to be exactly correct, not creatively
interpreted.

WHAT TO CARRY FORWARD FROM THE NOW-DELETED OLD SCAFFOLD, AND WHAT NOT TO —
stated explicitly here so you do not have to go looking for the deleted
file (it's gone; this is the full record of what mattered in it):

| From the old `src/index.css` | Carry forward? | How |
|---|---|---|
| The *mechanism* of defining tokens in a Tailwind v4 `@theme` block | Yes | Appendix D below already uses this mechanism — just implement it |
| The *idea* of perceptually-uniform color definition (the old file used `oklch()` for every color) | Not literally — the token values below are specified in hex, and hex is what you implement, verbatim. Converting them to `oklch()` equivalents would risk a subtle color drift from a from a lossy or imprecise conversion, which is exactly the kind of silent value-substitution this phase must not do | Implement the hex values in Appendix D exactly as written. If, after everything else in this entire build is complete, someone wants to migrate the token *format* from hex to `oklch()` as a pure refactor with zero visual change, that is a fine future task — it is explicitly out of scope for this phase and for this hackathon build |
| The keyframe scaffolding (`fadeIn`, `fadeInUp`, `fadeInScale`, `slideInLeft`, `shimmer`) | Partially | `shimmer` is genuinely reusable for the `Skeleton` primitive (Phase 2). The others are fine to keep as generic, reusable keyframes IF a later phase actually needs them for the one-orchestrated-motion-moment-per-page rule — do not wire them to anything in this phase, just keep the `@keyframes` definitions available in `index.css` under a clearly-commented section, since keyframe definitions costing nothing until referenced is different from speculative component code |
| `pulseGlow` keyframe | No | "Glow" as an effect reads as exactly the kind of generic AI-dashboard decoration this build's anti-pattern checklist forbids; the settled-state loop-diagram pulse (Phase 3) uses a plain opacity pulse, not a glow/blur effect |
| The five-tier risk-score threshold concept (critical/high/medium/low/minimal) | Yes | Already present, correctly, in Appendix D's risk-color tokens — this was a good instinct in the old file and Appendix D already reflects it |
| `.glass` (backdrop-blur over translucent panel) | No — discard entirely | Never write a `backdrop-filter: blur(...)` rule anywhere in this codebase. This is anti-pattern #6 |
| `.hover-lift` (translateY(-2px) + shadow on hover) | No — discard entirely | Never write a `transform` on any `:hover` rule anywhere in this codebase for a card, button, or tile. Border-color/background-color transitions only |
| `.text-gradient` (gradient text-fill) | No — discard entirely | No gradients anywhere in this build, on text or on fills |
| `.grain` (noise-texture overlay) | No — discard entirely | Decorative texture with no functional purpose |
| The fixed 280px sidebar layout | No — discard entirely | This build has no sidebar; see "Sitemap and Navigation Model" above |

YOUR TASK:

1. Replace the entire contents of `frontend/src/index.css` with the CSS in
   "Appendix D — The Full Design Token Sheet" below, verbatim. Do not
   reorder sections, rename tokens, round any color value, or "clean up"
   anything you find inconsistent — if you genuinely believe something in
   Appendix D is wrong, flag it in your `PROGRESS.md` entry as a discrepancy
   rather than silently correcting it, per this whole document's own
   discipline of naming disagreements instead of quietly resolving them.

2. Confirm `@import "tailwindcss";` is the first line of the file, above the
   `@theme { ... }` block, exactly as Appendix D shows.

3. Build one temporary, throwaway verification view so you (and whoever
   reviews this phase) can actually see the tokens rendering, since a CSS
   file with no consumer is unverifiable by eye. In `src/App.tsx` — which
   Phase 5 will fully rewrite, so anything you put here now is explicitly
   temporary — render a plain, unstyled-by-any-component grid of `<div>`s,
   each with an inline `style` (not Tailwind classes, so you're testing the
   raw CSS custom properties, not Tailwind's own defaults) that sets
   `background: var(--color-bg-base)`, `color: var(--color-fg-primary)`,
   etc., one div per token category (surfaces, foreground, borders, accent,
   risk spectrum, loop-leg colors, chart palette), each labeled with its own
   token name as visible text. Also render one `<div class="console">`
   wrapper with a few of its own child divs using the console-scoped
   variables, so you can visually confirm `.console` correctly overrides
   what's inside it and does NOT leak outside itself (check by putting a
   normal, non-console div immediately after it and confirming it stays
   light). This entire verification view is deleted by whoever runs Phase 2
   or Phase 5, whichever touches `App.tsx` first — say so explicitly in a
   `// TEMPORARY — Phase 1 token verification, delete in Phase 2/5` comment
   at the top of the block so nobody mistakes it for real UI.

4. Confirm the two font families load. Add `<link>` tags for Google Fonts
   "Inter" (weights 400/500/600/700) and "JetBrains Mono" (weights
   400/500/700) to `index.html`'s `<head>` — self-hosting fonts is a fine
   future optimization but is out of scope for "bare minimum" in a 3-day
   build; a CDN link is correct here.

DO NOT, IN THIS PHASE:
- Touch any file other than `src/index.css`, `index.html` (fonts only), and
  the temporary verification block in `src/App.tsx`.
- Build any shadcn/ui primitive, even a trivial one. That is Phase 2,
  entirely.
- Add any color, spacing, radius, or motion value that is not already in
  Appendix D. If a later phase seems to need one, that phase's own prompt
  will say so explicitly (and if it doesn't and you're running that later
  phase and you find yourself needing one anyway, that is a signal to add
  it to this document's token sheet first, and only then consume it — never
  invent a one-off value inline in a component file).
- Implement a manual light/dark whole-app theme toggle. That is optional,
  future, non-required work described in "Appendix G" — not this phase.

ACCEPTANCE CRITERIA:
[ ] `frontend/src/index.css` matches Appendix D verbatim — diff it yourself,
    token by token, against the appendix; do not eyeball it.
[ ] `npm run dev` renders the temporary verification grid with zero
    unstyled/fallback-black text, meaning every `var(--...)` reference
    resolves (an unresolved CSS variable renders as the property's initial
    value, which for `color` is often black — that visual tell is your
    check).
[ ] The `.console` wrapper's child divs render with the dark palette; a
    sibling div immediately outside `.console` renders with the light
    palette; opening dev tools and inspecting confirms `--color-bg-base`
    resolves differently inside vs. outside the `.console` class.
[ ] Both "Inter" and "JetBrains Mono" are visibly loaded (inspect the
    Network tab for font file requests, or confirm via computed style that
    body text is not falling back to a system sans-serif).
[ ] `prefers-reduced-motion` media query block from Appendix D's motion
    tokens section is present in the file (it has nothing to visually
    verify yet since no component uses motion tokens until Phase 3, but its
    presence in the file is itself checkable).

BEFORE YOU FINISH: append your `PROGRESS.md` entry — confirm this is a
small, clean phase with almost nothing to report as a "decision made" (if you
made one, it means you deviated from Appendix D and should say precisely
where and why), and explicitly flag the temporary `App.tsx`
verification block as something Phase 2 or Phase 5 must delete.

---

# Phase 2 — Primitives

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. It should show
Phase 0 (scaffold) and Phase 1 (design tokens) as DONE. `src/index.css`
should already contain the full token sheet from Phase 1. Do not
re-derive or second-guess those tokens in this phase — consume them.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL), a fraud-detection hackathon
prototype. This phase's job: build every primitive listed in "Component
Library Plan" above, under "Primitives (`design-system/primitives/`) — visual only, no business logic." These are the lowest-level building blocks — buttons, cards, badges, inputs — that every later feature page composes. None of them know anything about fraud, attacks, or transactions; they only know about the design tokens from Phase 1 and, where relevant, Radix primitives via shadcn/ui.

HOW TO GET THE SHADCN BASE COMPONENTS: use the shadcn/ui CLI
(`npx shadcn@latest init`, then `npx shadcn@latest add button card badge
input select slider tabs table tooltip sheet dialog skeleton progress
toast` — the exact command may vary slightly by current shadcn CLI version,
adapt as needed) to copy the source of each component into
`src/design-system/primitives/`. This is a deliberate, load-bearing
architecture choice already made in "Technology Stack Decision" above:
shadcn/ui is copied-in source you own and can restyle completely, not a
themed component *library* dependency you'd otherwise be fighting the
defaults of. After the CLI copies each file in, you will restyle every one of
them to reference this project's own tokens (`var(--color-accent)`,
etc.) instead of shadcn's own default Tailwind-gray-scale styling — do not
leave a single shadcn default color, spacing, or radius value in any
component; every visual value must trace to a token from Appendix D.

THE FULL LIST TO BUILD, WITH VARIANTS — do not build anything beyond this
list, and do not skip anything on it:

| Component | Built from | Variants you must implement |
|---|---|---|
| `Button` | shadcn base, restyled | `primary` (filled `--color-accent`, white text), `secondary` (bordered, `--color-border-strong`, `--color-fg-primary` text), `ghost` (text-only, `--color-fg-secondary`, `--color-accent` on hover) |
| `Card` | plain div + tokens (shadcn's card is optional scaffolding — a plain styled div is equally correct here and arguably more "bare minimum") | `default` (light surface, `--color-bg-base`, 1px `--color-border-default`), `bordered` (used only inside `.console`-wrapped contexts — same shape, dark tokens) |
| `Badge` | shadcn base | `neutral`, `risk-critical`, `risk-high`, `risk-medium`, `risk-low`, `risk-minimal` (colors from Appendix D's risk spectrum), `loop-identify`, `loop-generate`, `loop-defend`, `loop-improve` (colors from Appendix D's loop-leg tokens) — nine variants total, every one takes a required `label` prop (never render color alone, per Accessibility Standards) |
| `Input` | shadcn base wrapping Radix | text and number types, both restyled to tokens (border `--color-border-default`, focus ring `--color-border-focus`) |
| `Select` | shadcn base wrapping Radix | single-select only — no multi-select variant is needed by any page spec, so don't build one |
| `Slider` | shadcn base wrapping Radix | single-handle range only |
| `Tabs` | shadcn base wrapping Radix | build it, but do not wire it into any page yet — per "Component Library Plan," no current page needs in-page tabs; this is deliberately built ahead of a concrete need only because it's explicitly named in the plan as future-flexibility scaffolding, which is the one exception to "don't build ahead of need" this whole document makes, and it makes it explicitly rather than by accident |
| `Table` | shadcn base + `@tanstack/react-table` bindings | `compact` and `default` row-density variants; sortable column headers |
| `Tooltip` | shadcn base wrapping Radix | one variant, used for SHAP explanations and chart data points later |
| `Sheet` | shadcn base wrapping Radix Dialog | slide-in from the right, used later for the Identify attack-detail drawer |
| `Dialog` | shadcn base wrapping Radix | used later for the command palette (via `cmdk`, composed inside this `Dialog`) |
| `Skeleton` | plain div + shimmer animation (reuse the `shimmer` keyframe you preserved-but-didn't-wire in Phase 1 — this is where it finally gets consumed) | one variant, sized via `className`/`style` props from the call site, since a skeleton must match the shape of whatever it's standing in for |
| `Progress` | plain div | one horizontal bar variant, 0–100 |
| `Toast` | shadcn base | one variant, error-only in practice (per "Empty, Loading, and Error States" above) but build it generically, not hardcoded to one message |

RULES YOU MUST FOLLOW WHILE BUILDING THESE:
- No spinners, anywhere, ever — `Skeleton` is the only loading affordance in
  this entire codebase. If you find a shadcn component's default includes a
  spinner (some `Button` loading states do), strip it out.
- No `backdrop-blur`, no `box-shadow` beyond `--shadow-sm` (cards on hover
  only) and `--shadow-md`/`--shadow-lg` (Sheet/Dialog overlays only — never
  on a card).
- No `transform` on any `:hover` state, on anything.
- Every color, spacing, radius, and font value must be a `var(--...)`
  reference to a Phase-1 token. Grep your own output for raw hex codes or
  raw pixel values before considering this phase done — if you find any
  (other than inside the token file itself), replace them.
- Delete the temporary Phase-1 token-verification block from `src/App.tsx`
  now, if Phase 1 left it (check `PROGRESS.md`) — replace it with a
  similarly temporary, similarly clearly-commented showcase of every
  primitive and variant you just built (one of each, labeled), so this
  phase is visually verifiable the same way Phase 1 was. This new temporary
  block is, in turn, Phase 5's responsibility to delete.

DO NOT, IN THIS PHASE:
- Build anything from "Patterns (`design-system/patterns/`)" — `KpiTile`,
  `RiskBadge`, `StatusPill`, `FilterBar`, `CountUp`, `EmptyState` are Phase
  3's work, not this phase's, even though they're composed from these
  primitives. The primitives/patterns split is deliberate: primitives know
  nothing about this product's domain (risk, loops, fraud); patterns do.
- Create `src/design-system/icons.ts` yet unless you need to import an icon
  for a primitive that genuinely requires one right now (e.g., a `Select`'s
  chevron, a `Sheet`'s close button, a `Toast`'s dismiss icon) — if you do
  need one, create the icons barrel now with only the specific icons you
  actually used, and note in `PROGRESS.md` that Phase 3 will extend it
  rather than create it fresh. Do not pre-populate it with the full icon
  list from "Icon barrel" above speculatively.
- Wire any primitive to real or demo data. These components take props and
  render; they do not fetch anything.

ACCEPTANCE CRITERIA:
[ ] Every component and every variant in the table above exists in
    `src/design-system/primitives/` and renders correctly in the temporary
    showcase.
[ ] `grep -rn "backdrop-blur\\|box-shadow: 0 .* 0 .*px .* rgb\\|scale(" src/design-system/primitives/`
    (adapt the pattern to your shell) returns nothing outside of the allowed
    `--shadow-sm`/`--shadow-md`/`--shadow-lg` token usages.
[ ] No component in `design-system/primitives/` imports directly from
    `lucide-react` except through `design-system/icons.ts`, if that file
    exists yet.
[ ] Every `Badge` variant requires and renders a text `label`, never color
    alone — confirmed by trying to render one without a label and
    confirming TypeScript's prop types actually make that impossible, not
    just discouraged by convention.
[ ] Tab-key navigation through the showcase page reaches every interactive
    primitive in a logical order, and each shows the 2px accent focus ring
    from Appendix D — never a suppressed `outline: none`.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — list every primitive
built, note whether you created `icons.ts` (and with which icons, if so),
and flag the new temporary showcase block in `App.tsx` for Phase 5 to
remove.

---

# Phase 3 — Patterns (including the Loop Diagram)

Phase 3 — Patterns (including the Loop Diagram)

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0
(scaffold), 1 (tokens), and 2 (primitives) should be DONE. You have a full
set of restyled `Button`/`Card`/`Badge`/`Input`/`Select`/`Table`/etc.
available to compose from `src/design-system/primitives/`.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL) is a closed-loop
fraud-detection system with four conceptual stages — Identify, Generate,
Defend, Improve (the last one feeds back into Identify) — that this whole
product visualizes as a loop. This phase builds that loop diagram, plus
every other domain-aware "pattern" component from "Component Library Plan"
above. This is explicitly flagged, in this document's own phase-sequencing
guidance, as the single highest-visual-risk phase in the entire build —
give it your most careful attention, especially around motion and color
restraint, because the loop diagram is the one component that appears on
both the Home page (as this whole project's signature image) and the Loop
page (as its live, running centerpiece), and it is the single easiest place
in this codebase for a "make it look cool" impulse to reintroduce exactly
the AI-generic tells ("The Anti-'AI-Generic' Checklist" above) this entire
document exists to prevent — a bounce, a glow, a gradient, a scale-on-hover,
an extra flourish nobody asked for. Build exactly what is specified below,
nothing more.

BUILD, IN THIS ORDER:

1. `src/design-system/patterns/loop-diagram.tsx` — THE MOST IMPORTANT FILE
   IN THIS PHASE. Built with React Flow (`reactflow`), per "Technology Stack
   Decision"'s explicit reasoning for choosing it over a hand-built SVG:
   flexibility to add a fifth pillar later by editing a data array, not
   hand-editing path coordinates.

   - Four custom React Flow nodes, one per loop leg (Identify, Generate,
     Defend, Improve), each 88×88px, rounded square, `--color-bg-base`
     fill, a 2px border in that leg's color token
     (`--color-loop-identify`/`-generate`/`-defend`/`-improve`), a centered
     Lucide icon (Identify → `Radar`, Generate → `GitBranch`, Defend →
     `ShieldCheck`, Improve → `TrendingUp`) in the same leg color, and a
     text label below the node in `--text-caption`.
   - Fixed, non-draggable layout matching the ASCII diagram in "The loop
     diagram (shared component...)" above: Identify at top-center, Generate
     at right, Improve at bottom-center, Defend at left, edges flowing
     clockwise (Identify → Generate → Defend... — re-read that section's
     exact arrow directions before wiring edge sourceHandle/targetHandle so
     you match it exactly, not an approximation of it). Disable node
     dragging and viewport pan/zoom via React Flow's props (`nodesDraggable=
     {false}`, `panOnDrag={false}`, `zoomOnScroll={false}`, etc.) for THIS
     component's default configuration — Phase 9 (Loop page) will render
     this same component with a prop flag that re-enables pan/zoom for its
     "running" context, so build the prop into this component now
     (`interactive?: boolean`, default `false`) rather than hardcoding
     disabled forever.
   - Accept a second prop, `activeLeg?: "identify" | "generate" | "defend" |
     "improve" | null`, default `null`. When set, that leg's node and its
     incoming edge render in a visually "active" state (per this component's
     own judgment for what "active" means visually — e.g., a brighter border
     or a filled background instead of outline-only — but never a glow,
     never a blur, never a box-shadow beyond the standard token set). This
     prop is what Phase 9's live SSE-driven diagram will drive; Phase 3 does
     not wire it to anything live, but must build the visual "active" state
     and prove it works by toggling the prop manually in this phase's
     temporary showcase.
   - The one-time intro animation, exactly as specified in "The loop diagram
     (shared component...)" and its follow-on "Animation, plays once on
     mount" paragraph above: total 2.4s, nodes and edges light up in
     sequence (Identify → edge → Generate → edge → Improve → edge → Defend,
     with Defend deliberately landing last), then all four nodes settle into
     a slow, plain-opacity 4-second pulse in their own color — no other
     property animates in the settled state, specifically no scale, no
     blur, no glow. Build this with the Motion library (`framer-motion`
     package), and wrap the entire animated sequence in a check against
     `window.matchMedia("(prefers-reduced-motion: reduce)")` — when true,
     skip straight to the fully-settled final state with no animation at
     all, including skipping the ongoing 4s pulse (a reduced-motion user
     should see a static, correct diagram, not a slower version of the same
     motion).
   - Accept a third prop, `mode: "static" | "live"`, default `"static"`.
     `"static"` is the Home-page usage (light chrome background, the
     component renders directly on the page's normal background — it does
     NOT wrap itself in `.console`). `"live"` is the Loop-page usage — in
     `"live"` mode, this component's own root element applies the
     `.console` class from Appendix D, so the diagram renders on the dark
     "console" surface. This is the one and only place in the entire
     codebase, along with `ConversationTranscript` (built in Phase 7), that
     `.console` is ever applied — building this switch into the shared
     component itself, rather than having each page wrap it differently, is
     what keeps the "only two places ever use dark mode" rule enforceable
     from one file instead of trusted to page-level discipline.

2. `src/design-system/patterns/kpi-tile.tsx` (`KpiTile`) — large mono
   numeral (`--text-data-lg`) + label (`--text-caption`) + an optional delta
   chip (small, colored `--color-risk-low` for a positive/improving delta,
   `--color-risk-high` for a negative/regressing one — pick the sign
   convention per the specific metric, e.g. for PR-AUC and recall, up is
   good; for false-negative count, down is good — don't hardcode "up is
   always green," accept an explicit `direction: "up-is-good" |
   "down-is-good"` prop instead), with `CountUp` (below) built in as the
   default way the numeral appears.

3. `src/design-system/patterns/count-up.tsx` (`CountUp`) — animates a number
   from 0 to its target value over 1.2s on first viewport entry (use an
   `IntersectionObserver`, not a scroll listener), respects
   `prefers-reduced-motion` by rendering the final value immediately with no
   animation. Takes `value: number`, optional `format?: (n: number) =>
   string` for currency/percentage formatting (consume `lib/format.ts`'s
   helpers once Phase 4 creates them — for this phase, accept the prop as an
   interface even though nothing calls it with a real formatter yet).

4. `src/design-system/patterns/risk-badge.tsx` (`RiskBadge`) — wraps the
   Phase-2 `Badge`. Takes a `score: number` (0–100), internally resolves it
   to the correct risk tier using the exact boundaries implied by Appendix
   D's five-tier risk-color naming (critical/high/medium/low/minimal — pick
   sensible, evenly-reasoned score cutoffs, e.g. critical ≥ 90, high 70–89,
   medium 40–69, low 10–39, minimal 0–9, matching the same cutoffs used in
   `docs/DESIGN_SYSTEM.md`'s own risk table, which independently converged
   on the same five-tier boundaries — a second source agreeing is a good
   sign these cutoffs are reasonable, use them), and renders the
   correctly-colored `Badge` with BOTH the numeric score and the tier name
   as its label text (e.g. "87 · Critical") — never color or number alone.

5. `src/design-system/patterns/status-pill.tsx` (`StatusPill`) — a small
   colored dot (green `--color-risk-low` for online/healthy, gray
   `--color-fg-muted` for offline/unknown) plus short text, e.g. "● Online ·
   1.06M tx" — takes the dot color and the text as separate props, doesn't
   hardcode the copy, since the global nav (Phase 5) and potentially other
   contexts will supply different text with the same visual component.

6. `src/design-system/patterns/filter-bar.tsx` (`FilterBar`) — a row of
   toggle chips (built from `Badge` in a `role="button"`/toggle-pressed
   pattern, not a new primitive) plus a search `Input`, fully controlled
   from outside (accepts `chips: {id, label, active}[]`, `onChipToggle`,
   `searchValue`, `onSearchChange` — no internal state beyond what's needed
   for its own rendering).

7. `src/design-system/patterns/empty-state.tsx` (`EmptyState`) — an icon
   (from `icons.ts`, extend it now if needed) + one-line message + an
   optional action button, per the exact three copy strings already
   specified in "Empty, Loading, and Error States" above (build the
   component generically with `icon`, `message`, `action?` props — do not
   hardcode any of the three specific copy strings into this component
   itself; the pages that use it in Phases 6/7/9 supply their own copy).

8. `src/design-system/patterns/per-fraud-type-table.tsx`
   (`PerFraudTypeTable`) — THIS BELONGS HERE, NOT IN `features/defend/` OR
   `features/home/`, because both the Home page (Phase 5) and the Defend
   page (Phase 8) need it identically — this is the exact case "Folder &
   File Structure"'s rule 3 calls out for promotion to a shared pattern
   rather than "Home's copy of Defend's table." Columns: fraud_type
   (mono), count, precision, recall, pr_auc, fpr — one row per fraud type,
   each numeric cell in `--text-data`, plus a micro-bar (a simple inline
   `<div>` with `width: {value/max * 100}%` and a background color from
   `--chart-1`, no chart library needed for something this simple) showing
   the value relative to that column's max across all rows. Accepts
   `rows: EvalPerClassRow[]` as its only required prop (the type comes from
   Appendix E, built in Phase 4 — for this phase, define the shape inline
   as a local interface if Phase 4 hasn't landed yet, and note in
   `PROGRESS.md` that Phase 4 should replace it with the shared
   `lib/api/types.ts` import once that file exists).

DO NOT, IN THIS PHASE:
- Wire the loop diagram, `CountUp`, or anything else to real or demo data.
  Every pattern in this phase takes props and renders; data-fetching hooks
  are Phase 4's and each feature's own `use-*.ts` files' job.
- Add any additional visual flourish to the loop diagram beyond exactly
  what's specified: no particle effects, no glow on the "active" state, no
  gradient fills, no drop-shadow on the nodes beyond the standard
  `--shadow-sm` token if you use one at all (a flat, borderless node is
  equally acceptable and arguably more in keeping with "sharp = technical"
  restraint).
- Build a fifth or sixth pattern not listed above "because it seems useful."
  If a later phase needs something not on this list, that phase's own
  prompt will say so.

ACCEPTANCE CRITERIA:
[ ] The loop diagram renders correctly in both `mode="static"` (light
    background, no `.console`) and `mode="live"` (wrapped in `.console`,
    dark background) — verify both in this phase's temporary showcase.
[ ] The intro animation plays exactly once on mount, takes ~2.4s total, and
    the sequence order matches "Identify → edge → Generate → edge → Improve
    → edge → Defend" exactly, with Defend visibly landing last.
[ ] With `prefers-reduced-motion: reduce` simulated (via browser dev tools'
    emulation, not by physically changing OS settings), the diagram renders
    immediately in its fully-settled state with zero animation, including no
    ongoing pulse.
[ ] Toggling the `activeLeg` prop manually in the showcase visibly changes
    exactly one node/edge's appearance, with no effect on the others.
[ ] `CountUp` animates only when its element enters the viewport (test by
    placing it below an intentionally-tall spacer in the showcase and
    scrolling to it) and respects reduced motion.
[ ] `RiskBadge` renders the correct tier name and color for at least one
    score in every one of the five tiers — test all five explicitly in the
    showcase, don't assume the boundary math is right without checking a
    boundary value itself (e.g., score exactly 90, exactly 70, exactly 40,
    exactly 10).
[ ] `PerFraudTypeTable` renders correctly with exactly 7 rows of
    representative (not necessarily final/real) data in the showcase, each
    micro-bar's width visibly proportional to its column's max.
[ ] No new color, spacing, or motion-timing value exists in any file from
    this phase that isn't already a token from Appendix D.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — this is the highest-
risk phase in the build, so be unusually specific here: note exactly which
part of the loop-diagram animation you found ambiguous (if any) and what
you decided, since that is the single most likely place a later reviewer
will want to double-check your interpretation against the spec.
---

# Phase 4 — lib/: API Client, Store, Demo Data

Phase 4 — lib/: API Client, Store, Demo Data

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–3
should be DONE: scaffold, tokens, primitives, and patterns (including the
loop diagram) all exist and render correctly in temporary showcases.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). This phase builds the
architectural seam that makes "the frontend is never blocked on the
backend" literally true: a single API client interface with two
interchangeable implementations (real HTTP, local demo fixtures), a small
shared state store, and the demo fixture data itself — hand-built from this
document's own "The Real Numbers This Document Treats as Ground Truth"
table, not invented. Every page built in Phases 5 through 9 will consume
this layer exclusively; none of them will ever import `http-client.ts` or
`demo-client.ts` directly.

BUILD, IN THIS ORDER:

1. `src/lib/api/types.ts` — every request/response shape from "The API
   Contract" above, hand-typed as TypeScript interfaces. Use Appendix E
   ("Full TypeScript Type Definitions") below as the literal source — copy
   it in rather than re-deriving it, for the same "don't re-derive what's
   already correctly derived" reasoning "The API Contract" section gives for
   itself relative to prior research.

2. `src/lib/api/client.ts` — the `AflApiClient` interface, copied verbatim
   from "The API client interface — the seam that makes 'flexible' real"
   above. This file contains ONLY the interface definition (plus a
   `getApiClient(): AflApiClient` factory function, described in step 5
   below) — no implementation logic lives here.

3. `src/lib/api/http-client.ts` — the real implementation. Every method
   makes a `fetch()` call to `${import.meta.env.VITE_API_BASE_URL}/api/...`
   matching "The API Contract" exactly (method, path, body shape). For
   `runLoop`, use a native `EventSource` (or `fetch` + a manual
   `ReadableStream` reader if you need to send a POST body, since
   `EventSource` itself only supports GET — check which the actual
   `/api/loop/run` contract requires, and if it's a POST-with-SSE-response,
   implement it via `fetch` with `response.body.getReader()` parsing
   `data: ...` lines yourself, which is a well-known, small amount of code —
   do not add a new npm dependency for this, per "Live progress streaming"
   in "Technology Stack Decision" explicitly choosing "no dependency
   required"). Every method should surface a clear, typed error on failure
   rather than swallowing it — Phase 5 onward will decide what to *do* with
   that error (the Toast-and-fallback-to-demo pattern from "Empty, Loading,
   and Error States"), but this file's job is just to fail loudly and
   correctly, not to handle the fallback itself.

4. `src/lib/api/demo-client.ts` — the fixture implementation. Every method
   reads from the corresponding JSON file in `src/lib/demo-data/` (built in
   step 6 below) and returns a `Promise` that resolves after a small,
   realistic artificial delay (150–400ms, randomized per call, via
   `setTimeout` wrapped in a `Promise`) — a demo that resolves in 0ms reads
   as obviously fake the moment a judge notices every single loading
   skeleton flashes for exactly one frame; a small delay is honest cosmetic
   realism, not deception, since the real API will have comparable latency
   anyway. For `runLoop`, simulate the SSE stream with a `setInterval` that
   emits a plausible sequence of `cycle_start`/`miss_added`/`metric_update`/
   `cycle_end` events over roughly 3–5 seconds per cycle (matching the real
   contract's "each cycle takes roughly 30–60 seconds" note only
   approximately — a demo mode that makes a judge wait a literal 30–60
   real seconds per cycle is worse than a compressed, clearly-labeled-as-
   demo faster version; do not compress it so much it feels instant, since
   part of what sells "this is really running a cycle" is that it visibly
   takes some non-trivial time).

5. Back in `src/lib/api/client.ts`, add the `getApiClient()` factory:
   ```ts
   import { useAppStore } from "../store";
   import { httpClient } from "./http-client";
   import { demoClient } from "./demo-client";

   export function getApiClient(): AflApiClient {
     return useAppStore.getState().dataSource === "demo" ? demoClient : httpClient;
   }
   ```
   (Adjust exact syntax to however you've structured the store's exports in
   step 7 below — the point is this one function is the only place in the
   codebase that ever chooses between the two implementations. No feature
   component or hook ever imports `http-client.ts` or `demo-client.ts`
   directly — only `getApiClient()`, from `client.ts`.)

6. Build all five files under `src/lib/demo-data/`, using Appendix F ("Demo
   Data Fixture Specifications") below as your literal source for every
   number. These are not placeholder mockups — copy the real numbers from
   "The Real Numbers This Document Treats as Ground Truth" above (also
   reproduced in Appendix F for convenience) exactly, and where a fixture
   needs a number this document's ground-truth table doesn't have (e.g., a
   plausible-but-not-independently-sourced per-fraud-type precision value
   for `eval-per-class.json`'s seven rows), derive it so that it is
   internally consistent with the real aggregate figures that ARE given
   (e.g., the seven rows' counts should sum sensibly against the known
   total fraud count, and no single row's PR-AUC should be implausibly
   higher than the known overall test PR-AUC of 0.7971 unless a specific
   real number already says otherwise, as it does for `bustout_identity`
   and `ai_impersonation` per "The Real Numbers" table) — never invent a
   round, suspiciously-clean number anywhere:
   - `attacks.json` — this one is NOT invented at all: copy
     `src/identify/attacks.json` (created in Phase 0, step 4c) byte-for-byte
     into this location. Two files with identical content, in two different
     places, sounds like duplication, but it is the correct, deliberate kind
     — one is the backend's own source of truth it reads from at runtime,
     the other is the frontend's offline fixture for demo mode, and they
     must never be allowed to silently diverge, which is why this step says
     "copy," not "recreate independently." If you have the ability to
     generate the frontend copy from the backend file at build time (e.g., a
     small script, or a Vite plugin) rather than a manual copy-paste, that
     is a nice-to-have improvement — but a manual copy that stays correct
     today is better than a build step you don't have time to get right in
     a 3-day build. Note whichever approach you took in `PROGRESS.md`.
   - `eval-per-class.json`, `pr-curve.json`, `loop-history.json`,
     `system-status.json` — build per Appendix F's exact structure and
     value guidance.

7. `src/lib/store.ts` — the one Zustand store, copied verbatim from "The one
   Zustand store" code block under "State & Data Layer" above. Do not add
   any field beyond the three listed there
   (`commandPaletteOpen`/`setCommandPaletteOpen`,
   `dataSource`/`setDataSource`, `lastGeneratedTransactionId`/
   `setLastGeneratedTransactionId`) — if a later phase seems to need a
   fourth, re-read "If you find yourself wanting to add a fifth field..."
   immediately below that code block in this document; the answer is almost
   always "put it in that feature's own local state instead."

8. `src/lib/use-event-stream.ts` — a small shared hook wrapping the SSE
   consumption pattern, since both Generate (Phase 7) and Loop (Phase 9)
   need to consume a stream of typed events and expose them to a React
   component as state. Shape: `useEventStream<T>(subscribe: (onEvent: (e:
   T) => void) => (() => void)): { events: T[]; isStreaming: boolean }` (or
   an equivalent shape you find cleaner — the point is one hook, reused by
   both features, not two near-identical copies).

9. `src/lib/format.ts` — number/currency/date formatting helpers used
   throughout: a currency formatter (INR or USD — check which the rest of
   the project's numbers imply; the prize amounts in the hackathon brief are
   INR-denominated but transaction amounts in the dataset are unlabeled —
   default to a generic `$` USD-style format for transaction amounts unless
   you find explicit evidence otherwise in the source data, and note this
   assumption in `PROGRESS.md`), a percentage formatter (for PR-AUC,
   precision, recall — e.g., `0.7971` → `"79.71%"` or `"0.797"`, pick one
   convention and use it everywhere, don't mix "79.71%" in one component and
   "0.797" in another), and a relative/short date-time formatter (via
   `date-fns`/`date-fns-tz`) for the Loop run-history table.

10. `src/lib/constants.ts` — a small file mirroring `FEATURE_COLS` (for any
    frontend code that needs to know the model's feature names, e.g. the
    Defend page's transaction builder form, built in Phase 8 — see Appendix
    B for the authoritative list to mirror), the four loop-leg names and
    their token-variable names (for any component that needs to map a
    string like `"identify"` to `var(--color-loop-identify)`
    programmatically rather than via a static class), and the five route
    paths (`/`, `/identify`, `/generate`, `/defend`, `/loop`) as named
    constants rather than string literals scattered across `App.tsx` and
    the nav — this is a small thing but it's exactly the kind of "seam in
    the right place" that makes adding a sixth route later a one-line
    change instead of a grep-and-replace.

DO NOT, IN THIS PHASE:
- Build any UI component. This phase is pure data/state/plumbing — nothing
  in it renders anything.
- Wire any feature page to this layer. That happens starting in Phase 5.
- Add authentication, request retries beyond what TanStack Query gives you
  for free once it's wired in Phase 5, or any caching logic beyond TanStack
  Query's own defaults.
- Invent a demo-data number that isn't traceable to "The Real Numbers" table
  or a documented, reasoned derivation from it (see step 6's guidance on
  deriving internally-consistent per-fraud-type numbers) — this is checked
  explicitly in acceptance criteria below, line by line.

ACCEPTANCE CRITERIA:
[ ] `src/lib/api/types.ts` covers every request/response shape in "The API
    Contract" — cross-check against Appendix C, not from memory.
[ ] `getApiClient()` returns `demoClient` when `useAppStore.getState().
    dataSource === "demo"` and `httpClient` otherwise — verify by toggling
    the store value in a scratch console call and confirming the returned
    object's identity changes.
[ ] Every number in every file under `src/lib/demo-data/` is checked,
    line by line, against Appendix F / "The Real Numbers" table — for any
    number that is a derived (not directly sourced) figure, confirm it
    doesn't contradict a real, sourced figure elsewhere in the same fixture
    set (e.g., the sum of per-fraud-type counts in `eval-per-class.json`
    should be consistent with the known total fraud counts).
[ ] `attacks.json` in `lib/demo-data/` is byte-for-byte identical to
    `src/identify/attacks.json` from Phase 0.
[ ] The simulated SSE stream in `demo-client.ts`'s `runLoop` emits events in
    a plausible order (`cycle_start` before any `metric_update` for that
    cycle, `cycle_end` after) and calls its `onEvent` callback with typed,
    `LoopEvent`-shaped objects matching Appendix E.
[ ] `useAppStore` contains exactly the three fields specified — no more.
[ ] No file in `src/lib/` imports anything from `src/features/`,
    `src/chrome/`, or `src/design-system/` (the dependency graph flows one
    way — `lib/` sits at the bottom alongside `design-system/`, and neither
    imports "up" toward features or chrome).

BEFORE YOU FINISH: append your `PROGRESS.md` entry — be specific about which
demo-data numbers were directly sourced vs. derived, since Phase 5 onward
will be displaying these numbers on screen and whoever reviews the finished
app against "The Real Numbers" table needs to know which figures to
double-check.
---

# Phase 5 — Chrome, Routing, and the Home Page

Phase 5 — Chrome, Routing, and the Home Page

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–4
should be DONE: scaffold, tokens, primitives, patterns (loop diagram, KPI
tile, risk badge, etc.), and the full `lib/` layer (API client, store, demo
data) all exist. This is the first phase where things actually start
looking like the finished product, and the first real "does this look
right" checkpoint — if you have access to a Playwright MCP tool or any
other screenshot capability, use it to review your own output before
declaring this phase done, per this document's own suggested-model-tier
table pairing this phase with exactly that kind of self-review.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL) — re-read "Home Page
Specification" and "Global Chrome" (both under "Part IV — Information
Architecture and Page Specifications") in full before starting; this phase
prompt summarizes them but the full prose sections above contain detail
(exact copy, exact layout proportions) worth having open while you work
rather than relying on this condensed version alone.

BUILD, IN THIS ORDER:

1. DELETE any temporary verification/showcase code left in `src/App.tsx` by
   Phase 1 and/or Phase 2 (check `PROGRESS.md` for what to look for) — this
   phase replaces `App.tsx` entirely with real routing.

2. `src/main.tsx` — wire up `QueryClientProvider` (TanStack Query) wrapping
   the whole app. Reasonable defaults: `staleTime` around 30s for most
   queries (per-endpoint overrides can come later if a specific page needs
   different behavior — none currently do).

3. `src/App.tsx` — router only, no page content, per "Folder & File
   Structure"'s explicit note on this file's job. Five `React.lazy`-loaded
   routes (`/`, `/identify`, `/generate`, `/defend`, `/loop`), using the
   route-path constants from `lib/constants.ts` (Phase 4) rather than
   re-typing the strings. Wrap the routed content in the chrome (top nav +
   footer, built in step 4) so it persists across route changes rather than
   being re-rendered by each page.

4. `src/chrome/top-nav.tsx`, `src/chrome/footer.tsx`,
   `src/chrome/command-palette.tsx`, `src/chrome/system-status-pill.tsx` —
   build exactly per "Global Chrome" above:
   - Top nav: sticky, 56px, wordmark left (text "AFL" in accent color +
     "Adversarial Fraud Lab" in `--color-fg-primary`, both in
     `--text-section-title` weight 700 — re-read the exact spec, this
     summary compresses it), five nav items center-left with the active-
     route underline treatment, `StatusPill` + "Run the loop" button right.
     The "Run the loop" button navigates to `/loop` with its controls
     pre-filled for a 1-cycle run — implement this via a route search param
     (e.g. `/loop?prefill=1cycle`) that the Loop page (Phase 9) reads, not
     via the Zustand store, consistent with this document's own guidance
     elsewhere that one-time navigation hints belong in the URL, not
     cross-cutting state.
   - Footer: three columns exactly as specified, with the "Methodology"
     link doing an in-page scroll to the Home page's "Numbers that hold up"
     section (use a hash anchor, `#numbers-that-hold-up`, and
     `scrollIntoView` — if the footer is visible on a page other than Home
     when this link is clicked, navigate to `/#numbers-that-hold-up` first).
   - Command palette: `Dialog` (Phase 2) + `cmdk`, opened via `Cmd/Ctrl+K`
     (wire a global keydown listener, scoped so it doesn't fire while
     focus is inside a text input already capturing that combination) and
     via `useAppStore`'s `commandPaletteOpen` state (so the "Run the loop"
     button or any other future trigger could also open it, though none
     currently need to). Three groups exactly as specified: "Go to page,"
     "Attacks" (fuzzy search over the 25 taxonomy entries — fetch them via
     `getApiClient().getAttacks()`, cached by TanStack Query so opening the
     palette repeatedly doesn't refetch), "Actions" (the three named
     actions — "Run the loop," "Generate a random attack," "Predict a
     random transaction" — each navigates to the relevant page with
     appropriate pre-fill via search params).
   - `StatusPill`: pull live data from `getApiClient().getSystemStatus()`
     via a TanStack Query hook, rendering "● Online · {n_transactions}
     tx" formatted via `lib/format.ts`.

5. `src/features/home/` — build all five files:
   - `home-page.tsx` — composes everything below in the exact vertical
     order specified in "Home Page Specification."
   - Hero section (inline in `home-page.tsx` or its own small component,
     your choice): left-aligned headline exactly as specified ("The AI that
     learns fraud by *becoming* a fraudster," with "becoming" in accent
     color), sub-headline, two buttons, and the `LoopDiagram` pattern
     component from Phase 3 rendered in `mode="static"` on the right ~55%
     of the hero.
   - `hero-kpi-row.tsx` — four `KpiTile`s (Phase 3) in a row: transaction
     count, attack count, fraud rate (all three are static, known real
     numbers — pull them from `getSystemStatus()` rather than hardcoding,
     since that endpoint's contract already includes `n_transactions` and
     `fraud_rate`), and the fourth tile's PR-AUC value pulled live from
     `getApiClient().getEvalPerClass()` (aggregate or from
     `getPrCurve()`'s `operating_point`, whichever the real contract makes
     cleaner — never hardcode this number, per "A number you should
     reconcile before it goes on a UI screen" above; this is the exact
     number this document explicitly refuses to pick a side on).
   - "The closed loop, in four stages" — four cards, asymmetric widths per
     spec (two "strongest demo" cards at 1.25× width — use Defend and Loop
     as the two wider ones, per this document's own note that they're the
     strongest per the repo audit), each with a 4px top border in its leg
     color, icon, name, one sentence, "Try it →" link.
   - `pillar-preview-cards.tsx` — "Built on real attacks," three working
     miniatures: Identify (five most severe attacks — sort the 25 by
     feasibility descending and take the top five, or by a defined
     "severity" you derive consistently — document whichever you choose),
     Generate (a collapsed version of the Generate page's control panel —
     it is fine and expected for this to share the actual
     `GenerateControls` component once Phase 7 exists; if Phase 7 hasn't
     run yet when you build this, build a clearly-marked placeholder and
     leave a `// TODO(Phase 7): replace with <GenerateControls compact />`
     comment, and note this explicitly in `PROGRESS.md` as a
     cross-phase dependency for whoever runs Phase 7 to close the loop on),
     Defend (same pattern — collapsed `TransactionBuilderForm` to three
     fields, TODO-linked to Phase 8 if it hasn't run yet).
   - `numbers-that-hold-up.tsx` — the shared `PerFraudTypeTable` pattern
     (Phase 3) fed from `getApiClient().getEvalPerClass()`, with an `id`
     attribute (`id="numbers-that-hold-up"`) matching the footer's
     Methodology anchor link from step 4.
   - The "loop in motion" narrative block — plain text and numbers, not an
     illustration, using the exact feedback-loop figures from "The Real
     Numbers" table (val recall 0.8200 → 0.8467, FN 34 → 32) — these are
     static historical facts about a specific past run, not a live query,
     so it is correct for this one section (and only this one) to present
     them as fixed prose/numbers rather than wiring them to an endpoint.

DO NOT, IN THIS PHASE:
- Build the Identify, Generate, Defend, or Loop pages themselves (only the
  Home page's miniature/preview versions of their controls, per step 5's
  `pillar-preview-cards.tsx` guidance, with TODO comments where a full page
  doesn't exist yet).
- Give the four "closed loop" stage cards equal width — re-read anti-pattern
  #10 in "The Anti-'AI-Generic' Checklist" above; equal-width cards in a
  perfectly even grid is exactly the tell this document forbids.
- Add a sidebar, a mega-menu, or any nav pattern beyond the specified five
  flat top-nav items.
- Skip the `prefers-reduced-motion` check on the loop diagram or `CountUp`
  usages on this page — they were built correctly in Phase 3; this phase
  just needs to not break that by, e.g., wrapping them in something that
  interferes with the `IntersectionObserver` or the media-query check.

ACCEPTANCE CRITERIA:
[ ] `npm run dev` and navigate to `/` — the full Home page renders top to
    bottom exactly matching the six sections in "Home Page Specification"'s
    order, with zero console errors.
[ ] All five nav routes are reachable and each lazy-loads only its own
    page's JS (verify in the Network tab — clicking "Identify" should not
    trigger a request for Generate/Defend/Loop's bundle before those pages
    exist, and once they do exist in later phases, this should remain true).
[ ] `Cmd/Ctrl+K` opens the command palette from any page; fuzzy-searching an
    attack name jumps to `/identify` (even if that page is just a
    placeholder until Phase 6 runs) with the correct search param set.
[ ] The four "closed loop" cards are visibly, deliberately unequal in width
    (1.25× vs. 1×), not a coincidental rendering artifact — inspect the
    actual computed widths.
[ ] The fourth KPI tile's PR-AUC number matches whatever `demo-client.ts`'s
    fixture currently returns (not a hardcoded value found anywhere in this
    phase's own new code — grep your own new files for the literal strings
    "0.7971" or "0.8073" or "96.3" and confirm none of them appear outside
    of comments).
[ ] The Home page's loop diagram plays its intro animation once, in
    `mode="static"`, matching Phase 3's build exactly (no visual difference
    introduced by however you're passing props to it here).
[ ] Footer's "Methodology" link scrolls to the "Numbers that hold up"
    section from any page, including pages other than Home.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — explicitly flag any
TODO(Phase 7)/TODO(Phase 8) placeholders you left in
`pillar-preview-cards.tsx`, since those are real, load-bearing cross-phase
dependencies that Phase 7 and Phase 8 must each check for and close out
when they run, not just "nice to eventually fix" comments.
---

# Phase 6 — Identify Page

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–5
should be DONE: scaffold, tokens, primitives, patterns, `lib/`, chrome,
routing, and the Home page all exist and work. This phase does NOT depend
on Phases 7, 8, or 9 — if `PROGRESS.md` shows any of those as also DONE or
IN PROGRESS, that's fine and expected (per "Phase Sequencing" above, these
four pages are independent leaves on the dependency tree and may run in any
order, including in parallel across different sessions/models). Check
specifically whether Phase 5 left a `TODO(Phase 7)` comment referencing
this page — it shouldn't have (that TODO would reference Phase 7/8, not
this one), but if `home-page.tsx`'s Identify miniature is still a
placeholder, that's Phase 5's leftover concern, not something this phase
needs to fix; this phase only owns `/identify` itself.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). This page answers two of the
five judging axes: diversity (how many distinct attacks were catalogued)
and novelty (the AI-specific category, D, is this project's named
differentiator). Re-read "Identify Page Specification" above in full before
starting.

YOUR TASK — build everything under `src/features/identify/`:

1. `use-attacks.ts` — a TanStack Query hook, `useAttacks()`, calling
   `getApiClient().getAttacks()`. This is the ONLY file in this feature
   folder that imports from `lib/api/`.

2. `attack-filter-bar.tsx` — composes the shared `FilterBar` pattern (Phase
   3) with this page's specific filter state: five category chips (A
   through E), colored per "Identify Page Specification"'s explicit
   instruction — each chip's color is the *loop leg* color of whichever
   pillar that category is closest to (use your own reasoned mapping,
   documented in `PROGRESS.md` — e.g., category A "AI-Generated Social
   Engineering" and category E "Behavioral Manipulation" both feed the
   Generate pillar's simulation work, so both could reasonably take
   `--color-loop-generate`; category D "AI-Specific Attacks" is this
   project's own novel-detection differentiator and could reasonably take
   `--color-loop-defend` or `--color-loop-identify` — there is a genuine,
   acknowledged judgment call here, since the spec asks for a *reasoned*
   mapping rather than five arbitrary category colors, not a single
   uniquely correct answer; make a defensible choice and write down your
   reasoning, don't leave it undocumented), a status filter (All /
   Implemented / Partial / Conceptual), and a search input filtering by
   name.

3. `attack-list.tsx` — the `Table` primitive (Phase 2) bound to
   `@tanstack/react-table`, NOT virtualized (25 rows — re-read "Performance &
   Scalability Guidelines" above on exactly why virtualization here would be
   wrong, not just unnecessary). Columns: ID (`--text-data` mono), Name,
   Category (a colored chip using the same mapping from step 2), Feasibility
   (filled dots 1–3 — wait, re-check: Appendix A's feasibility scale is 1–5
   stars in the source taxonomy doc but this page spec describes "1–3" filled
   dots — resolve this discrepancy by using whatever scale
   `src/identify/attacks.json`'s `feasibility` field actually contains, per
   Phase 0's own unification work, and render that many filled dots out of
   that scale's max, with the numeric/star rating always available as a
   tooltip or hover label per "never dots alone" — note in `PROGRESS.md` which
   scale you ended up rendering, since this prompt just caught a real, small
   inconsistency between two parts of this document's own drafting history
   worth flagging rather than silently picking one), Status (badge), and a
   trailing chevron opening the detail drawer.

4. `attack-detail-drawer.tsx` — the `Sheet` primitive (Phase 2), full
   description, feasibility rationale (if `attacks.json` has one — if the
   unified file from Phase 0 didn't carry a rationale field over from the
   prose in `docs/ATTACK_TAXONOMY.md`, render what's available rather than
   fabricating a rationale that wasn't in the source), and — only when
   `generator_profile_id` is non-null on that attack (exactly the four:
   SE-001, KYC-002, PR-003, AI-004, per Phase 0's unification work) — a
   "Generate a sample →" button navigating to `/generate?attack_id={id}`
   (a route search param, not the Zustand store, per the page spec's
   explicit reasoning that this is a one-time navigation hint).

5. `identify-page.tsx` — composes the header strip (exact copy from the
   spec: "Attack Taxonomy" / "25 attack vectors across 5 categories..."),
   the filter bar, the list, and the drawer (open/closed state can be local
   `useState` in this top-level page component, passed down — this is
   exactly the kind of single-feature-local state that does NOT belong in
   the shared Zustand store, per "State & Data Layer"'s own guidance).
   Category D's filter chip renders visually first in the filter row, per
   the spec's explicit instruction that a judge scanning for novelty should
   find it in the first five seconds.

6. Read the URL's `?attack_id=` search param (relevant when arriving from
   the Home page's mini-preview or the command palette's fuzzy search) and,
   if present, open the drawer for that attack automatically on mount.

7. Wire the EmptyState pattern (Phase 3) for the "no attacks match these
   filters" case, exact copy from "Empty, Loading, and Error States" above.

8. Wire the `Skeleton` pattern for the loading state — a skeleton table
   matching the real table's row shape, not a generic spinner or blank
   screen, while `useAttacks()` is loading.

9. Close out Phase 5's `pillar-preview-cards.tsx` TODO, if it references
   this page (it shouldn't — re-read: Phase 5's TODOs were for Generate and
   Defend's miniatures, not Identify's, since Identify's miniature is "five
   most severe attacks," which Phase 5 could and should have built directly
   from `useAttacks()` without needing this page's own components to exist
   first). If you find a TODO in `pillar-preview-cards.tsx` that does
   reference Identify for some reason, resolve it and note the correction
   in `PROGRESS.md`.

DO NOT, IN THIS PHASE:
- Import anything from `src/features/generate/`, `src/features/defend/`, or
  `src/features/loop/` — even though the drawer's "Generate a sample" button
  conceptually connects to Generate, it connects via a URL search param,
  never a direct import.
- Hardcode the 25 attacks, their categories, or any of their metadata
  anywhere in this feature folder. Every attack-list component maps over
  whatever `useAttacks()` returns — this is explicitly checked in Phase 10's
  QA pass via a "does the list still work if we add a 26th attack to the
  fixture" test, so build it that way now rather than retrofitting later.
- Virtualize the list.

ACCEPTANCE CRITERIA:
[ ] `/identify` renders all (up to) 25 attacks from whichever data source
    (`demo` or `live`) is active, with zero hardcoded attack data anywhere
    in this feature folder's own source files (grep for any of the 25
    attack names or IDs inside `src/features/identify/` — the only place
    they should appear is inside `lib/demo-data/attacks.json`, which lives
    outside this feature folder).
[ ] Filtering by any one category chip shows only that category's rows;
    combining a category filter with the search input further narrows
    correctly; clearing all filters restores all rows.
[ ] Category D's chip is the leftmost/first chip in the filter row.
[ ] Clicking a row's chevron opens the drawer with that row's full detail;
    exactly the four attacks with a wired generator profile show the
    "Generate a sample →" button, and clicking it navigates to
    `/generate?attack_id=...` with the correct ID.
[ ] Arriving at `/identify?attack_id=SE-001` directly opens that attack's
    drawer automatically on page load.
[ ] Filtering to a combination that matches zero attacks shows the
    `EmptyState` with a working "Clear filters" action.
[ ] Temporarily adding a 26th fake entry to the demo fixture's
    `attacks.json` (a scratch test you undo before finishing) causes the
    list, filters, and drawer to all correctly reflect 26 items with zero
    code changes anywhere in this feature folder — this is the concrete
    proof of "Performance & Scalability Guidelines"'s scaling claim; if this
    fails, something in this phase is hardcoding a length-25 assumption and
    must be fixed before moving on.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — document your category-
to-loop-leg color mapping reasoning from step 2, and the feasibility-scale
resolution from step 3, since both were genuine judgment calls this prompt
flagged rather than fully resolving for you.

---

# Phase 7 — Generate Page

Phase 7 — Generate Page

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–5
should be DONE. This phase does not depend on Phases 6, 8, or 9 and may run
before, after, or in parallel with any of them. Check `PROGRESS.md`
specifically for a `TODO(Phase 7)` comment left inside
`src/features/home/pillar-preview-cards.tsx` by Phase 5 — closing that out
is part of this phase's job (see step 6 below).

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). This page answers "fidelity"
and "novelty," and is explicitly called out in "Generate Page Specification"
above as "the single most differentiated piece of engineering in the whole
repo" — the LLM writes a fraud *narrative*, a judge model validates it, and
the conversation is materialized into a transaction row. Re-read "Generate
Page Specification" in full before starting.

YOUR TASK — build everything under `src/features/generate/`:

1. `use-generate.ts` — a TanStack Query *mutation* hook (not a query — this
   is a user-triggered action, not passive data fetching), calling
   `getApiClient().generateAttack(req)`. Handle both response shapes the
   contract allows: a direct full payload, or an SSE stream (per "The API
   Contract"'s note that generation "streams as SSE if generation exceeds
   ~2s; otherwise returns the full payload directly") — use
   `lib/use-event-stream.ts` from Phase 4 for the streaming path, and
   present both paths to the UI through one consistent shape so
   `generate-page.tsx` doesn't need to know which one occurred.

2. `generate-controls.tsx` (`GenerateControls`) — react-hook-form + zod, per
   "Technology Stack Decision." Fields: attack type (`Select`, sourced from
   `useAttacks()` — yes, this feature imports the Identify feature's query
   hook's *shape*, but re-read "Folder & File Structure"'s rule 3 carefully:
   the rule forbids importing from a *sibling feature folder*. `useAttacks`
   is arguably borderline — the cleanest resolution, and the one this phase
   should take, is to NOT import `src/features/identify/use-attacks.ts`
   directly; instead, call `getApiClient().getAttacks()` again here, in this
   feature's own small local hook, even though the underlying data is the
   same. TanStack Query's cache will deduplicate the actual network/demo
   call if both hooks use the same query key — so there is no real
   performance cost to this, and it preserves the folder-independence
   invariant that makes it safe to delete or rebuild either feature without
   touching the other. Use the same query key string in both places (define
   it once in `lib/constants.ts` from Phase 4 and import it from there, not
   from each other) so TanStack Query's cache does the deduplication work
   for you), target user (`Select`: a handful of representative test-set
   user IDs, or "Random" — the demo fixture can supply a small fixed list),
   urgency (`Select`: low/medium/high, disabled/grayed — not hidden — for
   attack types where the underlying profile has no urgency parameter, per
   the spec's explicit "rather than silently ignored" instruction), and a
   `primary` "Generate →" `Button`.

   IMPORTANT: This component must also work in a `compact` prop mode (a
   smaller, Home-page-embeddable version with fewer visible fields, reusing
   the same underlying form logic) — this is exactly what Phase 5's
   `pillar-preview-cards.tsx` TODO was waiting for. Build the `compact`
   variant now, then go update `src/features/home/pillar-preview-cards.tsx`
   yourself, replacing its placeholder with `<GenerateControls compact />`,
   and remove the `TODO(Phase 7)` comment Phase 5 left there.

3. `conversation-transcript.tsx` (`ConversationTranscript`) — THE SECOND
   AND LAST PLACE `.console` IS USED IN THIS ENTIRE CODEBASE (the first is
   the Loop page's live diagram, built by Phase 3's shared component and
   consumed by Phase 9). Wrap this component's root in the `.console`
   class. Render each message bubble plainly (per the spec's explicit "no
   chat-app styling flourishes" instruction — no rounded speech-bubble
   tails, no avatar icons, no alternating left/right alignment unless that
   genuinely reflects two distinct parties in the transcript data itself),
   with a `Badge` "✓ validated" or "✗ rejected — leaked card data" at the
   end of the transcript, colored using the risk/status tokens (validated →
   `--color-risk-low`-family, rejected → `--color-risk-critical`-family, but
   remember `.console`'s own variable overrides apply here — re-check
   Appendix D's console-scoped variables rather than assuming the light-mode
   risk tokens apply unchanged inside `.console`).

4. `materialized-transaction.tsx` (`MaterializedTransaction`) — the
   resulting row, every field in `--text-data` mono, label/value grid.
   Per the spec's explicit instruction, this must use "identical visual
   treatment to what the Defend page shows for a prediction input" — since
   Phase 8 (Defend) may not have run yet when this phase runs, do not wait
   for it or attempt to import anything from it (folder-independence rule
   again). Instead, build this component's visual treatment directly from
   this document's own token/typography spec (label/value grid, mono for
   values) so that it is independently correct, and trust that Phase 8,
   when it runs, will independently arrive at the same visual treatment
   from the same spec — if Phase 10's QA pass finds the two don't actually
   match pixel-for-pixel, that's a legitimate QA finding to fix then, not
   something this phase should solve by reaching into Defend's folder.

5. `diff-against-normal.tsx` (`DiffAgainstNormal`) — a small two-column
   mini-table comparing `amount`, `channel`, `hour_of_day`, and
   `device_trust_age_days` (four specific fields, per the spec — not the
   full 23-feature set) against the same user's own median for each. The
   real API/demo fixture needs to supply this per-user median data
   alongside the generation result; if the current API contract or demo
   fixture doesn't yet carry it, add a `user_medians` field to
   `GenerateResult` in `lib/api/types.ts` (Appendix E) and to the demo
   fixture's generation-response shape, and note this addition explicitly
   in `PROGRESS.md` as a contract extension beyond what Appendix C
   originally specified, with your reasoning (the page spec requires this
   data to exist somewhere, and it wasn't explicitly in the original
   contract, which this document's own "don't assume anything as
   understood" principle means should be named, not silently patched).

6. `generate-page.tsx` — composes the header (exact copy from the spec),
   the 40/60 two-column workspace, calls
   `setLastGeneratedTransactionId(result.transaction.id)` (via the Zustand
   store from Phase 4) on successful generation, and implements the hard
   fallback: if the LLM path errors or times out, retry against the
   rule-based generator path and show the "Generated via rule-based
   fallback" `Badge` — never fail the demo silently, and never present a
   fallback result as if it came from the LLM path. Read `?attack_id=` from
   the URL (set by Identify's drawer, per Phase 6) and pre-select that
   attack type in `GenerateControls` on mount, if present.

7. Wire `EmptyState` for "before first run," `Skeleton` for the in-flight
   generation state (a skeleton matching the shape of the three output
   panels), per "Empty, Loading, and Error States."

DO NOT, IN THIS PHASE:
- Import anything from `src/features/identify/`, `src/features/defend/`, or
  `src/features/loop/` directly. Use the shared query-key-deduplication
  approach from step 2 for the attacks list; use route search params for
  cross-page hints; use the Zustand store for the one specific
  cross-cutting value it's designed for (`lastGeneratedTransactionId`).
- Apply `.console` anywhere in this feature folder except
  `ConversationTranscript`.
- Let a flaky LLM path visibly fail the demo — the fallback in step 6 is not
  optional polish, it is a hard requirement repeated in three different
  places across this document (page spec, this phase prompt, and
  implicitly in "Empty, Loading, and Error States").

ACCEPTANCE CRITERIA:
[ ] `/generate` renders the full two-column workspace; selecting an attack
    type, target user, and urgency, then clicking "Generate →," produces a
    populated transcript, materialized transaction, and diff panel within a
    few seconds in demo mode.
[ ] The urgency field is visibly disabled (not hidden) for at least one
    attack type whose underlying profile has no urgency parameter — verify
    against `src/identify/attacks.json`'s actual data, don't assume which
    ones qualify.
[ ] Simulating a generation failure (temporarily force `demo-client.ts`'s
    `generateAttack` to throw, as a scratch test you revert before
    finishing) triggers the rule-based-fallback path and shows the correct
    `Badge`, without a visible error state reaching the user.
[ ] After a successful generation, navigating to `/defend` — even as just
    Phase 5/8's current state, whatever exists — and checking
    `useAppStore.getState().lastGeneratedTransactionId` in a scratch console
    call confirms the ID was actually set.
[ ] `src/features/home/pillar-preview-cards.tsx`'s Generate miniature now
    renders the real `<GenerateControls compact />` with zero remaining
    `TODO(Phase 7)` comments anywhere in the codebase (grep to confirm).
[ ] `ConversationTranscript` visibly renders on a dark `.console` surface;
    every other component on this page renders on the normal light surface.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — explicitly document the
`user_medians` contract extension from step 5 if you added it, since this
is exactly the kind of "the frontend discovered the backend contract was
incomplete" finding that whoever owns the FastAPI implementation needs to
see and account for.
---

# Phase 8 — Defend Page

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–5
should be DONE. This phase does not depend on Phases 6, 7, or 9. Per
"Phase Sequencing" above, if the team is behind schedule, THIS is the phase
that should run immediately after Phase 5, ahead of Phases 6 and 7 — it is
simultaneously the highest-value page (judges spend the longest here) and the
lowest-risk to build (the most existing, working backend code sits behind it
already). Check `PROGRESS.md` for a `TODO(Phase 8)` comment left in
`src/features/home/pillar-preview-cards.tsx` by Phase 5 — closing it out is
part of this phase.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). This page answers
"detection efficacy" — the axis judges will scrutinize most carefully, since
it's the one with genuinely comparable, checkable numbers
(precision/recall/PR-AUC). Re-read "Defend Page Specification" above in full
before starting.

YOUR TASK — build everything under `src/features/defend/`:

1. `use-defend.ts` — TanStack Query hooks: a mutation for
   `getApiClient().predict(tx)`, and queries for `getEvalPerClass()` and
   `getPrCurve()`.

2. `transaction-builder-form.tsx` (`TransactionBuilderForm`) — react-hook-form
   + zod. Visible, editable fields: exactly the 7 named in the spec
   (`amount`, `hour_of_day`, `channel`, `new_device`, `tx_last_1hr`,
   `device_trust_age_days`, `count_30d`) — cross-check these names
   character-for-character against Appendix B's authoritative
   `FEATURE_COLS`/`CAT_COLS` list, since a typo'd field name here would
   silently fail to match the model's actual input schema. Every other
   field in `MODEL_COLS` (Appendix B has the full 23-field list) gets a
   sensible, VISIBLE default — per the spec's explicit "rather than being
   hidden" instruction, render the other 16 fields as a collapsed/
   secondary "Advanced fields (using dataset medians)" disclosure that's
   collapsed by default but inspectable, not literally absent from the DOM
   — a judge who's curious should be able to see the full 23-field payload
   this form actually sends, even though only 7 are front-and-center. Also
   render a "Load a transaction I just generated" link, visible ONLY when
   `useAppStore().lastGeneratedTransactionId` is set (from Phase 4's
   store) — clicking it should fetch that transaction's actual field values
   (from wherever Phase 7's generation result is retrievable — if there's
   no dedicated "get a past generated transaction by ID" endpoint in the
   current contract, this is a legitimate contract gap to flag in
   `PROGRESS.md`, the same way Phase 7 flagged `user_medians`; a reasonable
   interim solution is for Phase 7 to also stash the full generated
   transaction object, not just its ID, in a slightly extended store field
   — if you take this approach, extend `useAppStore` with exactly one more
   field, `lastGeneratedTransaction: TransactionRow | null`, and say
   explicitly in `PROGRESS.md` that you're doing this as a deliberate,
   reasoned exception to Phase 4's "don't add a fifth field" guidance,
   because this is precisely the "two pages don't import each other, they
   share state through the store" mechanism the folder rules exist to
   enable) and pre-fill the form.

3. `probability-gauge.tsx` (`ProbabilityGauge`) — custom SVG arc, 0–100,
   with a tick mark at the live operating threshold pulled from
   `getPrCurve()`'s `operating_point.threshold` (never hardcoded — this
   value should visibly move if the demo fixture's threshold value changes,
   proving it's wired live and not a fixed illustration).

4. `shap-waterfall.tsx` (`ShapWaterfall`) — horizontal bar chart via Recharts,
   signed contributions from the `predict()` response's `shap` array,
   colored by SIGN not by feature identity (positive-toward-fraud in
   `--color-risk-high`, negative in `--color-risk-low` — re-read the spec's
   explicit instruction on this; a chart that colors each bar by which
   feature it is, rather than which direction it pushes the prediction,
   would be a legible-but-wrong reading of "signed contributions").

5. `per-fraud-type-table.tsx` — do NOT build a new component here; import
   the shared `PerFraudTypeTable` pattern from `design-system/patterns/`
   (built in Phase 3, already consumed by Home in Phase 5) and feed it from
   this page's own `use-defend.ts` query. This is the exact case "Folder &
   File Structure"'s rule 3 names — the component itself lives in the
   shared layer, not duplicated here.

6. `confusion-heatmap.tsx` (`ConfusionHeatmap`) — small (240px), rows =
   fraud_type, columns = predicted label, cells colored on a scale from
   `--color-bg-muted` to `--color-risk-critical`, normalized per row, with
   the numeric count always printed in the cell text (never color alone,
   per Accessibility Standards).

7. `pr-curve-chart.tsx` (`PrCurveChart`) — Recharts, 400×300, from
   `getPrCurve()`, with the real operating point marked with a dot and a
   label showing its precision/recall/threshold values.

8. `defend-page.tsx` — composes the header (exact copy, including the real
   split sizes: "Trained on 745,474 transactions... validated on 106,496,
   tested on 212,993"), the live predictor as the page's hero section, then
   the per-fraud-type table, confusion heatmap, and PR curve below it in
   that order. Also update `src/features/home/pillar-preview-cards.tsx`'s
   Defend miniature, replacing its Phase-5 placeholder with a collapsed
   `<TransactionBuilderForm compact />` (build the `compact` variant on this
   form the same way Phase 7 built one for `GenerateControls` — three
   fields visible instead of seven), and remove the `TODO(Phase 8)` comment.

DO NOT, IN THIS PHASE:
- Import anything from `src/features/identify/`, `src/features/generate/`,
  or `src/features/loop/` directly.
- Re-derive or recompute the PR curve, per-class metrics, or SHAP values
  client-side — render exactly what the API/demo fixture returns, per
  "Performance & Scalability Guidelines"'s explicit "no client-side re-
  computation of anything the backend already computed" rule.
- Color the SHAP waterfall by feature identity instead of by sign.
- Hide the 16 non-primary `MODEL_COLS` fields entirely — they must be
  visible-on-demand, not absent.

ACCEPTANCE CRITERIA:
[ ] `/defend` renders the full page; filling the 7 visible fields and
    clicking "Predict →" returns a probability, a gauge reading, and a
    SHAP waterfall within a couple seconds in demo mode.
[ ] The "Advanced fields" disclosure, when expanded, shows all 23
    `MODEL_COLS` field names and their current (default or edited) values —
    cross-checked against Appendix B for completeness.
[ ] After generating a transaction on `/generate` (Phase 7) and returning to
    `/defend`, the "Load a transaction I just generated" link appears and
    correctly pre-fills the form with that transaction's real field values.
[ ] The `ProbabilityGauge`'s threshold tick mark moves if you temporarily
    edit the demo fixture's `operating_point.threshold` value (a scratch
    test you revert before finishing) — proving it's live-wired, not a
    static illustration.
[ ] `ShapWaterfall` bars are colored strictly by sign (positive vs.
    negative contribution), confirmed against at least one feature with a
    negative contribution in the demo fixture's data.
[ ] `ConfusionHeatmap` prints a numeric count in every cell, never relying
    on color alone.
[ ] `src/features/home/pillar-preview-cards.tsx`'s Defend miniature renders
    the real compact form, with zero remaining `TODO(Phase 8)` comments
    anywhere in the codebase.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — explicitly document
whether you extended `useAppStore` with `lastGeneratedTransaction` (step 2)
and why, since that's a deliberate, reasoned deviation from Phase 4's "don't
add a fifth field" default guidance and future phases/reviewers need to know
it happened and why it was justified here specifically.

---

# Phase 9 — Loop Page

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–5
should be DONE. This phase does not depend on Phases 6, 7, or 8. Per
"Judging Criteria Alignment Matrix" and "Submission Checklist" above,
this is the first page to cut if time runs out — but per "Phase Sequencing,"
that only applies as a last resort; build it properly if you have the time
this phase's slot implies you do.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). This page answers "novelty"
and "real-world feasibility," and is the destination of the global nav's
"Run the loop" button. It is also the second and last place `.console` is
used, and the second (and last) live consumer of the shared `LoopDiagram`
pattern from Phase 3 — this time in `mode="live"`, with real SSE events
driving its `activeLeg` prop. Re-read "Loop Page Specification" above in
full before starting.

YOUR TASK — build everything under `src/features/loop/`:

1. `use-loop.ts` — a query hook for `getApiClient().getLoopHistory()`, and a
   hook wrapping `getApiClient().runLoop(req, onEvent)` via
   `lib/use-event-stream.ts` (Phase 4) — remember `runLoop`'s signature
   returns an unsubscribe function directly, not a Promise, per "The API
   client interface" above; make sure this hook's cleanup (on unmount, or
   on starting a new run while one is active) actually calls that
   unsubscribe function, or you will leak an open SSE connection or a
   dangling `setInterval` (in demo mode) every time this page re-renders.

2. `loop-controls.tsx` (`LoopControls`) — fraud-type focus (`Select`: All
   or one of the seven `FRAUD_TYPE_TARGETS` keys — cross-check spelling
   against Appendix B), number of new attacks per cycle (`Select`: 50 / 100
   / 200), max cycles (`Select`: 1 / 3 / 5), "Run →" `Button`. Read the
   global nav's `?prefill=1cycle` search param (set by the "Run the loop"
   button, per Phase 5) and pre-fill max-cycles to 1 when present.

3. `loop-live-diagram.tsx` (`LoopLiveDiagram`) — a thin wrapper around the
   shared `design-system/patterns/loop-diagram.tsx` (Phase 3), rendered
   with `mode="live"` and `interactive={true}` (re-enabling pan/zoom, per
   the page spec's explicit note that a judge exploring the live page might
   want to zoom in — this is the one prop flip between this page's usage
   and the Home page's). Map incoming SSE/demo events to the `activeLeg`
   prop: a `cycle_start` event lights the Identify→Generate leg, a
   `miss_added` event lights the arc toward Improve, and so on — re-read
   the page spec's exact event-to-leg mapping description and implement it
   faithfully; if the real event `type` values end up not matching this
   description exactly once the backend is finished, that's a Phase 10 QA
   finding to reconcile, not something to guess around now.

4. `cycle-timeline.tsx` (`CycleTimeline`) — a vertical list, one row per SSE
   event received (not one row per cycle — every individual event), each
   with a timestamp (via `lib/format.ts`), a one-line description derived
   from the event's `type` and payload, and a delta chip where the event
   type is `metric_update`. On stream disconnection mid-run, render a final
   row: "Connection lost — showing results through the last received
   cycle," per "Empty, Loading, and Error States" above — never hang on a
   spinner (there are no spinners in this codebase) or leave the timeline
   silently frozen with no explanation.

5. `cycle-delta-tiles.tsx` (`CycleDeltaTiles`) — reuses the `KpiTile`
   pattern (Phase 3), updated in place after each `metric_update` event,
   each showing a `+/-` delta chip against the immediately-previous value
   (not against the run's starting value — a running delta, per cycle).

6. `run-history-table.tsx` (`RunHistoryTable`) — `@tanstack/react-table`
   bound `Table` (Phase 2), columns: start time, duration, final PR-AUC,
   cycles run, new attacks added, a "View artifacts →" external link to
   whatever output-directory path the API/demo fixture returns. Wire the
   `EmptyState` pattern for "no cycles run this session," per "Empty,
   Loading, and Error States."

7. `loop-page.tsx` — composes the header (exact copy), `LoopControls`, the
   left-60%/right-40% split (`LoopLiveDiagram` + `CycleTimeline` on the
   left, `CycleDeltaTiles` on the right), and `RunHistoryTable` full-width
   below. Ensure a run's completion appends a new row to the visible run
   history immediately (whether that's via TanStack Query cache
   invalidation triggering a refetch of `getLoopHistory()`, or an optimistic
   local append — either is fine, pick one and be consistent).

DO NOT, IN THIS PHASE:
- Import anything from `src/features/identify/`, `src/features/generate/`,
  or `src/features/defend/` directly.
- Build a second loop-diagram component. This page consumes the exact same
  shared component Home uses, with different props — if you find yourself
  wanting to write new diagram code here, stop; the correct fix is almost
  certainly a missing prop on the Phase 3 component, which should be added
  there (or flagged in `PROGRESS.md` for whoever can) rather than duplicated
  here.
- Let an unmounted or superseded SSE/demo-interval subscription keep
  running in the background — the unsubscribe-on-cleanup requirement in
  step 1 is not optional polish.

ACCEPTANCE CRITERIA:
[ ] `/loop` renders the full page; configuring controls and clicking "Run
    →" starts a visible sequence of events in demo mode: the diagram's
    active leg changes over time, the timeline fills in event-by-event, and
    the delta tiles update.
[ ] Navigating to `/loop` via the global nav's "Run the loop" button
    (`?prefill=1cycle`) arrives with max-cycles already set to 1.
[ ] Starting a second run while a first is still in progress does not leave
    two overlapping event streams both updating the UI — verify by
    triggering this deliberately and checking the browser's open-connections
    /active-timers state (or, in demo mode, confirming only one `setInterval`
    is alive) before finishing.
[ ] Navigating away from `/loop` mid-run (e.g., clicking "Identify" in the
    nav) and checking again confirms the stream/interval was actually torn
    down, not left running invisibly.
[ ] `RunHistoryTable` shows an `EmptyState` before any run has completed
    this session, and gains a new row immediately after the first run
    completes.
[ ] `LoopLiveDiagram` allows pan/zoom (drag to pan, scroll to zoom) — the
    one deliberate difference from the Home page's static, locked version
    of the same component.
[ ] Manually forcing a stream disconnection mid-run (a scratch test in
    demo mode — e.g., temporarily throwing inside the fake event emitter
    partway through) produces the "Connection lost..." final timeline row
    rather than a frozen or spinner-stuck UI.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — note the exact
event-`type`-to-leg mapping you implemented in step 3, since this is the
piece most likely to need reconciliation once the real backend's SSE event
shapes are finalized.

# Phase 9.5 — Motion & Visual De-Genericization Pass

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

This phase did not exist in the original 12-phase plan. It was inserted
after Phase 9 was reported nearing completion, in direct response to a
concern that the finished build — while structurally correct and already
compliant with the locked dark/restrained/no-gradient/no-glass token
system (Appendix D, H.5, H.27) — still reads as a generic AI-dashboard
template rather than a premium, purpose-built instrument in the register
of Stripe/Darktrace/Wiz/Datadog. See H.69 for why this was added as its
own phase rather than folded into Phase 10 or 11 (short version: both of
those phases explicitly forbid new visual/component work in their own
"DO NOT" lists — auditing and cutover are not the right place for design
work, so a dedicated phase is the only option that doesn't contradict
text already locked elsewhere in this document).

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–9
should be DONE — all five pages (Home, Identify, Generate, Defend, Loop)
exist and pass their own phase's acceptance criteria. This phase does not
build new pages, routes, or features. Its only job is to make the
existing, already-correct pages feel deliberately designed rather than
assembled — read H.71 (condensed from a current-dated research pass
against motion.dev and reactbits.dev, dated the same day as H.62) in full
before writing any code; it is the governing spec for this phase the way
Appendix D governs Phase 1.

This phase is a deliberate, one-time exception to the "each phase owns a
distinct set of files" convention every earlier phase follows — it revisits
components Phases 3 and 5–9 already built. That is intentional. Do not
interpret it as license to also change layout, color, spacing, typography,
or content on any component you touch — H.71's own definition of
"polished" (its §19) is explicit that polish here means motion restraint
and finishing detail, not new visual decisions.

YOUR TASK, IN ORDER:

1. **Finish H.68 project-wide, not just where Phase 5 left it.** Phase 5's
   `PROGRESS.md` entry logged H.68's icon-stroke-lockdown as partial.
   Audit every page (Home, Identify, Generate, Defend, Loop) for two
   things: (a) every live/updating number — KPI tiles, `CountUp`
   instances, the PR curve's operating-point label, the confusion
   heatmap's counts, the business-threshold table, `CycleDeltaTiles` —
   actually renders with `tabular-nums`, not just the components H.68 was
   written against; (b) every Lucide icon in the app resolves through the
   single wrapper in `design-system/icons.ts` at one of the two locked
   sizes with the one locked stroke-weight, with zero call sites passing
   an ad hoc `strokeWidth` or `size`. Re-run the icon-audit script already
   referenced in Phase 8's `PROGRESS.md` entry against the whole app, not
   one page.

2. **Home** — refine, don't rebuild. Confirm the `LoopDiagram` mount
   sequence and settled pulse still match H.71 §C's node/edge restraint
   (no glow, no particles, node geometry unchanged). Confirm `CountUp` is
   still AFL's own implementation (H.71 §7.2 — do not swap in React Bits'
   version). If the methodology/evidence section doesn't already have a
   single `useInView` reveal, add at most one per section (H.71 §I) — not
   one per child element.

3. **Identify** — wrap the attack-detail drawer's open/close in
   `AnimatePresence` if it isn't already (opacity + small directional
   movement only, per H.71 §4.1). Only add a `layout` transition on the
   filtered table if it demonstrably improves clarity at 25 rows; a
   visible cascade of all 25 rows moving is a regression, not polish
   (H.71 §H).

4. **Generate** — implement the empty-state → result transition as one
   coordinated reveal: transcript rows arrive with a short stagger
   (40–80ms succession, H.71 §4.4), then the transaction panel and diff
   panel settle. Real content must be visible immediately when it
   arrives — this phase must not add a delay, typing effect, or "LLM
   thinking" simulation in front of the real transcript (H.71 §D and its
   React-Bits-scramble-text ban, §7.6).

5. **Defend** — apply Motion `layout` to the advanced-fields disclosure
   (H.71 §F) so the 7-field → 23-field expansion reads as intentional
   rather than an abrupt jump. On a successful `Predict`, let the
   probability gauge settle to its real value and the SHAP waterfall
   enter once — no continuous animation on the gauge or bars, and no
   simulated processing step once the backend has actually responded
   (H.71 §E).

6. **Loop — the highest-priority page for this phase** (H.71 §9 calls it
   "the most animation-rich page because the product is actually
   processing a sequence here"):
   - `CycleTimeline`: each real SSE/demo event should produce one row
     entering with a restrained fade or short slide (H.71 §A / §7.1's
     Animated-List reference pattern) — no bounce, no bloom, no
     auto-generated demo rows, and item order must always match actual
     event-arrival order.
   - `CycleDeltaTiles`: on `metric_update`, the tile keeps its position
     and updates its value with a brief opacity/background emphasis only
     (H.71 §B) — never a scale pulse or screen flash.
   - `LoopLiveDiagram`: animate the active-leg state change subtly
     (opacity/border/fill only), preserving node dimensions and graph
     geometry exactly, with zero glow/particles/edge-beam effects
     (H.71 §C). **Before adding this transition, confirm what the
     component's `activeLeg` prop actually does to the two edges
     touching a node** — re-check H.2.6's semantic-direction decision
     against the current `loop-diagram.tsx` source itself. If Phase 9's
     own session left this specific question open (check its
     `PROGRESS.md` entry for a note to that effect), resolve it here
     before layering transition motion on top of a highlighting behavior
     nobody has confirmed against the actual code — animating an
     ambiguous state just makes the ambiguity harder to notice later.

7. **Re-audit, don't just add.** Once every component above has been
   touched, re-run the H.27 anti-pattern grep and walk H.67's numbered
   12-item checklist explicitly against the diff this phase produced —
   copying a reference implementation's structure is exactly how a stray
   `hover:scale` or `shadow-*` sneaks back in even when the intent was
   restraint.

DO NOT, IN THIS PHASE:
- Install any new npm dependency. Motion/framer-motion and Lucide are
  already present; if a React Bits component is adapted, copy and rewrite
  its source per H.71 §15 rather than installing a package for it, and
  only if its underlying mechanic (not its default visual style) is
  genuinely needed — Tier A/B in H.71 §17 covers everything this phase
  should need.
- Introduce anything from H.71's Tier D banlist: gradients, glassmorphism,
  backdrop blur, particle/aurora/beam/galaxy backgrounds, glow (border or
  hover), hover-scale or hover-lift transforms, 3D/tilt cards, confetti,
  magnetic cursor/button behavior, parallax, cinematic/curtain page
  transitions, decorative springiness/bounce, or scramble/decrypt/glitch
  text on normal UI copy.
- Change any locked color, spacing, radius, or typography token, or the
  content/copy of any page, while "improving" its motion. This phase's
  diff should be animation props, `AnimatePresence`/`layout` wrappers,
  `tabular-nums`, and icon-wrapper usage — nothing else.
- Let any new animation delay real data from appearing. Skeleton states
  (already built) come first; motion wraps the reveal of real content, it
  never gates it.
- Edit the text of Phases 0–9 anywhere above in this document, including
  Phase 9's own task list — if Phase 9's acceptance criteria are still
  unchecked when this phase starts, stop and say so rather than silently
  finishing Phase 9's own work under this phase's name.

ACCEPTANCE CRITERIA:
[ ] Every animation added in this phase maps to one of H.71 §8's use
    cases (A–I) by name in `PROGRESS.md`, or is justified against H.71
    §13's 20-question checklist if it doesn't cleanly map to one.
[ ] `prefers-reduced-motion`, toggled at the OS level, produces a correct
    settled end-state (not a frozen mid-animation state) on all five
    pages — verified in the browser, not assumed from code.
[ ] The H.27 grep and H.67's 12-item numbered checklist are re-run after
    this phase's changes and come back clean; any hit is fixed, not
    logged and left.
[ ] H.68's tabular-nums and icon-stroke/size rules are confirmed applied
    on every page (not only where Phase 5 left them), with the icon-audit
    script's output pasted into `PROGRESS.md`.
[ ] `LoopLiveDiagram`'s actual incoming/outgoing edge-highlighting
    behavior is stated plainly in `PROGRESS.md` (quoting the relevant
    source, per H.2.6/H.71 §C), and the transition motion added this
    phase matches whichever behavior is actually true in code — not the
    behavior the spec prose implies if the code disagrees.
[ ] Nothing on H.71's Tier D banlist appears anywhere in the diff this
    phase introduces (spot-checked, not merely assumed from the DO-NOT
    list above).
[ ] Before/after full-page screenshots exist for all five pages in
    `frontend/test-results/`, since this phase's actual success criterion
    — "does this now read as a specialized instrument rather than a
    generic AI dashboard" — is a judgment call the screenshots make
    checkable by the user, not something a script can assert.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — list which of H.71
§8's use cases (A–I) were implemented and which were deliberately skipped
and why, confirm the re-audit in step 7 came back clean, and give an
honest visual-review status the same way Phases 6–8 did (what you can
verify from tool/DOM output vs. what you cannot see directly, per H.64's
five questions).

---

# Phase 10 — QA, Accessibility, Performance, and Cross-Browser Hardening

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–9.5
should ALL be DONE (Phase 9.5 was inserted after Phase 9 — see H.69; if your copy of `PROGRESS.md` has no Phase 9.5 entry, treat that the same as any other unchecked prior phase per the paragraph below) — this phase is the first one that requires the entire
build to exist, because it audits the whole thing at once rather than
building a slice of it. If any earlier phase's acceptance criteria are
unchecked in `PROGRESS.md`, stop and say so rather than auditing an
incomplete build and reporting false negatives.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). This phase produces zero
new features and zero new visual components. Its entire job is to prove —
with tool output, not impressions — that the five pages built in Phases
5–9 actually hold up to the standard this whole document has been
asserting they'd meet: the locked token system (Appendix D), the locked
anti-patterns (§2.6 / "What the implementation phase is forbidden from
doing"), and a baseline of accessibility, performance, and cross-browser
correctness that a judge's 3-minute session should never trip over. This is
also where `tests/e2e/` (scaffolded empty in Phase 0, referenced but not
written in Phase 9) finally gets real content, and where `playwright.config.ts`
(also a Phase 0 skeleton) gets filled in with real projects.

Install these new dev-only dependencies this phase (do not add anything
beyond this list — see "DO NOT" below):
- `@axe-core/playwright` — accessibility assertions inside Playwright tests
- `rollup-plugin-visualizer` — one-time bundle composition report (see step 4)

YOUR TASK, IN ORDER:

1. Flesh out `playwright.config.ts` with three named projects — `chromium`,
   `firefox`, `webkit` — each run at two viewports via Playwright's
   `use.viewport`: a desktop pass at 1440×900 and a mobile pass at 390×844
   (iPhone-class, matching FRONTEND_VISION §5 Day 3's exact numbers — do not
   substitute a different device preset). That's six total run
   configurations for every spec file. Point `testDir` at `tests/e2e/`
   (already created empty in Phase 0) and set a `baseURL` of
   `http://localhost:5173` read from an env var so CI or a different port
   doesn't require editing this file. `webServer` config should boot
   `npm run dev` automatically before the suite runs, so a single
   `npx playwright test` is enough to execute everything in this phase —
   do not require the person running this to manually start the dev server
   first.

2. Write one smoke spec per page under `tests/e2e/`: `home.spec.ts`,
   `identify.spec.ts`, `generate.spec.ts`, `defend.spec.ts`, `loop.spec.ts`.
   Each one, at minimum:
   - Navigates to its route and asserts the page's header text (exact copy,
     per each page's own phase spec above) is visible.
   - Asserts zero messages were logged to the browser console at `error`
     level during load (attach a `page.on("console", ...)` listener before
     navigating; a `warn` is acceptable and should be logged to the test
     report, not failed on, unless it's a React key-prop warning, which
     fails the test — those are real bugs, not noise).
   - Exercises the one interaction that page exists to demonstrate: Home
     — the loop diagram's mount animation completes and settles into its
     pulse state; Identify — the taxonomy table filters when a category
     chip is clicked; Generate — running the compact generator against the
     demo fixture returns a transaction and populates the pillar-preview
     hook into Defend (per Phase 7/8's cross-page contract); Defend — the
     `ProbabilityGauge` and `ShapWaterfall` render non-empty for at least
     one demo transaction; Loop — clicking "Run →" produces at least one
     visible timeline row before the test ends.
   - Takes a full-page screenshot immediately after that interaction
     settles, saved to `tests/e2e/screenshots/<page>-<project>-<viewport>.png`
     (Playwright's project/viewport naming convention handles the
     differentiation automatically if you use `testInfo.project.name` in
     the filename — use that rather than hand-rolling names). These
     screenshots are the artifact Phase 11 re-captures against live data
     and the artifact the docx walkthrough and `README.md` draw from.
   - Reference the `?prefill=1cycle` deep link explicitly in the Loop spec
     (per Phase 9's acceptance criteria) — one test arrives via that link
     and asserts max-cycles is pre-set to 1, since that's a real navigation
     path a judge might hit if they click "Run the loop" from the nav
     before reading the rest of the page.

3. Automated accessibility audit — a sixth spec, `a11y.spec.ts`, that visits
   all five routes (desktop viewport only; accessibility rules don't
   meaningfully change with viewport, and doubling this pass adds runtime
   without new signal) and runs `@axe-core/playwright`'s
   `AxeBuilder(...).analyze()` against each. Assert zero `critical` or
   `serious` violations on every route. `moderate`/`minor` violations don't
   fail the test but must be enumerated in this phase's `PROGRESS.md` entry
   — every one, not a summary count, so Phase 11 or a human reviewer can
   triage them individually. Pay particular attention to three places this
   codebase is likely to trip axe, given what earlier phases built:
   - `Badge` components (Phase 2) — confirm the "never render color alone"
     rule actually produced an accessible-name-bearing label on every
     instance, not just a colored dot.
   - The `LoopDiagram` pattern (Phase 3) — SVG content needs either a
     `<title>`/`aria-label` per node or an `aria-hidden="true"` +
     text-equivalent-elsewhere pairing; check which approach Phase 3 took
     and confirm it's actually present in the rendered DOM, not just
     intended.
   - `ReactFlow`-based diagrams generally ship with poor default keyboard
     support — confirm focus can reach the diagram and Tab doesn't get
     trapped inside it or silently skip past it entirely.

4. Bundle and performance pass:
   a. Run `npm run build`. Read the actual Rollup/Vite output chunk sizes
      from the terminal — do not estimate. Temporarily add
      `rollup-plugin-visualizer` to `vite.config.ts`, rebuild once to
      generate its HTML treemap report, inspect it, then **remove the
      plugin and its import from `vite.config.ts` again before finishing
      this phase** — it's a one-time diagnostic tool, not a permanent build
      dependency, and leaving it wired in violates "bare minimum" from
      Phase 0.
   b. Confirm each of the four feature routes (`identify`, `generate`,
      `defend`, `loop`) is code-split via `React.lazy` + `Suspense` at the
      router level in `App.tsx` (Phase 5) — if Phase 5 shipped them as
      static imports instead, that's this phase's job to fix, since it's a
      routing-level change, not a new feature. Verify in the visualizer
      report that Recharts, ReactFlow, and Framer Motion each appear in
      only the chunk(s) for the pages that actually use them, not in the
      shared/main chunk.
   c. Run Lighthouse (`npx lighthouse http://localhost:5173/<route> --view`
      or the equivalent Chrome DevTools panel) against all five routes at
      both viewport classes — 10 runs. Record all four category scores
      (Performance, Accessibility, Best Practices, SEO) for each in
      `PROGRESS.md` as a table. Target floor: Accessibility ≥ 95 on every
      route (this should already be close to true given step 3's axe pass;
      Lighthouse's accessibility audit and axe-core overlap significantly
      but aren't identical, which is exactly why both are run), Performance
      ≥ 85 on desktop / ≥ 75 on mobile. Anything below floor gets fixed
      this phase if the fix is contained (an oversized unoptimized image,
      a missing `font-display: swap`, a missing `<meta name="viewport">`)
      or flagged in `PROGRESS.md` as a Phase 11 or post-submission item if
      the fix would require reopening an earlier phase's component work.

5. Anti-pattern self-audit — this is a **grep-based, scripted** check, not
   a visual skim, because the whole point is catching drift a human eye
   gets used to. Run each of these against `frontend/src/` and record exact
   findings (file:line, not just a pass/fail) in `PROGRESS.md`:
   - Any hex color literal (`#[0-9a-fA-F]{3,6}`) outside `src/index.css` —
     every color in every `.tsx`/`.css` file must be a token reference, per
     Appendix D and §2.6/"What the implementation phase is forbidden from
     doing." A hit here is a real bug — fix it, don't just log it.
   - Any Tailwind default palette class (`bg-blue-`, `text-purple-`,
     `border-red-`, etc. — the full default palette prefix list) — same
     severity as above.
   - Any `backdrop-blur` or `bg-*/[0-9]` (Tailwind's opacity-suffix
     shorthand used for glassmorphism) usage.
   - Any `box-shadow` / Tailwind `shadow-*` utility outside whatever single
     documented exception (if any) Appendix D actually carved out —
     cross-check, don't assume there is or isn't one.
   - Any emoji character in `.tsx` source (body copy, not code comments).
   - Any remaining `TODO(Phase` marker anywhere in `src/` — by this phase
     every one of these should have been resolved; any survivor is a
     regression from an earlier phase that got missed, not new work for
     this phase to silently do — fix the underlying gap this phase, but
     flag in `PROGRESS.md` which earlier phase's acceptance criteria should
     have caught it and didn't.
   - A raw count of TypeScript `any` usages (`grep -rn ": any\b" src/`) —
     doesn't block this phase, but record the count and the files, since an
     unreviewed pile of `any` is exactly the kind of thing that's cheap to
     audit now and expensive to discover during a live demo.
   - Any leftover `console.log` (as opposed to intentional `console.error`
     in an actual error-handling path) in committed source.

6. Manual interaction QA — walk the running app yourself, systematically,
   against this checklist (this is the one part of this phase that isn't
   automatable, so budget real time for it rather than rushing it):
   - Keyboard-only pass on every page: Tab reaches every interactive
     element in a sane order, focus rings are visible (Appendix D's focus
     token, per Phase 2's primitives note — never a suppressed
     `outline: none`), Enter/Space activate buttons and the taxonomy
     table's row expansion, no keyboard trap inside `LoopDiagram` or the
     `Table` primitive's sort headers.
   - `prefers-reduced-motion` respected: toggle it at the OS level, reload
     each page, confirm the loop diagram's mount sequence and the KPI
     count-up animations either skip straight to their end state or are
     meaningfully shortened — not merely "still plays the full animation
     because nothing actually checks the media query."
   - Resize the viewport continuously from 1440px down to 390px on every
     page — no horizontal scrollbar appears at any width, no text overlaps,
     no table overflows its container without an intentional horizontal
     scroll affordance on the table itself.
   - Browser back/forward through all five routes in sequence, then a hard
     refresh on each individual deep route (`/identify`, `/generate`,
     `/defend`, `/loop` directly, not just via in-app navigation) — confirm
     no 404 and no blank page. If `vite preview` (the prod-build server)
     doesn't have SPA-fallback configured for deep routes, fix that in
     `vite.config.ts` this phase; it's a one-line config gap, not a
     restructure.
   - Re-run Phase 9's SSE/interval leak checks, but this time scripted
     inside a Playwright test rather than manual DevTools inspection:
     assert that starting a second Loop run while one is active results in
     exactly one active subscription (hook into the demo-data fake-event
     emitter's own cleanup-call counter, incrementing a test-visible global
     or `window.__afl_test_hooks` object exposed only when
     `import.meta.env.DEV` is true — never ship this hook in a production
     build), and that navigating away mid-run tears the subscription down.

7. Cross-browser results — run the full spec suite (`npx playwright test`)
   across all three configured browser projects. Chromium passing and
   Firefox/WebKit failing is common specifically around SVG rendering
   (ReactFlow, Recharts) and `backdrop-filter`/custom-property fallback
   behavior — if either non-Chromium browser fails, diagnose whether it's a
   real rendering bug (fix it) or a test-authoring issue (a selector too
   Chromium-specific, a timing race — fix the test). Do not mark a real
   cross-browser rendering bug as "known issue, ship anyway" without
   explicitly recording that decision and its reasoning in `PROGRESS.md` —
   silently ignoring a failing non-Chromium run is exactly the kind of gap
   this phase exists to surface before a judge hits it live.

DO NOT, IN THIS PHASE:
- Add, remove, or restyle any component. Every fix in this phase is a
  targeted correction to something that violates an already-locked rule
  (a stray hex color, a missing SPA fallback, a missing `aria-label`) — not
  new design work. If a fix seems to require a new visual decision, stop
  and flag it in `PROGRESS.md` instead of deciding it yourself; that's a
  token- or component-spec-level question and this phase doesn't own
  either.
- Touch `docs/DESIGN_SYSTEM.md`, Appendix D, or any other locked token
  source, even if Lighthouse's contrast checker suggests a specific token
  is borderline — flag it, don't silently darken/lighten a color.
- Turn off or weaken any test once it's written because it's
  inconvenient — a flaky test gets fixed (usually a missing `await` or a
  race with the demo-data fake timers), not deleted or skipped.
- Leave `rollup-plugin-visualizer` wired into `vite.config.ts` after step 4a
  — it is explicitly a remove-after-use diagnostic tool for this phase only.
- Flip `VITE_DEMO_MODE` — this phase audits the build entirely in demo
  mode, exactly as Phases 5–9 built it. Phase 11 owns the live cutover.

ACCEPTANCE CRITERIA — verify every one of these yourself, against actual
tool output, not your own summary:
[ ] `npx playwright test` runs all six specs across all three browser
    projects and both viewports with zero failures (or every failure is
    explicitly triaged and recorded in `PROGRESS.md` as a known,
    reasoned-through issue — not silently left red).
[ ] `tests/e2e/screenshots/` contains a screenshot for every
    page × browser × viewport combination — 5 pages × 3 browsers × 2
    viewports = 30 files, named so each is unambiguous.
[ ] `a11y.spec.ts` reports zero critical/serious axe violations on all five
    routes; every moderate/minor violation is individually listed in
    `PROGRESS.md`, not summarized as a count.
[ ] The Lighthouse score table exists in `PROGRESS.md` with real numbers
    for all 5 routes × 2 viewports, and every score either clears the
    floor in step 4c or has an explicit note explaining why it doesn't yet
    and what would fix it.
[ ] The bundle visualizer report was actually opened and inspected (not
    just generated) and Recharts/ReactFlow/Framer Motion are confirmed
    route-scoped, not in the shared chunk — and the visualizer plugin
    itself is confirmed removed from `vite.config.ts` again afterward.
[ ] The anti-pattern grep audit in step 5 was actually run against the
    real `src/` tree (paste the actual command output into `PROGRESS.md`,
    not a paraphrase), and every hit that's a real violation (hex colors,
    Tailwind defaults, glassmorphism, unexplained shadows, emoji) is fixed,
    with zero remaining after the fix.
[ ] Keyboard-only navigation, `prefers-reduced-motion`, continuous resize,
    and deep-route-refresh were each manually verified on the running app
    per step 6, with any fixes made and re-verified afterward.
[ ] The scripted SSE/interval leak test from step 6 passes and demonstrates
    exactly one active subscription under the "start a second run while one
    is active" scenario.

BEFORE YOU FINISH: append your `PROGRESS.md` entry — the Lighthouse table,
the full list of moderate/minor a11y violations left open, the anti-pattern
grep results and what was fixed, any cross-browser rendering issue and
whether it was fixed or knowingly deferred (and why), and confirm
`VITE_DEMO_MODE` is still `true` in every committed `.env*` file, since this
phase must not have touched that.

---

# Phase 11 — Live Cutover, Freeze, and Submission Packaging

CONTEXT FOR A FRESH MODEL — READ THIS ENTIRE BLOCK BEFORE DOING ANYTHING

Before doing anything, read `frontend/PROGRESS.md` in full. Phases 0–10
must ALL be DONE — this is the final phase in the plan. There is no Phase
12; when this phase's acceptance criteria are all green, the build is
submission-ready. Per FRONTEND_VISION §5 ("The 3-day sequence") and §8
("The one rule that overrides all others"), this phase corresponds to Day
3 afternoon/evening plus the discipline of Day 4 ("submit, don't refactor")
folded in as this phase's own closing step, since this plan doesn't carry a
separate Day 4 phase.

PROJECT CONTEXT: "Adversarial Fraud Lab" (AFL). Everything up to this point
was built and QA'd against `VITE_DEMO_MODE=true` — canned fixture data that
never depends on the model, the generators, or the feedback loop actually
running correctly. That was the right call for building fast and safely,
but a prototype that's only ever been exercised against fixtures is not
actually proven. This phase is where the frontend meets the real
`FastAPI` backend for the first time end-to-end, where the whole thing gets
frozen, and where the specific artifacts the submission needs (screenshots,
`README.md`, the docx pointer) get produced. Nothing in this phase is
exploratory — every step has a specific, checkable output.

YOUR TASK, IN ORDER:

1. Live cutover. Create a **local, gitignored** `frontend/.env` (never
   `.env.example`, which stays `VITE_DEMO_MODE=true` forever — see "DO NOT"
   below) setting `VITE_DEMO_MODE=false` and pointing `VITE_API_BASE_URL`
   at the running backend. Start the real backend
   (`uvicorn src.api.main:app --reload --port 8000`) with the actual model
   and data loaded — confirm `GET /api/health` reports
   `model_loaded: true, data_loaded: true` before doing anything else; if
   it doesn't, this phase cannot proceed and the gap belongs to whoever
   owns the backend work referenced in Phase 0 step 4, not to this phase to
   silently work around.

2. Re-run every page's Phase 6–9 acceptance criteria against live data,
   not fixtures. This is a manual, page-by-page pass — do not assume
   "it worked in demo mode, so it'll work live." Specifically check the
   things fixtures can silently paper over: every numeric field renders a
   real number, never `NaN`, `undefined`, or a literal `"[object Object]"`;
   every chart's axis range is sane for the real data's actual min/max, not
   just the fixture's hand-picked range; the `ShapWaterfall`'s sign-based
   coloring still holds on a real SHAP response; the Identify page's 25
   attacks still match `attacks.json` field-for-field now that nothing is
   coming from `lib/demo-data/`; a real `POST /api/generate` and
   `POST /api/loop/run` SSE stream drives the UI exactly like the demo
   fixture's fake interval did (this is the single highest-risk item in
   this phase — the demo-data layer's shape and the real SSE payload shape
   were both built from the same `Appendix E`/`Appendix C` contract, but
   they were built by different phases at different times, so an untested
   drift here is entirely plausible).

3. Fallback hardening. FRONTEND_VISION §7 already locks the rule for the
   `generate` endpoint specifically ("rule-based fallback... LLM path
   silently skipped on any error, the demo never fails because of a flaky
   LLM endpoint") — this step generalizes that same rule to every other
   live call the frontend makes. For each of the five endpoint families
   (`/api/attacks*`, `/api/predict`, `/api/generate`, `/api/eval/*`,
   `/api/loop/*`), kill the backend process mid-request (or block the
   route at the network layer in DevTools) and confirm the page shows the
   `EmptyState`/error-toast pattern already established in earlier phases
   — never a blank screen, an unhandled promise rejection in the console,
   or a frozen skeleton. Where a page doesn't already degrade gracefully,
   add the narrowest possible fix (usually: an existing TanStack Query
   `onError` handler that isn't wired to anything visible yet) — this is
   not license to redesign error handling from scratch this late; if a
   page's error path needs more than a narrow fix, flag it in
   `PROGRESS.md` and fall back to `?demo=true` being forced for that one
   endpoint as an explicit, documented, last-resort decision rather than
   leaving the live gap unmitigated for the actual demo.

4. Cold-start full dry run — twice. Kill every running `node`/`vite`/
   `uvicorn` process. Start completely fresh: install nothing new, just
   `npm run dev` and `uvicorn ...` from a clean shell. Walk all five pages
   in nav order, run the loop once to full completion (whatever max-cycles
   value takes the least time while still exercising every event type),
   confirm zero console errors either run, and note the wall-clock time
   from cold start to "loop run complete" in `PROGRESS.md` — this is the
   number that determines whether the live demo fits inside a judge's
   3-minute window, per FRONTEND_VISION §1.1, and it needs to be a real
   measured number, not an estimate.

5. Submission screenshots — re-run Phase 10's Playwright screenshot suite
   one final time, now against live data, saved to `docs/assets/`
   (create this folder if it doesn't already exist in the wider repo — not
   `frontend/tests/e2e/screenshots/`, which is the QA copy from Phase 10
   and stays where it is). At minimum, capture and name clearly: the
   homepage mid-loop-animation, the homepage settled/pulsing state, the
   Defend page with a real `ShapWaterfall` populated, the Generate page
   mid-attack with a real conversation/transaction rendered, and the Loop
   page mid-run with `CycleDeltaTiles` showing real deltas. Update
   `README.md` so the very first thing after the title is the homepage
   screenshot, per FRONTEND_VISION §5 Day 3 evening's instruction — if
   `README.md` currently opens with anything else, move that content down,
   don't delete it.

6. Final anti-pattern and documentation audit. Re-run Phase 10's
   grep-based anti-pattern script one more time — a live-data pass can
   introduce a regression Phase 10 never had a chance to catch (a
   hardcoded color added while wiring an error state in step 3, for
   instance). Confirm `frontend/PROGRESS.md` has exactly one entry per
   phase, 0 through 11, with no gaps and no phase's entry overwritten by
   a later one. Confirm zero `TODO(Phase` markers remain anywhere in
   `src/`.

7. Submission Checklist verification. Walk the "Submission Checklist"
   referenced throughout this plan (repo, docx, and web-prototype
   three-deliverable structure) against what's actually on disk right
   now — not against what an earlier phase's `PROGRESS.md` entry claimed
   at the time, since claims can go stale. If anything on that checklist
   doesn't actually exist or doesn't actually work when exercised, report
   it plainly rather than checking the box anyway; this is the last phase
   before freeze, so this is the last safe place to catch a gap.

8. FREEZE. Once every acceptance criterion below is green, stop. Per
   FRONTEND_VISION §5 Day 4 ("Only emergency fixes. Don't add features.
   Don't restructure.") and §8 ("the one rule that overrides all others"),
   this plan's work is done. If your tooling supports it, tag the current
   commit (e.g. `git tag submission-freeze`) so there is an unambiguous,
   citable point-in-time reference for "this is what was submitted" if
   anything is questioned or drifts afterward. Any change after this point
   must be a named, scoped emergency fix — write what broke and why in
   `PROGRESS.md` before touching anything, not after.

DO NOT, IN THIS PHASE:
- Commit `VITE_DEMO_MODE=false` anywhere version-controlled.
  `frontend/.env.example` stays `VITE_DEMO_MODE=true` permanently, so a
  judge (or anyone else) cloning the repo fresh gets the safe, always-works
  fixture-backed experience by default without needing a live backend
  running. The live flip in step 1 exists only in the local, gitignored
  `frontend/.env` used to produce this phase's own screenshots and to run
  the actual live demo.
- Add any new page, component, token, or dependency. Every fix in this
  phase is a narrow correction surfaced by testing against real data or
  real failure conditions — not new scope. If step 2 or 3 surfaces
  something that genuinely needs new design work, that is by definition
  something this 12-phase plan didn't anticipate; flag it in
  `PROGRESS.md` for the user's explicit decision rather than deciding it
  unilaterally this late.
- Redesign error handling, retry logic, or the demo-data layer from
  scratch. Step 3's fallback hardening is explicitly narrow-fix-only.
- Skip the cold-start dry run, or run it only once. The whole point is
  catching a race condition or an ordering dependency that a warm dev
  server hides — one run is not enough evidence that it's actually fixed.
- Continue working past the freeze in step 8 without writing down, first,
  exactly what emergency and why.

ACCEPTANCE CRITERIA — verify every one of these yourself, against the
actual running app talking to the actual live backend, not against
fixtures and not against your own summary:
[ ] `GET /api/health` reports `model_loaded: true, data_loaded: true`
    against the live backend before any other step in this phase began.
[ ] Every page's Phase 6–9 acceptance criteria re-pass against live data,
    with any live-only discrepancy (shape drift between the fixture layer
    and the real API response) found and fixed, and noted in `PROGRESS.md`.
[ ] Killing the backend mid-request, tested against all five endpoint
    families, never produces a blank screen or an unhandled console error
    on any page — every page shows a proper error/empty state instead.
[ ] Two full cold-start dry runs completed back to back, both with zero
    console errors, with the measured wall-clock time recorded in
    `PROGRESS.md`.
[ ] `docs/assets/` contains the five live-data screenshots named in step 5,
    and `README.md` opens with the homepage screenshot immediately after
    its title.
[ ] The anti-pattern grep audit from Phase 10 was re-run against the
    current `src/` tree with zero unresolved hits.
[ ] `frontend/PROGRESS.md` has exactly one entry per phase 0–11, no gaps,
    nothing overwritten.
[ ] The Submission Checklist was walked item-by-item against what's
    actually on disk, and any gap was reported rather than silently
    checked off.
[ ] `frontend/.env.example` still reads `VITE_DEMO_MODE=true` — confirmed
    by actually opening the committed file, not from memory of step 1.

BEFORE YOU FINISH: append the final `frontend/PROGRESS.md` entry — this one
summarizes the whole build, not just this phase: confirm all 12 phases
(0–11) are DONE, list the measured cold-start timing, list any known,
deliberately-deferred issue from Phases 10–11 with its reasoning, and state
explicitly that the build is frozen as of this entry per step 8, so any
future editor opening this file knows unambiguously that further changes
should be scoped, named emergency fixes only.


---

# Appendix H — Frontend Implementation Clarifications, Contract Reconciliation, and Cline Runbook

> **Important:** This appendix is additive. It does **not** edit, delete, rewrite, or replace any preceding content in Phases 0–11. Its purpose is to remove implementation ambiguity discovered by auditing the complete repository and by checking the current official documentation for the libraries used by this build.
>
> **Precedence rule:** When the preceding phases contain an ambiguity or an internally inconsistent draft-era reference, use the explicit decision written in this appendix for implementation. Do not silently rewrite the earlier phase text. Record any actual code-level deviation in `frontend/PROGRESS.md` as already required.
>
> **Repository audit date:** 2026-08-29.
>
> **Audience:** Cline CLI / other coding agents that must build the frontend without asking repeated clarification questions.
>
> **Core objective:** Build the already-defined AFL prototype faithfully. Do not turn this into a generic admin dashboard, do not invent new product scope, and do not use the legacy frontend as a visual source of truth.

## H.0 — What was actually inspected

The implementation decisions below were checked against the repository supplied with this build, not only against the phase document.

Relevant repository sources inspected:

- `docs/FRONTEND_VISION.md`
- `frontend-vision.md`
- `docs/UI_IMPLEMENTATION_FINDINGS.md`
- `docs/ATTACK_TAXONOMY.md`
- `docs/HACKATHON_MASTER_PLAN.md`
- `docs/SOLUTION_OUTLINE.md`
- `docs/EXECUTION_STATUS.md`
- `docs/DESIGN_SYSTEM.md`
- `src/config.py`
- `src/fraud_model/inference.py`
- `src/identify/attack_profiles.py`
- `src/generator/rule_generator.py`
- `src/generator/llm_generator.py`
- `src/generator/anti_leakage.py`
- `src/models/evaluate.py`
- `src/models/feedback_loop.py`
- `CHANGELOG.md`
- repository `README.md`
- the bundled legacy `frontend/` inside the supplied `frontend.zip`

The bundled legacy frontend is **reference material for repository history only, not implementation guidance**. It contains a different sidebar-based information architecture, old token names, gradients, glassmorphism, hover transforms, and hardcoded dashboard data. Those characteristics directly conflict with the locked AFL frontend direction. Do not copy code, class names, layout patterns, token names, or visual effects from it.

The original frontend direction explicitly establishes a multi-view app with no sidebar, while the legacy frontend contains a permanent sidebar. The locked build therefore starts conceptually from a clean slate rather than incrementally modifying the old dashboard. The existing repository state confirms why this rule exists.

## H.1 — Final authority order for an implementation decision

When an agent encounters two instructions that appear to disagree, resolve them in this order:

1. A direct instruction in this Appendix H that explicitly reconciles an identified ambiguity.
2. The phase-local acceptance criteria in the relevant Phase 0–11 section.
3. The locked appendices in the main build bible:
   - Appendix A taxonomy
   - Appendix B fraud types/model columns
   - Appendix C API contract
   - Appendix D design tokens
   - Appendix E TypeScript interfaces
   - Appendix F real numbers
4. `docs/FRONTEND_VISION.md`.
5. Other historical/research docs such as `frontend-vision.md`.
6. Existing legacy frontend code is never authoritative for design.

This is intentionally narrow. It is not permission to redesign the product.

---

# H.2 — Contradiction ledger: issues discovered in the existing build bible

These are real ambiguities in the supplied specification. Do not improvise around them silently.

## H.2.1 Token-name mismatch

The canonical token appendix uses names such as:

```text
--bg-base
--bg-panel
--bg-elevated
--bg-grid
--border-subtle
--border-strong
--text-primary
--text-secondary
--text-muted
--text-mono
--accent-cyan
--accent-cyan-dim
--status-safe
--status-warn
--status-threat
--risk-minimal
--risk-low
--risk-medium
--risk-high
--risk-critical
--loop-attack
--loop-defend
--loop-identify
--loop-improve
```

Later prose sometimes refers to names such as:

```text
--color-bg-base
--color-bg-muted
--color-border-default
--color-border-focus
--color-fg-primary
--color-fg-secondary
--color-fg-muted
--color-accent
--color-risk-critical
--color-loop-identify
--text-caption
--text-data
--text-data-lg
--text-page-title
--text-section-title
--space-6
--shadow-sm
--shadow-md
--shadow-lg
--chart-1
```

Those latter names are not all defined by the canonical Appendix D shown in the build bible.

### Implementation rule

Do **not** silently add an entire second token system.

For the implementation, treat Appendix D's names as the canonical CSS custom properties. Use those exact variables directly:

```css
var(--bg-base)
var(--bg-panel)
var(--bg-elevated)
var(--border-subtle)
var(--text-primary)
var(--text-secondary)
var(--text-muted)
var(--text-mono)
var(--accent-cyan)
var(--status-safe)
var(--status-warn)
var(--status-threat)
var(--risk-minimal)
var(--risk-low)
var(--risk-medium)
var(--risk-high)
var(--risk-critical)
var(--loop-identify)
var(--loop-generate)
var(--loop-defend)
var(--loop-improve)
```

When Tailwind utility generation would otherwise require a `--color-*` namespace, prefer a static arbitrary-value utility or a normal CSS declaration that references the canonical variable.

Examples:

```tsx
className="bg-[var(--bg-panel)]"
className="text-[var(--text-primary)]"
className="border-[var(--border-subtle)]"
```

Do **not** introduce a parallel set such as both `--bg-panel` and `--color-bg-panel` merely to make utility names prettier.

If a Phase 2 component needs a token concept that truly does not exist, add a narrowly scoped extension only after checking whether the need can be satisfied by an existing canonical token. Record the extension in `PROGRESS.md`. Do not create an ad-hoc value inline.

### Why this matters

Tailwind scans source text for complete utility classes and does not understand arbitrary string construction. Dynamic class fragments such as ``bg-${color}`` are not reliable. Use explicit static class maps or CSS variables rather than building Tailwind class names dynamically. This is especially important for the risk, loop-leg, and category-color variants. citeturn889556search1

---

## H.2.2 Missing typography token definitions

Later phases refer to semantic typography concepts such as `--text-caption`, `--text-data`, `--text-data-lg`, `--text-page-title`, and `--text-section-title`, but Appendix D only declares the font families, not those semantic size tokens.

### Implementation rule

Do not create a second token sheet.

Implement these semantic roles through the locked typography specification:

- Page title: `Space Grotesk`, approximately 32px on feature pages.
- Hero headline: `Space Grotesk`, 56px / 64px on desktop as explicitly specified.
- Section title: `Space Grotesk`, approximately 24px.
- Body: `Inter`, 16px default.
- Caption / metadata: `Inter`, approximately 12–13px.
- Data numerals: `JetBrains Mono` or the explicitly stated display font where the phase says “large numeral”; for IDs, amounts, hashes and SHAP values use `JetBrains Mono`.

Do not invent a large ladder of typography tokens. Use the smallest set of semantic classes/components needed to make the pages consistent, and keep those values centralized if they are repeated.

---

## H.2.3 Missing spacing-token names

The document mentions `--space-6`, but the canonical design sheet intentionally says spacing is an 8px usage convention based on Tailwind's normal scale.

### Implementation rule

Do not create `--space-*` variables.

Use the normal Tailwind spacing scale consistently, with 8px as the preferred rhythm:

- 8px = `2`
- 16px = `4`
- 24px = `6`
- 32px = `8`
- 40px = `10`
- 48px = `12`
- 64px = `16`

A 4px increment is allowed inside dense table cells only, exactly as the main spec states.

---

## H.2.4 Missing shadow tokens

The build bible's Appendix D says the design is border-led and the homepage vision says “no shadows.” Later primitive prose mentions `--shadow-sm`, `--shadow-md`, and `--shadow-lg`.

### Implementation rule

Default to **no box shadows**.

Only use a shadow when the relevant phase explicitly allows it for an overlay such as Sheet/Dialog, and use the smallest implementation-safe value available from the component primitive rather than inventing visual depth for cards.

Never add a shadow to:

- ordinary cards
- KPI tiles
- loop nodes
- buttons
- table rows
- hero panels
- chart containers

The “technical blueprint” appearance comes from border contrast and surface hierarchy, not elevation effects.

---

## H.2.5 `.console` scope must remain exact

`.console` is a deliberately narrow dark-surface mechanism.

Use it only in:

1. `LoopDiagram` when `mode="live"`.
2. `ConversationTranscript`.

Do not apply `.console` at page-root level, `<body>`, global layout containers, or ordinary cards.

The reason is architectural: the pages are intentionally normal/light-surface content with two embedded dark “instrument” surfaces, rather than a second global theme.

Verify the inheritance boundary in DevTools.

---

## H.2.6 Loop-direction contradiction

The repository's conceptual flow is:

```text
Identify → Generate → Defend → Improve → Identify
```

However, some earlier wording describes the mount animation as:

```text
Identify → Generate → Improve → Defend
```

and the fixed-node geometry places:

```text
Identify = top
Generate = right
Improve = bottom
Defend = left
```

### Final implementation decision

Keep the **semantic closed loop** as:

```text
IDENTIFY
   ↓
GENERATE
   ↓
DEFEND
   ↓
IMPROVE
   ↺ back to IDENTIFY
```

Keep the **fixed node positions**:

```text
               [IDENTIFY]

                        [GENERATE]


[DEFEND]                            


               [IMPROVE]
```

Route the edges around the perimeter rather than drawing a confusing line directly through the center.

The live conceptual meaning of each edge is:

- Identify → Generate: turn a discovered attack into an adversarial scenario.
- Generate → Defend: turn the generated scenario into a transaction and score it.
- Defend → Improve: inspect misses and extract the failure signal.
- Improve → Identify: feed newly learned attack patterns back into the attack surface.

For the one-time Home-page animation, visually emphasize the same semantic order:

```text
Identify → Generate → Defend → Improve
```

The animation should therefore not imply that Improve comes before Defend, even if the older draft text says otherwise.

For React Flow, use four fixed nodes, four routed edges, and one explicit edge per semantic relationship. Prefer smooth-step/orthogonal routing around the outside of the composition. Do not allow edge paths to cross node bodies.

---

## H.2.7 Home hero dimension contradiction

The vision specifies both a `100vh` hero and a 480×480 loop diagram.

### Implementation rule

Desktop:

- Hero minimum height: one viewport.
- Do not force exact `height: 100vh` if that would clip content because browser UI or a very short viewport makes the content too tall.
- Use a minimum viewport-sized hero with natural content height.
- Never implement scroll-jacking.

Mobile:

- Prefer the small-viewport-safe CSS viewport unit (`svh`) for viewport-sized sections when supported, because mobile browser chrome can make plain `100vh` visually larger than the available space.
- The hero may become taller than one viewport on mobile; never shrink content below legible sizes just to force a one-screen composition.

The goal is “hero occupies the opening viewport,” not “content must be clipped to a CSS arithmetic target.”

---

## H.2.8 Home and nav behavior contradiction

The older vision says the nav “Run the loop” button opens a drawer.

Phase 5's explicit implementation says it navigates to:

```text
/loop?prefill=1cycle
```

### Final behavior

Use the Phase 5 behavior.

Clicking “Run the loop”:

1. Navigates to `/loop?prefill=1cycle`.
2. The Loop page sees `prefill=1cycle`.
3. It sets max cycles to `1`.
4. It does **not** automatically start the run.
5. The user still chooses/clicks “Run →”.

This keeps the action predictable and makes the deep-link testable.

---

## H.2.9 Identify feasibility scale contradiction

Some prose says “1–3 filled dots”; Appendix A has feasibility scores from 1–5.

### Final behavior

Use the actual `feasibility` field from `attacks.json`, which is on a 1–5 scale.

Render:

- 5 visual positions.
- `feasibility` filled positions.
- Empty positions use the neutral border/foreground treatment.
- The accessible name includes both the numeric value and human-readable wording.
- The number must remain available in text or tooltip; do not rely only on dot count.

Do not compress 1–5 into 1–3.

---

## H.2.10 Generate-page unsupported attacks ambiguity

The taxonomy contains 25 attacks, but only four currently have a generator profile:

```text
SE-001  voice_clone_scam
KYC-002 synthetic_identity_basic
PR-003  bnpl_max_out
AI-004  llm_jacking
```

### Final behavior

The Generate control may display the complete taxonomy so a judge can see the full attack surface, but only generator-backed entries are actionable.

Recommended implementation:

- All 25 attacks are shown in the picker.
- Non-wired attacks have visible `Conceptual`/`Partial` state and a disabled action state.
- Generator-backed attacks are selectable.
- The primary submit button is disabled when the selected attack is not generator-backed.
- A small inline explanation says the selected vector is catalogued but not currently wired to a generator profile.
- Never make a conceptual attack submit successfully by manufacturing fake generation behavior.

This preserves the diversity story without pretending that 25 generator implementations exist.

---

## H.2.11 User-ID control ambiguity

The Generate contract accepts:

```ts
user_id: number | "random"
```

but there is no endpoint in the contract that lists representative user IDs.

### Final behavior

Demo mode:

- It is acceptable to expose a small fixed set of fixture user IDs if those IDs are explicitly present in demo fixtures.
- Always include `Random`.

Live mode:

- Do not invent or fabricate user IDs.
- If no user-list endpoint exists, keep `Random` available and, if a specific-user control is shown, implement it as a numeric user-ID input rather than a fake select list.
- Do not fetch arbitrary users from undocumented endpoints.

---

## H.2.12 Transaction ID mismatch

The actual Python inference layer uses:

```text
transaction_id
```

and the generators emit a `transaction_id`.

The frontend's original `TransactionRow` interface, however, does not declare that field, while Phase 7 later refers to `result.transaction.id`.

### Final behavior

The canonical frontend transaction shape should allow:

```ts
transaction_id?: string;
```

because the backend generator/inference code actually uses it.

Do not rename it to `id` merely for frontend convenience.

When a transaction is generated, the frontend should read:

```ts
result.transaction.transaction_id
```

or the equivalent field confirmed from the final backend response.

If the backend wrapper deliberately transforms it to `id`, then the transformation must happen in one typed API-adapter layer and be documented in `PROGRESS.md`. Do not spread both names through the feature components.

---

## H.2.13 Generate result needs `user_medians`

The Diff Against Normal panel requires four comparisons against a user's median:

```text
amount
channel
hour_of_day
device_trust_age_days
```

The original Generate API contract does not provide those medians.

### Final behavior

Preferred backend/API extension:

```ts
interface UserMedians {
  amount: number;
  channel: string;
  hour_of_day: number;
  device_trust_age_days: number;
}

interface GenerateResult {
  ...
  user_medians?: UserMedians;
}
```

The field is required for the fully populated fidelity comparison.

Frontend behavior:

- If `user_medians` exists: render the four comparisons.
- If absent: render a clear “User baseline unavailable” state for that panel.
- Never fabricate a median on the frontend from the generated row itself.
- Never use a global dataset median when the panel says “same user's median.”

Record the contract extension in `PROGRESS.md`.

---

## H.2.14 Business-threshold table is underspecified in Appendix C

The Defend page requires precision, recall, F1 and operational counts across thresholds.

The existing `FraudInferenceService.get_business_metrics()` actually produces:

```text
threshold
precision
recall
f1
true_positives
false_positives
true_negatives
false_negatives
alert_rate
```

But the frontend API contract has no dedicated endpoint for it.

### Final behavior

Add a narrow endpoint:

```text
GET /api/eval/business
```

Suggested response:

```ts
interface BusinessMetricRow {
  threshold: number;
  precision: number;
  recall: number;
  f1: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  alert_rate: number;
}

type BusinessMetricsResponse = BusinessMetricRow[];
```

Thresholds must come from the centralized backend `BUSINESS_THRESHOLDS` configuration plus the actual frozen operating threshold if the backend policy requires that row.

The frontend should render the returned values and must not recompute precision/recall/F1.

This endpoint is a contract completion, not a new product feature.

---

## H.2.15 Confusion heatmap is underspecified

`EvalPerClassRow` contains:

```text
fraud_type
count
precision
recall
pr_auc
fpr
```

That is insufficient to produce a row-normalized fraud-type × predicted-label confusion heatmap.

### Final behavior

Add a narrow endpoint:

```text
GET /api/eval/confusion
```

Suggested response:

```ts
interface ConfusionRow {
  fraud_type: FraudType;
  predicted_legit: number;
  predicted_fraud: number;
  total: number;
}

type ConfusionResponse = ConfusionRow[];
```

The backend should use the same frozen evaluation split and operating threshold used for the page's evaluation story.

The frontend then normalizes each row for the visual fill percentage while displaying the raw count in every cell.

Do not reconstruct these counts from precision/recall/count on the client.

---

## H.2.16 Run history artifact links are underspecified

The Run History table asks for “View artifacts,” but the current `LoopHistoryEntry` has no URL/path field.

### Final behavior

Preferred contract extension:

```ts
interface LoopHistoryEntry {
  run_id: string;
  started_at: string;
  duration_s: number;
  final_pr_auc: number;
  n_cycles: number;
  n_new_attacks: number;
  artifact_url?: string;
}
```

Rules:

- `artifact_url` must be an actual browser-reachable URL.
- Never put a raw server filesystem path such as `C:\...` into an `<a href>`.
- Never expose local filesystem paths as if they were web resources.
- If the backend only writes artifacts to disk and does not serve them, render a non-link status such as “Saved locally” rather than a broken hyperlink, and record the contract gap.

Do not invent a URL.

---

## H.2.17 Generate SSE shape is underspecified

The Generate endpoint says it can return either:

- complete JSON, or
- SSE when generation takes longer than ~2 seconds.

But it does not define the SSE event types.

### Final frontend transport rule

The frontend API adapter must normalize both transports into the same `GenerateResult`.

Recommended stream event contract:

```ts
type GenerateStreamEvent =
  | { type: "progress"; message: string }
  | { type: "result"; result: GenerateResult }
  | { type: "error"; message: string };
```

The frontend may tolerate additional future progress events, but the final successful event must carry the full result.

Do not make feature components understand HTTP `Content-Type` branching.

The API client owns the transport details.

---

## H.2.18 Loop SSE lacks explicit baseline/final-run semantics

The current loop event list is enough to show incremental events but not enough to guarantee that a live page can always render a correct before/after summary without hardcoding a baseline.

### Preferred event extension

Add:

```ts
type LoopEvent =
  | {
      type: "run_start";
      run_id: string;
      started_at: string;
      baseline: {
        recall: number;
        pr_auc: number;
        fn: number;
        precision: number;
      };
    }
  | { type: "cycle_start"; cycle: number }
  | { type: "miss_added"; cycle: number; fraud_type: FraudType; count: number }
  | {
      type: "metric_update";
      cycle: number;
      metric: "recall" | "pr_auc" | "fn" | "precision";
      value: number;
    }
  | { type: "cycle_end"; cycle: number }
  | {
      type: "run_complete";
      run_id: string;
      final: {
        recall: number;
        pr_auc: number;
        fn: number;
        precision: number;
      };
      duration_s: number;
      n_cycles: number;
      n_new_attacks: number;
      artifact_url?: string;
    }
  | { type: "error"; message: string };
```

The frontend must remain tolerant of the old events while the backend is being finalized, but it must never fabricate a baseline in live mode.

Demo mode may use the known Appendix F historical values because those values are explicitly sourced and are already the demo story.

---

# H.3 Final frontend architecture

## H.3.1 Dependency direction

The dependency graph is:

```text
features
   ↓
chrome / design-system / lib
   ↓
browser + API boundary
```

More precisely:

```text
features/*
  ├── can import design-system/*
  ├── can import chrome/*
  └── can import lib/*

chrome/*
  ├── can import design-system/*
  └── can import lib/*

design-system/*
  └── can import lib/* only when it is genuinely generic
      (prefer not to, unless the pattern is formatting-related)

lib/*
  └── imports no feature/chrome code
```

A feature must never import a sibling feature.

A feature may share functionality through:

- `lib/`
- `design-system/`
- URL search parameters
- the explicitly allowed Zustand fields

---

## H.3.2 File ownership rule

Every file should have one clear owner.

Examples:

```text
src/chrome/top-nav.tsx
→ owns global navigation rendering

src/chrome/command-palette.tsx
→ owns palette presentation + command selection

src/features/identify/use-attacks.ts
→ owns Identify's query hook

src/features/generate/generate-controls.tsx
→ owns Generate form UI

src/features/defend/use-defend.ts
→ owns Defend data hooks

src/features/loop/use-loop.ts
→ owns Loop streaming/query state
```

Do not create generic folders such as:

```text
src/helpers/
src/utils2/
src/common/
src/misc/
```

when an existing architecture location already fits.

---

# H.4 Exact setup decisions for Cline

## H.4.1 Package manager

Use **npm**.

Reason:

- Phase 0 already specifies npm.
- The repo already contains npm package-lock files.
- Cline is working on a Windows-centered repository.
- Introducing pnpm solely because an older research note recommended it adds unnecessary environment variability.

Do not migrate the project to pnpm or bun.

---

## H.4.2 Framework

Use the Phase 0 scaffold:

```text
Vite
React 19
TypeScript
React Router 7
```

Do not switch the implementation back to Next.js just because older research docs mention Next.js 15. The supplied build bible deliberately changed the build sequence to Vite/React/TypeScript.

---

## H.4.3 Tailwind v4

Use the Vite integration:

```text
@tailwindcss/vite
```

and:

```ts
plugins: [react(), tailwindcss()]
```

Do not add a v3-style `tailwind.config.ts` solely to recreate an old theme configuration. Tailwind v4's `@theme` CSS is the intended token mechanism. Tailwind's own documentation confirms that theme variables declared with `@theme` generate utility APIs and CSS variables. citeturn515681search12

---

## H.4.4 shadcn/ui

Use shadcn as **owned source code**, not as an opaque component dependency.

Current shadcn documentation describes this model explicitly: the CLI copies component source into the project so the source can be modified. citeturn423138search2turn423138search0

When initializing an existing Vite project:

1. Run the CLI from `frontend/`.
2. Configure it for a Vite + React + TypeScript project.
3. Choose the base that best matches the phase's intended primitive stack.
4. Inspect every file the CLI writes.
5. Preserve the AFL token system.
6. Do not allow the CLI to become the source of truth for color, radius, or spacing.

Current shadcn supports Vite projects through the CLI, and its current configuration uses `components.json` to control component placement and aliases. citeturn423138search8turn423138search6

---

## H.4.5 Important shadcn dependency note for forms

The phases specify React Hook Form + Zod but omit `@hookform/resolvers` from the Phase 0 dependency table.

That resolver package is required for the standard Zod integration.

Current shadcn's React Hook Form documentation explicitly shows:

```ts
import { zodResolver } from "@hookform/resolvers/zod";
```

and uses it in `useForm(...)`. citeturn957766search10

### Final setup rule

Add:

```text
@hookform/resolvers
```

when Phase 2/7/8 form implementation requires it.

Do not solve Zod validation by writing an ad-hoc custom validator when the standard resolver is appropriate.

---

## H.4.6 Current shadcn Toast situation

Current shadcn documentation has multiple toast implementations in active documentation, including a current Base UI toast and Sonner, while the older Radix Toast page is marked deprecated. citeturn957766search1turn957766search2turn957766search4

### Final project rule

The project only needs a single owned `Toast` abstraction from Phase 2.

Do not let implementation churn in the shadcn registry change the application-level API.

If the current CLI gives a different internal toast implementation than the older draft expected:

- keep the project's `Toast` surface stable,
- keep the same visual tokens,
- keep the same accessibility behavior,
- keep usage generic,
- record the actual internal base library in `PROGRESS.md`.

Do not add both Radix Toast and Sonner just because both appear in documentation.

---

## H.4.7 Motion / Framer Motion

Keep the package selected by the phase plan.

Do not migrate to another animation package halfway through the build.

The current Motion documentation recommends reduced-motion handling through `useReducedMotion` or `MotionConfig`, and explains that reduced-motion should disable or simplify motion rather than merely slow the same animation. citeturn515681search1turn515681search2

The locked application-level rule remains:

- loop diagram: Motion allowed
- count-up: Motion allowed
- everything else: CSS transitions or no motion

---

# H.5 Global visual implementation rules

## H.5.1 Surface hierarchy

Use only the following conceptual layers:

```text
Page background
→ --bg-base

Standard panel
→ --bg-panel

Hovered/focused/elevated state
→ --bg-elevated
```

Do not introduce:

```text
glass
frosted glass
transparent white overlays
random tinted panels
gradients
noise
grain
3D cards
```

---

## H.5.2 Border hierarchy

Default:

```text
1px solid var(--border-subtle)
```

Emphasis:

```text
1px solid var(--border-strong)
```

Focus:

```text
2px visible accent focus treatment
```

Do not use border colors based on arbitrary semantic categories unless those categories already have locked tokens.

---

## H.5.3 Radius hierarchy

Default:

```text
card = 8px
input = 4px
loop node = 0px
```

Do not use:

```text
14px
16px
20px
24px
rounded-full
```

for ordinary content cards merely because a generated shadcn component came with those defaults.

`rounded-full` is acceptable only when the visual object is intentionally a pill/badge/status dot and the shape is semantically a pill.

---

## H.5.4 No gradients

No CSS gradient anywhere in the finished UI.

That includes:

```text
linear-gradient
radial-gradient
conic-gradient
Tailwind bg-gradient-*
gradient text
gradient borders
```

Exception: none for product UI.

The only thing visually resembling a gradient-like chart fill should be a normal solid token color.

---

## H.5.5 No glassmorphism

Never use:

```text
backdrop-filter
backdrop-blur
bg-*/opacity as fake glass
mix-blend-mode for decoration
```

The legacy bundled frontend uses glass-like effects; that code must not be copied.

---

## H.5.6 No decorative texture

Never implement:

```text
grain
noise overlays
data-matrix rain
scanline overlays
particles
animated starfields
random glowing dots
```

The product already communicates technical credibility through data, borders, and the loop.

---

# H.6 Global interaction model

## H.6.1 Every click target must communicate one of four outcomes

A clickable UI element should:

1. navigate,
2. open something,
3. change a local control/state,
4. submit/trigger a real operation.

Do not add decorative controls that appear interactive but do nothing.

---

## H.6.2 Buttons

Primary action:

- one dominant action in a section,
- concise verb label,
- no spinner,
- preserve button dimensions while pending,
- show a disabled state during a pending request if duplicate submission would be dangerous.

Secondary action:

- outlined/bordered.

Ghost action:

- text-only.

Do not use multiple cyan primary buttons fighting for attention within the same panel.

---

## H.6.3 Disabled controls

Disabled means:

- visibly reduced emphasis,
- still understandable,
- not hidden,
- `aria-disabled` or native `disabled` used correctly,
- no confusing tooltip requirement unless the reason genuinely needs explanation.

For a disabled “Urgency” selector, add a nearby explanation such as:

```text
Not used by this profile
```

rather than relying solely on visual dimming.

---

## H.6.4 Focus behavior

Never remove the focus outline without replacing it with an equally clear or better visible focus indicator.

At minimum:

```css
:focus-visible {
  outline: 2px solid var(--accent-cyan);
  outline-offset: 2px;
}
```

The exact visual must remain visible on dark and light surfaces.

WCAG 2.2 includes explicit requirements around focus visibility and target size; the project should treat these as implementation constraints, not optional polish. citeturn830860search3turn957766search12

---

## H.6.5 Pointer target size

Avoid tiny click targets.

Where a control is custom and not constrained by text layout, target approximately 24×24 CSS px or larger, and use more generous hit areas for important controls such as:

- Close
- Run
- Open drawer
- Next/previous
- Sort header

WCAG 2.2 Target Size (Minimum) is 24×24 CSS pixels with stated exceptions. citeturn957766search12

---

# H.7 Routing and deep links

## H.7.1 Route table

```text
/                    → Home
/identify            → Identify
/generate            → Generate
/defend              → Defend
/loop                → Loop
```

---

## H.7.2 Query parameters

Use URL search params only for one-time navigation context.

Supported:

```text
/identify?attack_id=SE-001
/generate?attack_id=SE-001
/loop?prefill=1cycle
```

Potential future/command-palette hints may use similarly scoped params, but do not introduce a global state field for a temporary route hint.

---

## H.7.3 `attack_id` lifecycle

On `/identify?attack_id=SE-001`:

1. Read the search parameter.
2. Wait for attack data if necessary.
3. Once the data is loaded, find `SE-001`.
4. Open its drawer.
5. Do not immediately remove the search parameter unless the router architecture benefits from replacing the history entry.
6. The drawer remains local UI state after initial hydration.

Do not create an infinite effect loop:

```text
URL → state → URL → state → URL
```

---

## H.7.4 Deep refresh

Direct navigation and hard refresh must work for:

```text
/identify
/generate
/defend
/loop
```

The application must boot into the same route without a blank page.

---

## H.7.5 React.lazy placement

Define every lazy component at module scope, never inside another React component. React's current documentation warns that declaring lazy components inside a component can cause state resets on re-render. citeturn957766search0

Use:

```ts
const IdentifyPage = lazy(() => import("./features/identify/identify-page"));
```

not:

```ts
function App() {
  const IdentifyPage = lazy(...);
}
```

---

# H.8 App shell

## H.8.1 Desktop header

Target:

```text
height = 56px
position = sticky top: 0
surface = --bg-panel
bottom border = --border-subtle
```

Contents, left to right:

```text
AFL
Adversarial Fraud Lab
Identify
Generate
Defend
Loop
System status
Run the loop
```

Keep the content inside a consistent page container on wide displays.

---

## H.8.2 Mobile header

At the 390×844 target:

- do not squeeze all nav labels into unreadable text,
- keep the AFL wordmark visible,
- replace the full nav row with a compact menu control,
- use the existing Sheet primitive for the temporary mobile menu,
- do not turn that into a permanent sidebar.

This is a responsive presentation of the same five routes, not a new information architecture.

The mobile menu must:

- open from a clear button,
- trap focus correctly while open,
- close on Escape,
- restore focus to the trigger,
- contain only the five page links plus the loop action,
- not add secondary navigation categories.

---

## H.8.3 Footer

Three logical columns on desktop.

On mobile:

```text
stack vertically
left
center
links
```

Do not create horizontal overflow solely to preserve three columns.

---

# H.9 Responsive layout contract

The design is desktop-led but must remain usable at 390×844.

Tailwind uses mobile-first responsive utilities, so establish the mobile structure with unprefixed classes and layer desktop behavior with breakpoint prefixes. The default breakpoints are `sm 640px`, `md 768px`, `lg 1024px`, `xl 1280px`, and `2xl 1536px`. citeturn889556search0

## H.9.1 Global container

Desktop:

```text
max width ≈ 1280px
margin auto
padding 32px
```

Tablet:

```text
padding 24px
```

Mobile:

```text
padding 16px
```

Never use a giant fixed left margin.

---

## H.9.2 Home

Desktop:

```text
Hero
→ two-column visual balance
→ loop diagram large

Stage cards
→ horizontal

Built on real attacks
→ 3 columns

Metrics table
→ full width

Loop narrative
→ structured two-column or asymmetric composition
```

Mobile:

```text
Hero
→ headline
→ subhead
→ loop
→ KPIs
→ CTA

Stage cards
→ stack

Built on real attacks
→ stack

Metrics table
→ horizontal scroll inside its own container

Loop narrative
→ stack
```

Do not shrink a table's text until it becomes unreadable merely to avoid horizontal scrolling.

---

## H.9.3 Identify

Desktop:

```text
header
filter bar
full table
```

Mobile:

```text
header
filter/search controls may wrap
table in an explicit horizontal-scroll container
```

The scroll container must not cause the page itself to scroll sideways.

Useful pattern:

```css
overflow-x: auto;
overscroll-behavior-x: contain;
```

---

## H.9.4 Generate

Desktop:

```text
40% controls
60% outputs
```

Mobile:

```text
controls
↓
transcript
↓
materialized transaction
↓
diff
```

The mobile page must not preserve a two-column split that compresses text below comfortable reading size.

---

## H.9.5 Defend

Desktop:

```text
hero input region | probability + SHAP
```

Mobile:

```text
transaction builder
↓
probability gauge
↓
SHAP waterfall
↓
metrics table
↓
heatmap
↓
PR curve
```

Charts must be allowed to shrink in width but should retain meaningful minimum height.

---

## H.9.6 Loop

Desktop:

```text
60% live pane | 40% delta pane
history full width
```

Mobile:

```text
controls
live diagram
event timeline
delta tiles
history
```

The live diagram should fit within the viewport without causing horizontal page overflow.

---

# H.10 Loading, error, and empty-state state machines

## H.10.1 Query lifecycle

Every data query should be considered in at least these states:

```text
idle
→ loading
→ success
or
→ error
```

A feature may additionally have:

```text
empty
partial
stale
streaming
```

Do not treat “loading” as “unknown forever.”

---

## H.10.2 Query hooks

The feature hook owns the API interaction.

Example conceptual shape:

```ts
export function useAttacks() {
  return useQuery({
    queryKey: queryKeys.attacks,
    queryFn: () => getApiClient().getAttacks(),
  });
}
```

Components consume the hook and render states.

Do not call `fetch()` directly from the component.

---

## H.10.3 Query cancellation

TanStack Query passes an `AbortSignal` to query functions and supports cancellation. Use it where the underlying request supports `fetch` cancellation. citeturn515681search3

For ordinary GET query hooks:

```ts
queryFn: ({ signal }) =>
  httpClient.getAttacks({ signal });
```

The HTTP client should not ignore a signal when one is available.

---

## H.10.4 Mutation lifecycle

A mutation has four meaningful UI states:

```text
idle
pending
success
error
```

TanStack documents these states directly. citeturn515681search13

For Generate/Predict/Run:

```text
idle
→ pending
→ result
```

On pending:

- prevent duplicate submission where appropriate,
- preserve layout dimensions,
- replace content with skeletons where the spec says loading skeleton,
- never display a spinning icon.

---

## H.10.5 Error strategy

Transient:

```text
toast
```

Persistent panel-level:

```text
inline error banner
```

Entire application boot failure:

```text
route-level error boundary
```

Never:

```text
blank screen
silent skeleton forever
red console only
```

The route shell should remain usable even when one feature request fails.

---

# H.11 Error boundaries

Because `React.lazy()` can propagate rejected module-loading errors to an Error Boundary, the router/app shell should include a small error boundary around routed page content. React's lazy documentation explicitly describes rejected dynamic imports being thrown for the nearest Error Boundary to handle. citeturn957766search0

### Required behavior

If a feature chunk fails to load:

```text
Page title:
"Page failed to load"

Explanation:
"The requested feature could not be loaded."

Action:
"Reload page"
```

The error boundary must not expose a stack trace to the judge.

Log the technical detail only through the existing error pathway appropriate for the environment.

---

# H.12 API client implementation contract

## H.12.1 One public surface

Feature code sees:

```ts
getApiClient()
```

and nothing else.

---

## H.12.2 HTTP JSON helper

Centralize common behavior:

```text
build URL
→ fetch
→ check response.ok
→ parse content type
→ return typed payload
→ throw typed error
```

A useful error type:

```ts
class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;
}
```

Do not throw raw `Error("Failed")` for every problem.

---

## H.12.3 Response validation

The project is TypeScript-first, but TypeScript alone cannot validate runtime JSON.

For high-risk API responses, especially live data:

- validate required fields at the API boundary,
- reject malformed payloads before they reach chart code,
- surface a controlled user-facing error.

The frontend may use Zod schemas for response validation even though Zod is already used for forms.

Do not make every UI component independently type-guard the same payload.

---

## H.12.4 Number hygiene

Before rendering any numeric response:

```ts
Number.isFinite(value)
```

must be true.

Never render:

```text
NaN
Infinity
undefined
null
[object Object]
```

For optional values, provide a deliberate “—” state where appropriate.

---

# H.13 SSE transport implementation

## H.13.1 Do not use EventSource for POST-with-body

`EventSource` is designed around a GET stream. The Loop contract uses POST with a request body.

### Final implementation

Use:

```text
fetch()
→ response.body.getReader()
→ TextDecoder
→ line/chunk parser
→ `data:` record extraction
→ JSON.parse
→ typed event callback
```

Do not add a new SSE package solely to solve this unless the backend architecture requires one.

---

## H.13.2 Parser requirements

The parser must handle:

- chunks split in the middle of a JSON object,
- multiple events in one chunk,
- blank-line event separators,
- `data:` prefixes,
- final unterminated chunk where reasonable,
- abort/cancellation,
- HTTP errors before streaming begins.

Never assume one `reader.read()` call equals one SSE event.

---

## H.13.3 Suggested parser algorithm

Conceptually:

```text
buffer = ""

while stream readable:
    chunk = decode(...)
    buffer += chunk

    while buffer contains "\n\n":
        record = everything before delimiter
        buffer = remainder

        extract all data: lines
        join data lines with "\n"

        parse JSON
        emit typed event
```

If the backend emits comment/heartbeat records:

```text
: heartbeat
```

ignore them.

---

## H.13.4 Cancellation

Each stream must have:

```text
AbortController
```

or an equivalent unsubscribe mechanism.

The hook must terminate the stream when:

- the component unmounts,
- a new run starts,
- a previous run is superseded,
- the user explicitly cancels if cancellation is later added.

The unsubscribe function must be idempotent.

Calling it twice must not produce an error.

---

## H.13.5 Connection-loss handling

Distinguish:

```text
normal completion
abort caused by navigation
unexpected disconnect
HTTP failure before stream
malformed SSE event
```

Do not report a user-initiated abort as a scary server failure.

For unexpected disconnect:

```text
Connection lost — showing results through the last received cycle.
```

This is the exact visible terminal state specified by Phase 9.

---

# H.14 TanStack Query rules

## H.14.1 Query keys

Create one centralized key map in `lib/constants.ts` or a dedicated query-key object.

Recommended shape:

```ts
export const queryKeys = {
  attacks: ["attacks"] as const,
  attack: (id: string) => ["attack", id] as const,
  evalPerClass: ["eval", "per-class"] as const,
  evalPrCurve: ["eval", "pr-curve"] as const,
  evalBusiness: ["eval", "business"] as const,
  evalConfusion: ["eval", "confusion"] as const,
  loopHistory: ["loop", "history"] as const,
  systemStatus: ["system", "status"] as const,
};
```

Use the same key for all hooks consuming the same resource so TanStack Query can deduplicate/cache them.

---

## H.14.2 Mutation success invalidation

When a successful loop run creates new history:

```text
invalidate loop history
```

TanStack Query recommends invalidating related queries after successful mutations when their cached data may now be stale. citeturn515681search0

Do not manually refetch unrelated pages.

---

## H.14.3 Status polling

Global system status is a changing resource.

A sensible implementation is:

```text
staleTime ≈ 30s
refetchInterval ≈ 15–30s
```

while the application is active.

Do not make it poll every second.

Do not poll when a static fixture is enough in demo mode unless the page behavior needs the changing timestamp.

---

# H.15 Design-system primitive contracts

## H.15.1 Button

Props must be predictable:

```ts
variant: "primary" | "secondary" | "ghost"
size: "sm" | "md" | "lg"
disabled?: boolean
type?: "button" | "submit" | "reset"
```

Behavior:

- native `<button>`
- `type="button"` by default when not inside a form
- keyboard activation works natively
- no custom click-only divs

---

## H.15.2 Input

Must support:

```text
id
name
value
defaultValue
type="text" | "number"
disabled
readOnly
aria-invalid
aria-describedby
```

Labels belong to the field, not floating as detached decorative text.

---

## H.15.3 Select

Single-selection only.

Keyboard requirements:

- open
- select
- escape
- tab away

Do not imitate a native select with arbitrary divs if the chosen shadcn/Radix primitive already provides the interaction model.

---

## H.15.4 Slider

Use for numeric values where continuous adjustment helps.

Always provide:

- visible current value,
- associated label,
- keyboard control,
- minimum/maximum,
- step.

Never hide the actual numeric value.

---

## H.15.5 Badge

Every badge has text.

This rule is absolute.

A colored rectangle with no label is not a complete badge.

---

## H.15.6 Table

The table component is a rendering primitive.

The data table owner handles:

```text
columns
sorting
row state
empty/loading
```

TanStack Table's current documentation distinguishes core, sorted, filtered, expanded, and paginated row models. For this project, only enable the features actually needed; do not add pagination or virtualization when the spec explicitly says they are unnecessary. citeturn889556search3

For client-side sorting in the current TanStack Table API, use the sorting feature/row-model API appropriate to the installed version rather than copying legacy v8 snippets verbatim. Current documentation distinguishes `createSortedRowModel` from older compatibility APIs. citeturn889556search4turn889556search5

---

# H.16 React Flow implementation contract

The project uses React Flow v11.

## H.16.1 Fixed Home diagram

Home:

```text
nodesDraggable = false
panOnDrag = false
zoomOnScroll = false
```

Do not render React Flow's default control UI on Home.

---

## H.16.2 Live diagram

Loop:

```text
nodesDraggable = false
interactive prop = true
pan enabled
zoom enabled
fit view enabled
```

Even in interactive mode, nodes themselves remain semantically fixed. “Interactive” means the canvas can be explored, not that the judge can redesign the graph.

React Flow's current documentation confirms `fitView`, `minZoom`, `maxZoom`, and controlled/uncontrolled viewport behaviors. citeturn515681search11

---

## H.16.3 Accessibility

React Flow currently supports keyboard and screen-reader interactions for focusable nodes and edges. It supports `nodesFocusable`, `edgesFocusable`, `disableKeyboardA11y`, and configurable ARIA labels. citeturn830860search0

For AFL:

- keep focusability enabled unless a concrete test proves it causes a trap,
- provide meaningful labels,
- make the surrounding text equivalent enough that the diagram is understandable without visual interpretation,
- ensure Tab can move into and out of the graph.

---

## H.16.4 Node dimensions

The phase text contains both:

```text
88×88
```

and:

```text
96×96
```

### Final decision

Use:

```text
96×96
```

for the primary four-node hero diagram because that is the explicit locked page specification.

If the Phase 3 component needs an internal 88px content box for layout reasons, the outer hit/visual node remains consistent with the final page visual spec and must be recorded as an implementation detail.

Do not resize the nodes independently per page.

---

## H.16.5 Handles

The handles are connection infrastructure, not decorative dots.

React Flow's documentation explains that handles are the connection points for edges and can be individually identified with IDs. citeturn830860search1

For a fixed graph:

- use the fewest handles necessary,
- assign explicit handle IDs,
- hide their default visual appearance if the handles are not meant to be seen,
- do not use `display: none` when a handle still needs to be measured.

---

# H.17 Recharts implementation contract

## H.17.1 Responsive container

The page is responsive.

Prefer a parent that controls width:

```text
width: 100%
```

and a fixed/controlled aspect ratio or height.

Do not hard-code:

```text
400px width
```

as the only size on mobile.

The 400×300 figure in the page spec is the intended desktop presentation size, not a command to overflow mobile screens.

---

## H.17.2 Accessibility

Current Recharts documentation exposes `accessibilityLayer`, which is enabled by default for accessibility support in relevant charts. citeturn515681search15

For AFL:

- leave accessibility support enabled,
- provide meaningful chart headings,
- ensure axes have human-readable labels,
- do not encode meaning only in color,
- expose operating-point values as visible text.

---

## H.17.3 SHAP waterfall

Color by sign:

```text
positive toward fraud
→ --risk-high / threat-family visual

negative / mitigating
→ --risk-low / safe-family visual
```

Feature identity does not determine color.

Each bar needs:

```text
feature name
signed value
```

and accessible text.

Do not depend on hover alone for the actual number.

---

## H.17.4 PR curve

Axes:

```text
x = Recall
y = Precision
```

Operating point:

```text
visible dot
visible label
```

The label must include:

```text
precision
recall
threshold
```

The chart is an evidence artifact, not a decorative line.

---

# H.18 Exact page behavior

## H.18.1 Home

### Load

On first mount:

```text
load system status
load per-fraud metrics
load attacks
render hero
```

Use skeletons only where data genuinely affects layout.

Do not make the entire page blank while unrelated data is loading.

---

### Hero

Required content:

```text
Headline
Subheadline
Loop diagram
4 KPI tiles
Run the loop CTA
```

Hero diagram:

```text
mode="static"
```

Click behavior:

- each node can act as a route affordance if implemented,
- if a node is not clickable, it must not look like a button.

---

### KPI values

Do not duplicate the same number in multiple places as separate hardcoded literals.

Prefer:

```text
API response
→ formatting helper
→ KpiTile
```

For historical “loop in motion” figures explicitly tied to the CHANGELOG, static values are acceptable.

---

### Built on real attacks

Identify miniature:

- top five most relevant/high-feasibility attacks
- use the actual data
- clicking “See all” navigates to `/identify`

Generate miniature:

- use `GenerateControls compact`
- preserve the same validation model as full Generate
- do not create a second form implementation

Defend miniature:

- use `TransactionBuilderForm compact`
- preserve the same field mapping as full Defend

---

## H.18.2 Identify

### Filter state

Keep filter state local to the page.

Suggested state:

```ts
selectedCategories: Set<string>
selectedStatus: "all" | "implemented" | "partial" | "conceptual"
search: string
selectedAttackId: string | null
```

If the shared `FilterBar` needs serialization, keep that implementation-specific.

---

### Search

Case-insensitive name matching.

Optionally include ID matching because it is useful for a technical taxonomy, but do not invent fuzzy semantic matching beyond what is required.

---

### Category D priority

The D/NOVEL discovery path must be visually easy to scan.

However, “first” does not mean “larger than everything else.”

Use ordering:

```text
D
A
B
C
E
```

or the exact ordering defined by the phase implementation, as long as D is first.

---

### Drawer

When opening:

```text
Sheet
→ title
→ status
→ feasibility
→ description
→ generator wired state
→ action
```

When closing:

- Escape closes,
- close button closes,
- focus returns to the triggering row/button.

Do not navigate away just to show details.

---

## H.18.3 Generate

### Initial state

Before the first successful run:

```text
controls visible
right side = EmptyState
```

Use the exact conceptual message:

```text
Generate an attack to see the narrative, materialized transaction, and fidelity comparison.
```

A precise final copy may be chosen during implementation, but it must explain why the area is empty.

---

### Submit

On submit:

```text
disable duplicate submit
show output skeletons
leave controls usable unless unsafe to change during request
```

Do not reset form fields unnecessarily.

---

### Success

Display:

```text
Transcript
Materialized Transaction
Diff Against Normal
Generation outcome
Drop statistics
```

The user must be able to understand:

```text
what was generated
what was accepted
what became a transaction
why it was accepted/rejected
```

---

### Fallback

If the LLM path fails:

```text
retry / route to rule-based
→ show result
→ show "Generated via rule-based fallback"
```

Never say:

```text
Generated by AI
```

when the result actually came from the rule path.

---

## H.18.4 Defend

### Form

The 7 primary fields are:

```text
amount
hour_of_day
channel
new_device
tx_last_1hr
device_trust_age_days
count_30d
```

The remaining 16 are advanced fields.

All 23 are sent in the request.

---

### `channel`

The generator code currently uses:

```text
card_present
ecom
```

in the rule-based path.

However, do not assume that the trained dataset contains no other category. The authoritative live values should come from the backend/data pipeline if that information becomes available.

For a demo control:

- use values proven valid by the current backend/dataset,
- do not add arbitrary strings.

---

### `three_ds_result`

The current generator code uses values such as:

```text
not_attempted
failed_then_passed
passed_first_try
success
```

Use exact backend-supported strings.

Do not normalize them to different UI-only enum keys before sending them back unless the API adapter maps them explicitly.

---

### Numeric field rules

General input constraints:

```text
amount >= 0
account_age_days >= 0
tx_last_1min >= 0
tx_last_1hr >= 0
tx_last_24hr >= 0
count_30d >= 0
time_since_last_s >= 0
dist_from_prev_km >= 0
geo_velocity_kmh >= 0
hour_of_day = 0..23
three_ds_failures_before_result >= 0
three_ds_failures_last_30d >= 0
device_trust_age_days >= 0
burst_count_10m >= 0
inter_transaction_time_s >= 0
```

Binary:

```text
new_device ∈ {0,1}
new_merchant ∈ {0,1}
is_high_amount_burst ∈ {0,1}
```

`amount_zscore_30d` may be negative and must not be incorrectly clamped to zero.

`merchant_cat_freq_user` is numeric and should not be transformed into a percentage unless the backend contract explicitly says so.

These are type/domain sanity constraints, not fake dataset-derived statistical ranges.

---

### Probability gauge

The gauge receives:

```text
probability
threshold
```

from the prediction response/PR-curve response.

Do not hardcode:

```text
0.95
```

or any other threshold.

The threshold is a live contract value.

---

### Result semantics

For the visible label:

```text
fraud
legit
```

the displayed status color should align with:

```text
fraud → threat family
legit → safe family
```

Do not imply that a high probability is “good.”

---

## H.18.5 Loop

### Initial state

Before a run:

```text
controls
idle diagram
empty timeline
empty history if no previous run
```

---

### Start

Disable the Run button while the run is active.

Do not allow two simultaneous run streams.

---

### Event-to-diagram semantic mapping

Recommended mapping:

```text
run_start
→ identify

cycle_start
→ identify or generate depending on the exact substep being shown

miss_added
→ improve

metric_update
→ defend

cycle_end
→ improve
```

The important semantic rule:

- Identify = attack surface being examined
- Generate = adversarial examples being produced
- Defend = model measurement
- Improve = misses becoming training feedback

If the final backend introduces richer event types, map them to the most semantically accurate leg.

Document the final event map in `PROGRESS.md`.

---

### Cycle timeline

Every received event gets a row.

Do not group all events in a cycle into one row.

Example:

```text
14:31:04  Cycle 1 started
14:31:07  42 missed ai_impersonation cases added
14:31:09  Recall 0.8241 → +0.0041
14:31:10  PR-AUC 0.9078 → +0.0006
14:31:11  Cycle 1 complete
```

The exact wording can vary, but it must be:

- concise,
- factual,
- derived from the event payload.

---

### Live region

The event list should expose dynamic status to assistive technology without forcing every low-level update to be annoyingly repeated.

Recommended:

```html
aria-live="polite"
aria-atomic="false"
```

on a dedicated status summary or event log region.

Use a compact textual current-state summary such as:

```text
Cycle 1 running. Recall improved to 84.67%.
```

rather than making the entire scrolling DOM a constantly announced giant block.

---

### Delta logic

For every metric:

```text
current value
previous value
delta = current - previous
```

Do not compare every cycle to the original baseline when the tile says “cycle delta.”

For first update:

```text
previous = baseline/current value before first update
```

---

# H.19 Formatting contract

## H.19.1 Percentages

Pick one display policy and use it consistently.

Recommended:

```text
0.9072 → 90.72%
0.596 → 59.6%
0.0052 → 0.52%
```

Do not alternate randomly between:

```text
90.72%
0.9072
.908
```

in the same visual system.

Exception:

- raw threshold values may remain decimal because `0.30`, `0.50`, `0.70`, `0.90` are decision thresholds, not percentages.

---

## H.19.2 Large counts

Recommended:

```text
1,064,963
1.06M
```

Use:

- full number in detailed contexts,
- compact number in constrained KPI/status contexts.

Do not display both styles randomly.

---

## H.19.3 IDs

Use monospaced formatting for:

```text
SE-001
run_...
tx_...
user_...
```

Never apply sentence-case typography to technical IDs.

---

## H.19.4 Dates

The API produces timestamps.

Format them as:

```text
short human-readable date/time
```

while preserving the underlying timestamp for actual ordering/sorting.

Do not sort by formatted strings.

---

# H.20 Data freshness and “real vs historical” labeling

The UI contains both:

```text
live metrics
historical facts
demo fixture metrics
```

These must not look deceptively identical.

Where useful, add small contextual text such as:

```text
Historical run
Demo fixture
Live
```

without cluttering every card.

The most important distinction is:

```text
Home "loop in motion"
→ historical evidence

Loop page while running
→ live stream/current session

Appendix F demo numbers
→ fixture-backed proof when demo mode is active
```

Never describe a hardcoded historical number as “live.”

---

# H.21 Demo mode behavior

## H.21.1 Frontend switch

```text
VITE_DEMO_MODE=true
```

means:

```text
getApiClient()
→ demoClient
```

Every page remains visually and structurally identical between demo and live modes.

The UI must not render:

```text
Demo Mode
```

as a giant banner.

A small subtle status indicator is allowed if useful for debugging, but the judge experience should focus on AFL.

---

## H.21.2 Fixture delay

Use a random artificial delay within the specified range rather than always returning synchronously.

Suggested:

```text
150–400ms
```

This allows:

```text
skeleton
→ result
```

to be visible without making the demo feel artificial.

---

## H.21.3 Demo SSE timing

The fake Loop stream should take long enough that the judge can see:

```text
event
→ diagram change
→ timeline update
→ metric change
```

but not so long that one cycle occupies most of the demo.

Use the existing phase guidance of roughly 3–5 seconds per cycle in demo mode.

Do not make it instantaneous.

---

# H.22 Accessibility checklist by component

## Navigation

- `<nav>` landmark
- visible focus
- current route indication
- keyboard activation
- mobile menu focus trap and restore

## Buttons

- native `<button>`
- accessible text
- disabled state correctly announced

## Inputs

- `<label for>` / matching `id`
- errors associated with `aria-describedby`
- invalid state with `aria-invalid`

## Tables

- semantic `<table>`
- `<caption>` or accessible heading
- `<th scope="col">`
- sortable headers announce sort state
- horizontal scroll container has an accessible name when needed

## Drawer/Sheet

- visible title
- description
- focus trap
- Escape
- return focus

## Charts

- title
- visible numeric summary
- accessibility layer where supported
- data not communicated exclusively by color

## Loop diagram

- accessible labels
- text-equivalent explanation
- no keyboard trap

React Flow's current accessibility implementation supports focusable nodes/edges and ARIA descriptions, so use those mechanisms rather than disabling keyboard accessibility globally. citeturn830860search0

---

# H.23 Motion accessibility contract

## H.23.1 Global

Respect:

```text
prefers-reduced-motion
```

Do not merely reduce duration of all animations.

For the loop diagram:

```text
normal:
    intro animation
    then pulse

reduced:
    final static state immediately
    no pulse
```

For count-up:

```text
normal:
    0 → target over 1.2s

reduced:
    target immediately
```

Motion's current React documentation explicitly supports querying the user's reduced-motion preference and recommends simplifying/disabling problematic motion. citeturn515681search1turn515681search2

---

# H.24 Performance contract

## H.24.1 Do not optimize before measuring

The build is small enough that premature abstraction can make it slower rather than faster.

Measure:

```text
build
bundle
route chunks
Lighthouse
Playwright runtime
```

then optimize evidence-backed issues.

---

## H.24.2 Code splitting

Lazy-load the four feature routes.

The shared chunk should contain:

```text
React
Router
shared chrome
design-system
basic lib
```

Heavy feature-specific libraries should not be eagerly imported into every route when avoidable.

---

## H.24.3 Chart and React Flow imports

Keep Recharts imports in the Defend route/module tree.

Keep React Flow imports in the loop-diagram tree.

Do not import the heavy visualization libraries from a global `design-system/index.ts` barrel used by every page.

This preserves route-level code splitting.

---

## H.24.4 Images

The current prototype does not require decorative image assets.

If an image is genuinely needed:

- use an actual asset,
- define dimensions,
- provide meaningful alt text or mark decorative images as decorative,
- do not add random stock art to fill space.

---

# H.25 Playwright implementation contract

Current Playwright supports:

- named projects for multiple browsers/devices,
- `webServer` for starting a local app automatically,
- screenshot artifacts.

The existing phase design should use those facilities rather than shelling out to ad-hoc scripts. citeturn515681search10turn515681search7

## H.25.1 Projects

Exactly:

```text
chromium
firefox
webkit
```

with:

```text
desktop = 1440×900
mobile  = 390×844
```

Six configurations total.

---

## H.25.2 Stable test selectors

Do not use brittle selectors such as:

```text
nth-child(4)
div > div > button
CSS class names that are purely stylistic
```

Prefer:

```text
getByRole
getByLabel
getByText
data-testid only when role/label is insufficient
```

Good examples:

```text
getByRole("button", { name: "Run →" })
getByRole("heading", { name: "Attack Taxonomy" })
getByLabel("Amount")
```

If a test id is needed, use:

```text
data-testid="defend-probability"
data-testid="loop-event-log"
data-testid="attack-row-SE-001"
```

Do not expose internal implementation details in selectors.

---

## H.25.3 Console error capture

Attach the console listener **before navigation**.

Fail on:

```text
console.error
```

Also fail if a React key warning appears even if emitted at warning level.

Allow unrelated non-error warnings only when explicitly recorded.

---

## H.25.4 Screenshot naming

Recommended:

```text
<page>-<browser>-<viewport>.png
```

Examples:

```text
home-chromium-desktop.png
home-chromium-mobile.png
identify-firefox-desktop.png
...
```

For the Phase 10 matrix:

```text
5 × 3 × 2 = 30 screenshots
```

---

# H.26 Visual QA procedure

For every page, evaluate in this order.

## Pass 1 — structure

Check:

```text
title
main sections
spacing
alignment
responsive stacking
```

## Pass 2 — visual language

Check:

```text
surface hierarchy
borders
type hierarchy
cyan restraint
absence of gradients
absence of glass
absence of excessive pills
```

## Pass 3 — interaction

Check:

```text
hover
focus
click
keyboard
drawer
form validation
loading
error
empty
```

## Pass 4 — data

Check:

```text
numbers
labels
units
percentages
IDs
dates
```

## Pass 5 — accessibility

Check:

```text
tab sequence
focus visibility
labels
aria
live regions
chart accessibility
diagram accessibility
```

## Pass 6 — responsive

Check:

```text
1440×900
390×844
and continuous resize in between
```

Do not stop after checking only two fixed viewport sizes. The Phase 10 specification already calls for continuous resizing.

---

# H.27 Visual style anti-pattern audit

Search the final source tree for:

```text
backdrop-blur
bg-gradient
from-purple-
via-pink-
to-orange-
hover:scale
hover:-translate
translate-y on hover
shadow-
emoji characters
console.log
TODO(Phase
```

Also search for raw color literals outside the canonical token file.

Any hit must be inspected.

A search hit is not automatically a bug if it lives in:

- a code comment,
- an external test fixture,
- a documentation example.

But visual source code hits are presumptively a defect.

---

# H.28 Legacy frontend quarantine rule

The supplied repository contains an older frontend implementation with files resembling:

```text
frontend/src/components/Sidebar.tsx
frontend/src/components/Header.tsx
frontend/src/components/Card.tsx
frontend/src/components/RiskScore.tsx
frontend/src/pages/Dashboard.tsx
```

That implementation is **not** to be evolved into the final AFL site.

Specific legacy characteristics that must not survive into the final implementation:

```text
Sidebar
FraudGuard wordmark
Dashboard / Investigations / Rules / Models nav
gradient card fills
glass card variant
hover lift
gradient text
fake hardcoded dashboard metrics
old color tokens such as --color-bg-0 / --color-bg-1
```

Delete or replace the legacy implementation as instructed by Phase 0. Do not merge it with the new architecture.

---

# H.29 Current backend facts the frontend must respect

## H.29.1 Inference

`FraudInferenceService.predict_single(...)` currently returns fields shaped around:

```text
transaction_id
fraud_probability
fraud_prediction
threshold_used
tier
```

and accepts:

```text
threshold
include_tier2
```

It does not natively return the frontend's `probability`, `label`, and `shap` contract in exactly the same field names.

### Final backend adapter rule

The FastAPI route should adapt backend service output into the frontend API contract.

Do not make every React component know the Python implementation vocabulary.

---

## H.29.2 Health

The current Python health-check implementation returns fields such as:

```text
status
tier1_loaded
tier2_loaded
tier2_p99_threshold
test_prediction
```

rather than the simplified Appendix C shape.

### Final backend route rule

The `/api/health` route should normalize backend health into the frontend contract:

```json
{
  "status": "ok" | "degraded",
  "model_loaded": true,
  "data_loaded": true,
  "n_users": 15000
}
```

where those values can be established honestly from the actual backend state.

Do not expose the raw internal health shape directly if the frontend contract expects another shape.

---

## H.29.3 `channel`

The current rule-based generator uses:

```text
card_present
ecom
```

The canonical demo transaction in the build bible uses:

```text
card_present
```

while the actual inference smoke-test transaction in `health_check()` uses:

```text
online
```

This is a real inconsistency between the generator and health-check examples.

### Frontend rule

Never infer categorical option lists from one hardcoded sample.

Use the final backend/dataset-supported options.

If the backend cannot expose them dynamically, use only values verified against the actual model pipeline and document the chosen set.

---

# H.30 Current model-field facts

The authoritative model input count is:

```text
20 numeric features
+ 3 categorical features
= 23 MODEL_COLS
```

Numeric:

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

Categorical:

```text
merchant_category
channel
three_ds_result
```

The current `src/config.py` is the source of truth for this list.

Never create a shortened “frontend version” and then silently submit only the shortened version to the model.

---

# H.31 Home metrics reconciliation

There are multiple historical metrics in the repository:

- `README.md` contains an older 96.3% headline.
- `CHANGELOG.md` documents the frozen Tier 1 test PR-AUC as `0.9072`.
- older frontend-vision prose contains `0.807` in the homepage example.
- later Build Bible materializes `0.9072` as the current baseline.

### Final UI rule

Use the later Build Bible/CHANGELOG value:

```text
PR-AUC baseline = 0.9072
```

when a historical baseline is required.

For the live Home KPI, prefer the current `/api/system/status`/evaluation response over a hardcoded literal.

Do not display the stale README number as if it were current.

---

# H.32 Honest metric labeling

Use phrases that make metric provenance clear.

Good:

```text
Test PR-AUC
Validation recall
False negatives
Operating threshold
Historical feedback-loop result
```

Bad:

```text
Accuracy
Success rate
AI score
Confidence
```

when those are not the actual metrics.

Do not rename PR-AUC to “accuracy.”

Do not rename recall to “detection rate” unless the relevant spec explicitly wants that wording.

---

# H.33 Fraud-type table semantics

For:

```text
count
precision
recall
pr_auc
fpr
```

render the fraud type exactly as the backend key in monospace where technical clarity is desired:

```text
ai_impersonation
synthetic_identity
bnpl_abuse
```

A human-readable label may be shown in a secondary visual label, but do not replace the actual key entirely because the key is the technical evidence.

---

# H.34 Business-threshold table semantics

Threshold rows:

```text
0.30
0.50
0.70
0.90
```

Columns:

```text
Threshold
Precision
Recall
F1
FP
FN
Alert rate
```

Potentially include:

```text
TP
TN
```

if width allows.

The point is to make the precision/recall tradeoff legible to an operational reviewer.

Do not highlight only the highest metric. The point is that threshold choice is a business decision.

---

# H.35 Accessibility of color semantics

Color mappings must always have text.

Examples:

```text
✓ validated
✗ rejected
Online
Offline
Fraud
Legit
High
Critical
```

Do not communicate:

```text
green = good
red = bad
```

without text.

This applies to:

- heatmap cells,
- badges,
- SHAP bars,
- status pills,
- loop active-leg styling.

---

# H.36 Table and chart overflow contract

A visualization may have its own scroll/clip region, but the page must not unexpectedly overflow horizontally.

Required:

```text
body width = viewport
```

not:

```text
body width = content width
```

When a table is wider than the viewport:

```text
outer panel
→ horizontal overflow inside panel
```

rather than:

```text
whole page → horizontal overflow
```

---

# H.37 Form submission and Enter-key rules

Generate/Defend forms should submit on Enter where native form semantics allow.

Exception:

- multiline transcript content areas are not user-editable anyway.
- controls inside a select popover should not trigger the parent form accidentally.

Use:

```html
<form onSubmit={handleSubmit(...)} />
```

and a real submit button.

Do not manually listen for every Enter key unless the primitive interaction requires it.

---

# H.38 Query cache and URL-state separation

Use Zustand only for the three deliberate cross-cutting values already specified:

```text
commandPaletteOpen
dataSource
lastGeneratedTransactionId
```

If Phase 8 requires the complete generated transaction object for the cross-page handoff, the documented one-field exception is:

```text
lastGeneratedTransaction
```

Use URL state for:

```text
attack_id
prefill=1cycle
```

Use local feature state for:

```text
filters
drawer open
selected row
form dirty state
active stream
cycle timeline
```

Use TanStack Query cache for:

```text
server data
```

Do not put server response collections into Zustand.

---

# H.39 Command palette behavior

Keyboard shortcut:

```text
Ctrl+K
Cmd+K
```

Must:

- work from any page,
- not break text editing behavior,
- not steal focus from normal text input shortcuts when the input is actively handling the same combination,
- focus the search field when opened,
- close on Escape,
- restore focus to a sensible element.

Groups:

```text
Go to page
Attacks
Actions
```

Attacks are fetched/cached once through TanStack Query.

---

# H.40 Command palette actions

Exactly the three named actions:

```text
Run the loop
Generate a random attack
Predict a random transaction
```

Recommended routes:

```text
Run the loop
→ /loop?prefill=1cycle

Generate a random attack
→ /generate?attack_id=<chosen generator-backed id>

Predict a random transaction
→ /defend
```

If a random transaction fixture is available, load it after navigation.

Do not invent a new `/random` route.

---

# H.41 Accessibility of dynamic updates

For dynamic values such as:

```text
probability
prediction label
loop cycle metrics
connection state
```

do not put `aria-live="assertive"` on everything.

Use:

```text
polite
```

for ordinary progress.

Reserve assertive announcements for genuinely urgent state changes only.

The page must remain pleasant for screen-reader users during a multi-event loop run.

---

# H.42 Content-writing rules inside the UI

Avoid:

```text
powered by AI
intelligent platform
next-generation AI
smart fraud
revolutionary
magic
```

Prefer factual descriptions:

```text
LLM-generated narrative
rule-based fallback
23-feature transaction representation
test-set PR-AUC
validation recall
closed-loop feedback
```

Do not exaggerate model capability.

---

# H.43 No fake “live” indicators

A green pulsing dot does not make a system live.

For `System status`, the status should be derived from actual backend/demo state.

In demo mode, “Online” means:

```text
the demo data source is available
```

not:

```text
the production inference stack is running
```

If you choose to show additional status text in demo mode, use something honest such as:

```text
Demo · 1.06M tx
```

but do not clutter the judge-facing nav unless necessary.

---

# H.44 Cline execution protocol

Cline should execute each phase in this exact order:

## Step A — read

Before editing:

```text
README.md
docs/FRONTEND_VISION.md
frontend/PROGRESS.md
relevant phase
Appendix H sections relevant to that phase
```

Then inspect the actual files named in the phase.

---

## Step B — reconcile

Before writing code:

- identify any ambiguity,
- look for an existing repo implementation,
- decide from the authority order,
- avoid asking a question when Appendix H already answers it.

---

## Step C — implement the smallest complete change

Do not prematurely implement future phases.

Do not add:

```text
new page
new abstraction
new dependency
new design token
new backend feature
```

unless the current phase or an explicitly documented contract completion requires it.

---

## Step D — run the app

Use the actual dev server.

Do not rely exclusively on:

```text
TypeScript compile
```

because visual and interaction errors can survive type-checking.

---

## Step E — inspect the browser

For relevant phases:

```text
desktop screenshot
mobile screenshot
console
network
computed styles
keyboard navigation
```

Use Playwright or browser tooling available to Cline.

---

## Step F — verify against acceptance criteria

Do not write:

```text
all criteria passed
```

unless each criterion was actually checked.

The existing project requires evidence-oriented `PROGRESS.md` entries.

---

## Step G — append progress

Record:

```text
files
deviations
verified criteria
known issues
```

Never rewrite old entries.

---

# H.45 Cline “do not get confused” checklist

Before creating a new file, ask internally:

```text
Is this explicitly required by the current phase?
Does an existing file already own this concern?
Will this introduce a second source of truth?
Does this cross the feature dependency boundary?
Can the requirement be satisfied by existing primitives?
```

If the answer indicates duplication, stop and use the existing layer.

---

# H.46 Cline “do not overfit to the screenshot” rule

Screenshots are a validation mechanism, not a substitute for semantics.

Do not write brittle code such as:

```text
absolute position everything
hardcode text widths
fix table by magic pixel offset
set 1px negative margins to align icons
```

Use:

```text
flex
grid
normal flow
consistent gaps
max widths
intrinsic content sizing
```

Only use absolute positioning for genuinely layered UI elements such as:

```text
chart marker
status dot
drawer close icon where appropriate
```

---

# H.47 Cline “one component, one responsibility” rule

Bad:

```text
HomePage.tsx
→ fetches attacks
→ fetches metrics
→ renders nav
→ renders footer
→ owns command palette
→ renders chart
→ formats dates
```

Better:

```text
HomePage
├── hero
├── hero-kpi-row
├── pillar-preview-cards
└── numbers-that-hold-up
```

with data access in hooks.

The exact file split remains phase-defined; the principle is to keep responsibilities legible.

---

# H.48 Cline “do not create wrapper soup” rule

Do not create:

```text
PanelWrapper
CardWrapper
SectionWrapper
VisualWrapper
DashboardShell
InnerPanel
PanelInner
PanelContent
```

for every `<div>`.

Create components only when:

- they have repeated behavior,
- they have stable semantics,
- they are explicitly part of the design system,
- or the phase names them.

Prefer simple markup for one-off layout.

---

# H.49 Cline debugging order

When a visual does not look right:

1. inspect computed CSS,
2. check the token variable resolves,
3. check container dimensions,
4. check flex/grid constraints,
5. check overflow,
6. check browser default styles,
7. only then modify component code.

Do not immediately add:

```text
!important
```

or arbitrary transform offsets.

---

# H.50 Cline debugging order for missing Tailwind classes

If a class does nothing:

1. confirm the class appears as a complete literal string in source,
2. confirm Tailwind v4 is scanning the file,
3. inspect generated CSS,
4. prefer static mapping,
5. switch to a canonical CSS variable if the value is runtime-driven.

Tailwind's documentation explicitly states that string interpolation does not generate dynamic utility classes. citeturn889556search1

---

# H.51 Cline debugging order for broken shadcn components

When a generated shadcn primitive looks wrong:

1. inspect the generated source,
2. identify its data attributes/variants,
3. replace its default color/radius/spacing values with AFL tokens,
4. preserve the interaction/accessibility implementation,
5. do not delete its semantic roles just to make styling easier.

Current shadcn documentation emphasizes that the component source is owned by the project and can be modified. citeturn423138search2

---

# H.52 Cline debugging order for React Flow

When the loop diagram is misaligned:

1. confirm node IDs are stable,
2. confirm the node positions,
3. confirm source/target handles,
4. confirm edge direction,
5. confirm `fitView`/viewport state,
6. confirm CSS around `.react-flow`,
7. only then adjust the dimensions.

Never “fix” edge geometry with arbitrary page transforms.

React Flow's current handle documentation confirms that explicit source/target handles and handle IDs control edge attachment points. citeturn830860search1

---

# H.53 Cline debugging order for charts

When a chart is blank:

1. log/inspect data shape,
2. verify all required numeric values are finite,
3. verify axis keys match exact response fields,
4. verify container width/height is non-zero,
5. verify the chart library is imported only in the page that needs it,
6. inspect accessibility layer,
7. only then adjust chart props.

Do not invent chart data just to make the graph render.

---

# H.54 Required frontend test behaviors by page

## Home

Must prove:

```text
loads
nav works
loop animation runs once
loop settles
KPI values render
command palette opens
```

## Identify

Must prove:

```text
25 attacks render
category filter
status filter
search
drawer
URL pre-open
Generate action only for wired profiles
```

## Generate

Must prove:

```text
form validates
attack selection
generation pending state
success result
fallback
transaction handoff
user medians state
```

## Defend

Must prove:

```text
23-field payload
7 primary fields
advanced disclosure
prediction
probability
threshold tick
SHAP
metrics table
business thresholds
heatmap
PR curve
```

## Loop

Must prove:

```text
run
SSE events
diagram active state
timeline
metric deltas
history
disconnect state
cleanup
```

---

# H.55 Testing contract for URL handoffs

Automate:

```text
/identify?attack_id=SE-001
```

and assert:

```text
drawer open
SE-001 visible
```

Automate:

```text
/generate?attack_id=SE-001
```

and assert:

```text
attack field pre-selected
```

Automate:

```text
/loop?prefill=1cycle
```

and assert:

```text
max cycles = 1
```

Do not assert internal React state directly if the same behavior can be observed from the DOM.

---

# H.56 Test the actual user story, not only the DOM

The highest-value Playwright scenarios are:

```text
Home
→ Run the loop
→ Loop page opens with 1-cycle prefill

Identify
→ open SE-001
→ click Generate sample
→ Generate page prefilled

Generate
→ generate
→ go to Defend
→ generated transaction is loaded

Defend
→ predict
→ probability and SHAP appear

Loop
→ run
→ events appear
→ deltas update
→ history gains a row
```

These sequences are more valuable than dozens of isolated CSS assertions.

---

# H.57 Screenshot review rubric

Score each screenshot mentally on:

```text
Hierarchy
8/10+

Alignment
8/10+

Density
7/10+

Legibility
9/10+

Technical credibility
9/10+

Visual restraint
9/10+
```

The exact scores are not machine tests. They are a review heuristic.

The question is:

> Does this look like a specialized fraud-analysis instrument with evidence, or like a generic AI dashboard template?

The intended answer must be the former.

---

# H.58 Final “judge in three minutes” walkthrough

The finished application should support this natural flow:

```text
0:00
Home opens.

0:05
Judge understands:
Identify → Generate → Defend → Improve.

0:15
Judge sees:
1.06M+ transactions
25 attack vectors
real evaluation metrics

0:30
Judge opens Identify.
Finds AI-specific attacks immediately.

0:45
Judge opens a wired attack.
Clicks Generate sample.

1:10
Judge sees:
fraud narrative
materialized transaction
validation/drop behavior

1:30
Judge moves to Defend.
Scores the generated transaction.

1:50
Judge sees:
probability
threshold
SHAP
per-class performance
PR curve

2:20
Judge opens Loop.
Starts one cycle.

2:30+
Judge sees:
events
active loop leg
metric deltas
closed-loop improvement story
```

Do not optimize the UI for a “dashboard browse” where the judge has to inspect twenty cards before discovering the core loop.

---

# H.59 Final submission hardening

Before freeze, verify:

```text
No old Sidebar
No legacy token names in production UI
No gradient
No glass
No hover lift
No emoji
No fake metrics
No unresolved TODO(Phase
No console.log
No raw API fetch from feature components
No direct sibling-feature imports
No duplicate API clients
No duplicate attack taxonomy
No unhandled lazy route error
No SSE leak
No mobile horizontal page overflow
No missing deep-route refresh
No hidden 16 MODEL_COLS fields
No misleading “AI generated” label for rule fallback
```

---

# H.60 Repository-grounded facts to remember

The supplied project confirms:

```text
N_USERS in rule generator = 15,000
N_MERCHANTS = 1,000
simulation starts 2026-01-01
simulation horizon = 60 days
```

These are backend facts, not frontend KPIs.

Do not expose them just because they exist.

Expose only data that advances one of the five judging questions.

---

# H.61 Explicit “do not use” source files for visual decisions

These are useful for understanding history but should not be treated as the current visual source of truth:

```text
frontend-vision.md
docs/DESIGN_SYSTEM.md
legacy frontend source from frontend.zip
```

`docs/FRONTEND_VISION.md` and this build bible control the final design direction.

The reason for this explicit list is to prevent an agent from seeing the old light-mode design-system document or legacy dashboard and “helpfully” reintroducing the wrong system.

---

# H.62 Official web research notes — 2026-08-29

The following implementation guidance was checked against current official documentation.

## React

`React.lazy` defers loading until the component is rendered and should be declared at module scope. Rejected lazy imports propagate to the nearest Error Boundary. citeturn957766search0

`<Suspense>` is the correct boundary for showing fallback content while a lazy component is loading. citeturn957766search5

## TanStack Query

Queries receive an `AbortSignal`, enabling request cancellation when integrated with `fetch`. citeturn515681search3

Mutations expose `idle`, `pending`, `error`, and `success` lifecycle state, and related queries should generally be invalidated after successful mutations when cached data is now stale. citeturn515681search13turn515681search0

## Tailwind v4

Tailwind's current theme-variable system is based on `@theme`, and those variables participate in generated utilities. citeturn515681search12

Tailwind scans source as text and cannot reliably generate dynamic class fragments produced via string concatenation/interpolation; static class maps or CSS variables are the safe approach. citeturn889556search1

Tailwind's responsive model is mobile-first. citeturn889556search0

## shadcn/ui

shadcn is source distribution rather than an opaque runtime component library, so copied component source should be treated as project-owned and restyled to the AFL system. citeturn423138search2

The current CLI supports adding components, and `components.json` configures how those components and aliases are managed. citeturn423138search0turn423138search6

Current shadcn form guidance uses React Hook Form + Zod + `zodResolver`. citeturn957766search10

Current shadcn documentation has evolved around Toast/Sonner/Base UI, so keep the project's Toast API stable rather than coupling feature code to the registry's internal choice. citeturn957766search1turn957766search4

## React Flow

Current React Flow documentation confirms viewport control (`fitView`, min/max zoom) and the accessibility APIs for keyboard-focusable nodes and edges. citeturn515681search11turn830860search0

Current handle documentation confirms explicit source/target handle positions and handle IDs as the mechanism for controlling edge attachment. citeturn830860search1

## Recharts

Current Recharts documentation exposes accessibility support through `accessibilityLayer`. citeturn515681search15

## Motion

Current Motion documentation recommends `useReducedMotion` / `MotionConfig` to respect device motion preferences and explains that reduced motion can disable/simplify movement rather than merely slow it. citeturn515681search1turn515681search2turn515681search4

## Playwright

Current Playwright supports projects for multiple browsers/devices and a `webServer` configuration to start a development server automatically before tests. citeturn515681search10turn515681search7

## Accessibility standards

WCAG 2.2 adds explicit criteria around focus visibility, focus not being obscured, dragging, and minimum target size. citeturn830860search3turn957766search12

---

# H.63 Source-to-decision map for future agents

| Question | First source to inspect | Secondary |
|---|---|---|
| Which page owns this? | Phase 0.2 + page phase | `docs/FRONTEND_VISION.md` |
| What visual token? | Appendix D | This Appendix H.2 |
| What API shape? | Appendix C/E | This Appendix H.2/H.29 |
| What model field? | Appendix B | `src/config.py` |
| How is prediction actually implemented? | `src/fraud_model/inference.py` | API adapter |
| How is generation actually implemented? | `src/generator/llm_generator.py` / `rule_generator.py` | Phase 7 |
| How does the loop actually work? | `src/models/feedback_loop.py` | Phase 9 |
| Which numbers are trusted? | Appendix F / `CHANGELOG.md` | current API response |
| Which old UI can be copied? | **None** | legacy frontend is historical only |
| How do I verify? | phase acceptance criteria | Phase 10 |
| What if two docs disagree? | authority order in H.1 | `PROGRESS.md` |

---

# H.64 Final agent instruction

Before declaring any phase complete, answer these five questions from the actual running app:

```text
1. Does the feature render?
2. Does the feature work with demo fixtures?
3. Does the feature respect the locked design language?
4. Does the feature behave correctly at 390×844?
5. Did I verify the behavior in the browser rather than assuming it from code?
```

If any answer is “no,” the phase is not complete.

Do not mark a phase complete because TypeScript compiles.

Do not mark a phase complete because the component “looks right in code.”

Do not mark a phase complete because a screenshot exists.

The acceptance standard is the running product.

---

# H.65 One-page implementation summary for Cline

```text
ARCHITECTURE
Vite + React 19 + TS + React Router 7
TanStack Query for server state
Zustand only for explicit cross-cutting state
shadcn-owned primitives
Recharts for charts
React Flow for loop diagram
Motion/Framer Motion only for loop + counters

VISUAL
Dark cyber-command
No gradients
No glass
No sidebar
No decorative grain
Borders over shadows
8px rhythm
Cyan is restrained
Mono for data/IDs
Space Grotesk for display
Inter for normal UI

API
Never fetch inside a component
Use getApiClient()
Demo and live must share one interface
Normalize JSON/SSE in the API layer
Use fetch+ReadableStream for POST SSE
Abort streams on unmount/supersession

STATE
TanStack Query = server data
local React state = feature UI state
Zustand = only approved cross-cutting values
URL params = one-time navigation hints

FORMS
React Hook Form + Zod
@hookform/resolvers required
All 23 model columns sent to predict
7 primary + 16 advanced
No fake categorical values

ROUTES
/
/identify
/generate
/defend
/loop

RESPONSIVE
Desktop target 1440×900
Mobile target 390×844
Mobile-first
No page-level horizontal overflow
Tables may scroll inside their own container

ACCESSIBILITY
Visible focus
Semantic labels
Keyboard-first interactions
Accessible charts
Accessible React Flow
Polite live updates
24px target-size baseline where applicable
No color-only meaning

QA
Playwright × Chromium/Firefox/WebKit
Desktop + mobile
Console errors fail
Screenshot every page
Axe critical/serious = zero
Lighthouse floors from Phase 10
Cold-start run twice in Phase 11

MOST IMPORTANT
Do not improvise a generic dashboard.
Do not revive the legacy frontend.
Do not invent API fields silently.
Do not fake numbers.
Do not fake generator support for conceptual attacks.
Do not hardcode live thresholds.
Do not hide the 16 advanced model fields.
Do not let SSE subscriptions leak.
Do not declare success without browser verification.
```

---

## H.66 End of additive clarification appendix

This appendix is intentionally placed **after Phase 11** so the original phase text remains byte-for-byte preserved. It exists to remove ambiguity discovered during repository audit and current-library research; it does not add a Phase 12 and does not change the project's 12-phase sequence.

---

# H.67 Canonical Anti-"AI-Generic" Checklist (numbered)

This closes a real gap in the document as combined: several phase prompts and appendices above cite specific, numbered items from "The Anti-'AI-Generic' Checklist" as though it exists as one enumerated list "above" — e.g. `.glass` is called out as "anti-pattern #6" (near line 775) and Phase 5's DO-NOT list cites "anti-pattern #10" for equal-width cards (near line 1517) — but no single section in this combined document actually spells out all ten-plus items end to end. They're scattered across H.5.3, H.5.4, H.27, H.28, and inline phase notes. Nothing below is a new decision; every item already exists elsewhere in this document and is locked. This section only gathers them into the one place every phase prompt already assumes exists, numbered so the two existing by-number references above resolve correctly, so a fresh agent doesn't have to reconstruct the list from memory or skip the audit because the citation dead-ends.

1. No CSS gradient anywhere — background, text-fill, or border (H.5.4).
2. No `backdrop-filter: blur(...)` / glassmorphism panel (H.27).
3. No decorative particle effects, floating orbs, or ambient background animation (H.27, "random glowing dots").
4. No glow or blur effect on hover, active, or pulse states — state changes are opacity, border-color, or background-color only, never a blurred glow (Phase 3's loop-diagram `pulseGlow` decision).
5. No `hover:scale`, `hover:-translate-y`, or hover-lift transform on cards or buttons (H.27).
6. No glass card variant, inherited or otherwise (H.28 legacy-quarantine list).
7. No emoji as UI iconography — Lucide only, routed through `design-system/icons.ts`.
8. No `shadow-*` box-shadow used for elevation — elevation is borders and background-color steps only ("borders over shadows").
9. No sidebar, mega-menu, or nav pattern beyond the five flat top-nav items (Phase 5 DO-NOT list; H.28's "Sidebar" legacy-quarantine entry).
10. No perfectly equal-width card grid where the underlying content has a real priority order — deliberate asymmetric widths (e.g. Home's 1.25× Defend/Loop cards) signal an actual information hierarchy instead of a generated template (Phase 5 DO-NOT list).
11. No more than one saturated cyan primary button competing for attention within the same panel (H.5.x, "Do not allow the CLI to become the source of truth..." section's sibling rule near line 3723).
12. No mixed, ad hoc corner radii on one screen — only the locked radius hierarchy (`--radius-card`, `--radius-input`, `--radius-node`, and `rounded-full` for genuine pills/status dots) (H.5.3).

Phase 10's grep-based anti-pattern audit (H.27) should treat this numbered list as its checklist and check off each item explicitly by number in that phase's `PROGRESS.md` entry, rather than re-deriving the list from memory or from a partial grep pass.

---

# H.68 Premium Execution Addendum — numeric and iconographic precision

Two small, concrete additions, genuinely new rather than gathered from elsewhere, aimed at the specific pixel-level details that separate a Wiz/Datadog/Darktrace-grade dashboard from a template-grade one wearing the same color palette. Neither changes any locked color, spacing, or motion decision above — both are additive refinements to components that already exist in the plan (Phase 3's `KpiTile` and `PerFraudTypeTable`, and the Lucide icon wrapper from Phase 0).

1. **Tabular numerals on every live or updating number.** Every KPI tile, `CountUp` instance, and numeric table cell (precision, recall, PR-AUC, FPR, transaction counts) should render with tabular/lining figures (`font-variant-numeric: tabular-nums`, or Tailwind's `tabular-nums` class) rather than each font's default proportional digits. Without this, a digit changing from a narrow character (1) to a wide one (8) during a count-up or a live refresh visibly nudges surrounding layout by a pixel or two — a small flaw, but exactly the kind that reads as "unfinished" even when the color and spacing are otherwise correct. Apply it once, at the `KpiTile` and `PerFraudTypeTable` component level in Phase 3, so no later page has to remember to add it per usage.

2. **One icon stroke-weight and two icon sizes, app-wide.** Lucide's stroke width is variable per call site by default; lock it once in the icon wrapper (`design-system/icons.ts`) — e.g. a fixed `strokeWidth={1.75}` — instead of leaving each usage to inherit whatever default it happens to get. Standardize on exactly two icon sizes for the whole app: one for inline/label icons (nav, buttons, table headers) and one for the larger pillar/nav icons already specified at 88×88px (Phase 5). Inconsistent stroke-weight or ad hoc icon sizing across pages is one of the more common tells that a UI was assembled page-by-page rather than designed as one system — and one of the easiest things for a later phase to silently drift on if it isn't locked centrally now.

Everything else in the locked visual system (dark cyber-command base, restrained single accent, mono for data, no gradients/glass/glow) already matches the register of the reference sites this project is aiming for. These two items are precision, not direction — the kind of detail that shows up on screen in Phases 6–9 rather than only in the spec.

---

# H.69 — Why Phase 9.5 exists and why it was inserted rather than folded in

This document was extended a second time after H.66–H.68 were added, in
response to a direct request to steer the finished pages toward the
visual register of Stripe/Darktrace/Wiz/Datadog rather than a generic
AI-dashboard template. The natural places to add that work would have
been Phase 10 or Phase 11, since they're the only "upcoming" phases at
the point this request arrived — but both explicitly forbid it in their
own locked text:

- Phase 10's own PROJECT CONTEXT states: "This phase produces zero new
  features and zero new visual components," and its DO NOT list opens
  with "Add, remove, or restyle any component."
- Phase 11's DO NOT list states: "Add any new page, component, token, or
  dependency," and frames any late-surfacing design need as something to
  flag for the user's explicit decision, not decide unilaterally.

Sprinkling motion/visual work into either phase would have required
silently contradicting text this document already locks elsewhere, which
H.1's authority order treats as exactly the kind of thing to flag rather
than paper over. Inserting a new phase between 9 and 10 was the only
option that adds the work without rewriting either phase's already-locked
scope. It's named "9.5" rather than renumbering 10 and 11 to 11 and 12 so
that every existing cross-reference to "Phase 10" and "Phase 11" elsewhere
in this document (there are many) stays correct without a find-and-replace
across the whole file. See the addendum on "0.2 Phase Sequencing" above
for the one-sentence acknowledgment that this makes the plan 13 phases in
practice.

Nothing in Phases 0–9's own text was altered to make room for this. Phase
9.5 is purely additive, exactly like H.67 and H.68 before it.

---

# H.70 — Dangling "Page Specification" cross-reference ledger

This closes a real, recurring gap discovered while reviewing the combined
document for places a fresh agent could stall. Five phase prompts each
instruct the agent to "re-read the [Page] Page Specification above in
full" before starting:

| Phase | Phrase used | Line (approx.) |
|---|---|---|
| Phase 5 (Home) | "Home Page Specification" | ~1465, ~1528 |
| Phase 6 (Identify) | "Identify Page Specification" | ~1578, ~1589 |
| Phase 7 (Generate) | "Generate Page Specification" | ~1723 |
| Phase 8 (Defend) | "Defend Page Specification" | ~1891 |
| Phase 9 (Loop) | "Loop Page Specification" | ~2030 |

None of these five named sections exist anywhere in this combined
document as their own headed section — there is no "## Home Page
Specification" heading, and the same is true for the other four. This
almost certainly reflects content that existed in one of the pre-merge
source documents (`docs/FRONTEND_VISION.md` / `frontend-vision.md` /
`frontend_instrcutions.md` in the wider repo) but wasn't carried into this
compiled build bible when it was assembled — the same class of gap H.67
already documented for "The Anti-'AI-Generic' Checklist," just five more
instances of it.

Practically, this has not blocked Phases 5–9 from being built, because
each phase prompt's own numbered task list, DO-NOT list, and acceptance
criteria are self-contained and don't actually depend on content from the
missing section to be followed correctly — the phantom reference reads as
"go re-read the context you were just given" rather than pointing to
information that exists nowhere in the agent's context at all. But an
agent that takes the instruction literally and searches this document for
a section by that exact name will not find one, and may reasonably stall
or hallucinate a resolution to fill the gap.

**Rule for every future agent, including whoever runs Phase 9.5 or
finishes Phase 9:** if you're told to "re-read [X] above" and cannot find
a section with that exact name, treat the phase's own inline CONTEXT/TASK/
DO-NOT/ACCEPTANCE-CRITERIA block as the complete and authoritative
specification for that page. Do not assume missing, unstated requirements
exist in a section you can't find, and do not silently invent content to
fill the gap — if something is genuinely ambiguous without the missing
section, resolve it the way H.2's contradiction ledger resolves every
other gap in this document: state the ambiguity plainly in `PROGRESS.md`
and make the smallest reasoned decision, rather than guessing quietly.

---

# H.71 — Motion & React Bits execution reference for Phase 9.5

This condenses `AFL_Motion_ReactBits_Curated_Agent_Guide.md` — a
standalone research pass against current motion.dev and reactbits.dev
documentation, dated the same day as H.62's research notes — into the
governing reference for Phase 9.5. It does not replace the source
document; read the source in full before Phase 9.5 begins if it's
available in the repo. This section exists so Phase 9.5 has a citable,
in-document spec the way every other phase cites Appendix D or H.2,
rather than an external file a future agent might not have open.

**Governing directive (verbatim from the source, §20):** use Motion as
the primary animation engine and React Bits only as a selective source of
component mechanics — never as the project's visual style. Preserve the
AFL design system exactly (dark technical surfaces, restrained semantic
colors, borders over shadows, locked radii, mono technical values, no
gradients/glass/glow/particles/hover-lift/decorative backgrounds). Add
animation only when it communicates a real product state change. The
final test is not "does this look impressive" but "does this look like a
specialized fraud-analysis instrument with evidence, or like a generic AI
dashboard" — the required answer is the former.

**§3 Library roles:** Motion = animation engine (state transitions,
enter/exit, layout changes, staged reveals, event-driven transitions,
subtle hover/focus/press feedback). React Bits = narrowly curated
component-mechanic reference only, never the source of AFL's visual
language — most of its catalog (particles, gradients, glass, glow,
cursors, shaders, 3D cards, distortion) is explicitly out of scope for
this project.

**§4/§5 Tier A Motion allowlist:** `layout` (highly approved — expanding/
collapsing disclosures, reflow, size changes that reflect a real state
transition), `AnimatePresence` (approved — drawers, conditional panels,
success/error transitions; opacity + small directional movement only, no
bounce/scale/rotate), `stagger` (approved with strict limits — a short
group revealing together, 40–80ms succession, never a cascade across a
large list), `useInView` (one reveal per section, not per child),
`useReducedMotion`/`MotionConfig` (mandatory wherever motion exists),
`useAnimate` (for event-driven choreography, primarily Loop), restrained
`whileFocus`/`whileTap`. `layoutId` is conditional — only where "this is
the same object, now viewed in more detail" is genuinely true, never as a
shared-element showcase effect.

**§6/§7 explicitly rejected regardless of technical quality:** page
curtains/cinematic transitions, magnetic cursor/button interactions,
parallax, 3D/tilt/coverflow, confetti, animated border beams, decorative
springiness/bounce/overshoot, glassmorphism, gradient text or backgrounds,
aurora/beams/galaxy/particle/dot-field/plasma backgrounds, glow (border
or cursor), spotlight/chroma-grid hover effects, decrypted/scrambled/
glitch text on normal UI copy, fake terminal/scanner/radar/CRT overlays,
magic-bento grids, and carousel/coverflow treatment of core evidence
content. React Bits' Animated List is the one component judged a strong
enough fit to use directly (for the Loop `CycleTimeline`), and only with
its hover/click/auto-add demo behaviors disabled and real event order
preserved.

**§8 High-value use cases (cited by letter throughout Phase 9.5):**
A. Loop timeline event arrival (very high priority) — real event → row
fades/short-slides in → settles, no loop, no bounce.
B. Loop metric delta update (high) — tile keeps position, value updates,
brief opacity/background emphasis only, never scale/pulse/flash.
C. Active LoopDiagram leg transition (very high) — subtle node/edge state
change, geometry and dimensions unchanged, no glow/particles/beams.
D. Generate result arrival (high) — coordinated but immediate reveal
(transcript → transaction → diff), never delaying real data behind
theatrics.
E. Defend prediction result (high) — gauge settles to its real value,
SHAP waterfall enters once, no fake "thinking" after the backend has
already responded.
F. Advanced-fields disclosure (medium-high) — `layout` animation on the
7→23 field expansion.
G. Identify drawer (medium) — Sheet open/close feels intentional, no
galleries or shared-element drama.
H. Filter results (medium, use with caution) — a tiny `layout` reflow may
help; a visible cascade across 25 rows is a regression, not polish.
I. Home methodology/evidence reveals (medium) — one `useInView` reveal per
section, not per child.

**§9 Strict motion budget per page (do not exceed):** Home — LoopDiagram
intro + settled pulse, CountUp, a small number of section reveals; no
cards sliding in, no animated backgrounds. Identify — drawer enter/exit,
optional subtle table reflow; otherwise static. Generate — skeleton→result,
transcript row arrival, compact dialog entrance; no typing effect, no
fake LLM thinking, no shimmer. Defend — result panel entrance, advanced-
fields layout, subtle metric update; no continuously animated charts, no
speedometer gauge, no fake scanning. Loop — the most animation-rich page
by design: live active-leg transition, timeline entry, KPI delta update,
history-row insertion, disconnect-state transition.

**§13 Twenty-question fitness check** (apply to any animation this phase
considers adding that doesn't map cleanly to an §8 use case): does it
communicate a real state change; is it reversible/interruptible; does it
respect `prefers-reduced-motion` with a correct end-state; does it avoid
adding a new dependency or duplicating an existing capability; does it
make the interface feel more like a security/fraud instrument; would
removing it make the feature *less* understandable; does it delay access
to real data; is it worth the added complexity. If removing the animation
would not make the feature less understandable, the animation probably
does not belong (source §13, item 18).

**§19 What "polished" means for AFL (do not substitute "more effects"
for this):** consistent spacing, precise alignment, stable dimensions,
clean hierarchy, crisp typography, predictable interactions, good empty/
loading/error states, clear active states, no layout jumps, responsive
behavior, accessible focus, real data appearing without delay, meaningful
motion only where state changes, technically credible visualization,
visual restraint. A polished AFL interaction should leave the user
thinking "I understand what just happened," not "that animation was
cool."

**§14/§15 Dependency discipline:** prefer the eight dependencies already
in the project (Motion, React Flow, Recharts, cmdk, React Hook Form, Zod,
TanStack Query, Zustand, Lucide) over installing anything new. If a React
Bits component is adapted, inspect its source, strip decorative behavior,
rewrite its styling to AFL tokens, preserve accessibility and existing
component APIs, and test both viewport classes and reduced motion before
counting it done — never install a React Bits component's underlying
runtime dependency (GSAP, OGL, Three, or another rendering stack) without
an extraordinary, product-specific reason, which does not currently exist
for this project.

Everything else in the source document (§10's full "visual rules override
library defaults" list, §11's radius/color/typography integrity notes,
§12's "existing AFL components take precedence" list, and §17's full
Tier A/B/C/D shortlist) is consistent with and reinforces H.5–H.10, H.27,
and H.67 already locked in this document — nothing in the source
document's own text asks for a visual decision that contradicts anything
already locked above. Where the source document is silent on a point this
document already decided, this document's decision governs (H.1's
authority order).
