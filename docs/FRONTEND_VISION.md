# Frontend Vision — Adversarial Fraud Lab (AFL)
**Locked design doc · code reference, not a spec to re-derive**
Written: Aug 28, 2026 · Deadline: Aug 31, 2026 (3 days)
Owner: Cline (acting on user decisions) · Reviewer: User

---

## 0. TL;DR — the five locked decisions

| # | Decision | Value |
|---|---|---|
| 1 | **Stack** | **C. Next.js + shadcn/ui + Tailwind + Recharts, FastAPI backend, server-state via TanStack Query** (the heavy lift; we accept 1.5-2 days of frontend time because the prototype is the star) |
| 2 | **Live demo** | **All four in priority order**: (1) single-tx prediction + SHAP waterfall, (2) side-by-side flagged case study, (3) "generate a fraud -> predict on it" closed loop, (4) mini closed-loop run with PR-AUC delta |
| 3 | **Aesthetic** | **B. Dark cyber-command** (Wiz / Darktrace / CrowdStrike lineage). Deep navy + charcoal, neon green/amber/red status, monospace numerics, subtle grid texture, no glassmorphism, no neon-rainbow gradients |
| 4 | **Closed loop** | **A + B combined**: literal 4-node loop diagram on the homepage *and* a "Run the loop" button that streams status |
| 5 | **Scope bias** | **A. Prototype is the star, docx is a compact walkthrough that points to the prototype**. ~70% polish to prototype, ~20% to docx, ~10% to repo hygiene |

Plus two new locks from this conversation:
- **The Wiz "AI-Powered Code-to-Cloud Defense" animation style is the named reference** for the homepage hero. We copy that exact narrative arc (input surface -> attack progression -> detection response -> closed-loop improvement), not the visual.
- **Project name stays "Adversarial Fraud Lab (AFL)"** — already in `HACKATHON_MASTER_PLAN.md`, no rename.

---

## 1. What we're actually building and why

### 1.1 The judge audience and the 3-minute window
The brief is read literally: five scoring axes — **diversity, fidelity, detection efficacy, novelty, real-world feasibility** — and three deliverables: code repo, docx, web prototype. A judge has 3 minutes with each submission. Every screen in the prototype must answer one of the five scoring questions, or it doesn't earn its place. Decorative screens lose.

### 1.2 What already exists in this repo
- **Identify**: `src/identify/attack_profiles.py` (4 profiles wired to generation) + `docs/ATTACK_TAXONOMY.md` (25 attacks, 5 categories A-E, feasibility ratings).
- **Generate**: `src/generator/rule_generator.py` (1.06M-row rule-based fraud injection, 7 fraud types, anti-leakage audited) + `src/generator/llm_generator.py` (LLM writes a fraud *narrative*, judge model validates, then `materialize_llm_transaction` turns the conversation into a row).
- **Defend**: `src/fraud_model/inference.py` (`FraudInferenceService` with `predict_single`, `predict_batch`, `get_business_metrics`, `health_check`). Tier 1 XGBoost PR-AUC ~0.80. Tier 2 Isolation Forest PR-AUC ~0.006, deliberately documented as near-random. `src/models/explain.py` has SHAP but only writes static PNGs.
- **Feedback loop**: `src/models/failure_analyzer.py` (evasion patterns from misses) + `src/models/feedback_loop.py` (synthesizes adversarial rows, retrains, compares val F1). Real numbers: val recall 0.8200 -> 0.8467, FN 34 -> 32.
- **Web prototype (broken)**: `app.py` is a single-file Streamlit with a stranded `with col2:` after the footer and a "Live Demo" tab that does `if amount > 5000: risk_score += 0.3` instead of calling the model.

### 1.3 What changes from prior docs
- **Committing to dark cyber-command aesthetic** (prior doc left it as a default-to-light suggestion).
- **Locking the homepage as a 4-node loop diagram** (prior doc treated it as "later").
- **Pushing the live "run the loop" button to second priority on the homepage** (not a "later" thing — it's the wow moment).
- **Allocating 70% of 3 days to the prototype, not 50%**.

---

## 2. The aesthetic system — Wiz / Darktrace / CrowdStrike lineage

### 2.1 Why this aesthetic, in one paragraph
Your three named references (Wiz, Darktrace, CrowdStrike) converge on **the visual language of a security operations center**. Light-mode "Stripe-style" financial SaaS is what every other fintech team will ship. Dark cyber-command is a differentiator that is also *true* to the project's subject (red team / blue team). It also hides the "this is a student project" tell better than light mode, because dark UIs are more forgiving of slight proportions and color drift.

### 2.2 Color tokens (locked)

```
--bg-base          #0A0E1A   /* page background, deep navy-black */
--bg-panel         #0F1626   /* card / panel background */
--bg-elevated      #161E33   /* hover, focused, modals */
--bg-grid          #0D1322   /* subtle grid texture layer */

--border-subtle    #1F2A44
--border-strong    #2E3D5F

--text-primary     #E6ECFF
--text-secondary   #8B9DC3
--text-muted       #5A6B8A
--text-mono        #B8C5DD   /* IDs, hashes, tx_ids */

--accent-cyan      #00D4FF   /* brand accent, links, focus rings */
--accent-cyan-dim  #0088AA   /* hover/disabled */

--status-safe      #00FF88   /* green, "legit" / pass */
--status-warn      #FFB800   /* amber, "review" / low conf */
--status-threat    #FF3D5A   /* red, "fraud" / high conf */

--loop-attack      #FF6B35   /* the "Generate" leg */
--loop-defend      #00D4FF   /* the "Defend" leg */
--loop-identify    #B47AFF   /* the "Identify" leg */
--loop-improve     #00FF88   /* the "feed back" leg */
```


### 2.3 Typography stack (locked)

```
--font-sans     "Inter", system-ui, -apple-system, sans-serif   /* UI, body, labels */
--font-mono     "JetBrains Mono", "Fira Code", monospace       /* IDs, amounts, hashes, SHAP values */
--font-display  "Space Grotesk", "Inter", sans-serif           /* hero, large numerals */
```

**Why monospace for amounts and IDs:** the eye reads them as *data* not *text*, and it visually separates the "this is a number" parts of a transaction row from the "this is prose" parts. Sift and Grafana do this for the same reason.

**No emoji, no decorative icons in body copy.** Icons only in the nav and the loop diagram, from a single icon set (Lucide — shadcn default, free, consistent stroke weight).

### 2.4 Layout primitives (locked)

- **8px grid.** Every spacing value is a multiple of 8 (4 only inside table cells).
- **Max content width:** 1280px on the homepage, full-bleed for the loop diagram, 1024px on docs-style pages.
- **Panel radius:** 8px for cards, 4px for inputs, 0px for the loop diagram nodes (sharp = technical).
- **Shadows:** none. Borders only. The "depth" comes from `--bg-elevated` on hover, not from `box-shadow`. This is the "blueprint, not app" feel.

### 2.5 Motion language (locked, sparse)

**The rule: one orchestrated moment per page, not scattered micro-interactions.**

- **Homepage hero** (locked): the 4-node loop diagram animates once on mount, ~2.4s total, with each leg lighting up in sequence: Identify -> Generate -> Defend -> Improve. After the first pass, each node pulses softly in its assigned color at a 4s cycle. This is the "AI-Powered Code-to-Cloud Defense" pattern you liked from Wiz, translated to our loop.
- **Number counters** (used in KPI cards and metric tiles): count up from 0 to target value over 1.2s on first viewport entry. Used everywhere, but only one count-up animation visible at a time (the one in the current scroll viewport).
- **Chart reveals:** bars/lines draw in left-to-right over 600ms on mount. No bouncing, no overshoot, no spring physics. Easing: `cubic-bezier(0.22, 1, 0.36, 1)`.
- **Hover states:** 150ms color transition on borders and text. No scale transforms on cards (scaling on hover is the most common "AI dashboard" tell).
- **No spinners** anywhere. Use skeletons (1.5s pulse on `--bg-panel` -> `--bg-elevated`) for loading states. The home page's loop-diagram pulse serves as a global "system is alive" indicator.

### 2.6 Anti-patterns we explicitly forbid

- No `bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400` hero. The single brand color is cyan, used sparingly.
- No "3D rotating card on hover." No parallax. No glassmorphism (`backdrop-blur` over translucent panels).
- No Tailwind default colors (`bg-blue-500` etc.) — every color must come from a token in §2.2.
- No more than one chart library (Recharts). The chart color set is exactly the four `--loop-*` tokens + `--status-safe` + `--status-threat`.
- No Lottie / Framer-motion for the small stuff. Motion (formerly Framer Motion) is used only for the homepage loop and the number counters. Plain CSS transitions for everything else.

---

## 3. Page-by-page specification

### 3.0 Global chrome

- **Top nav** (sticky, 56px, `--bg-panel` with bottom border): AFL logomark on the left, then 4 nav items (Identify · Generate · Defend · Loop), then on the right a "System status" pill (green dot + "Online · 1.06M tx") and a "Run the loop" button (cyan outline, 32px height, opens the §3.5 drawer).
- **Footer** (3 columns, `--bg-panel`, top border): left = "Adversarial Fraud Lab · Mastercard Innovation Challenge 2026", center = "Built on a 1,064,963-transaction adversarial dataset (0.115% fraud rate, anti-leakage audited)", right = three small links (Methodology, GitHub, Contact).
- **No sidebar.** The 4 nav items are enough; the loop drawer handles everything secondary.

### 3.1 Home — `/`

The single most important page. Judges land here first. Must answer "is the closed loop real" within 5 seconds.

**Layout (top to bottom):**

1. **Hero (full-bleed, 100vh, no scroll-jacking):**
   - Top-left: AFL logomark (32px) + "Adversarial Fraud Lab" wordmark in `--font-display` 24px.
   - Centered headline (max-width 720px): "The AI that learns fraud by *becoming* a fraudster." in `--font-display` 56px / 64px line-height / weight 600. The word "becoming" is in `--accent-cyan`.
   - Sub-headline (max-width 640px): "Closed-loop red team / blue team for GenAI-powered payment fraud. We identify emerging attacks, generate them at scale, defend against them, and feed every miss back into the next generation."
   - Below the headline, the **4-node loop diagram** (locked — see §3.1.1). This is the centerpiece of the entire site.
   - Below the loop: a single row of 4 KPI tiles (count up on mount): "1,064,963 transactions" · "25 attack vectors catalogued" · "0.115% fraud rate (real-world)" · "0.807 PR-AUC (test set)". These are the actual numbers from the repo — no fake stats.
   - Bottom-right of the hero: a "Run the loop ->" button (filled cyan, 40px height, opens the §3.5 drawer pre-loaded to a 1-cycle run).

2. **"The closed loop, in four stages"** (next 80vh):
   - 4 horizontal cards, each 320px wide, gap 24px, with the loop leg color as a 4px top border.
   - Each card: icon, leg name in `--font-display` 24px, one-sentence description, a "Try it ->" link that goes to the relevant page.

3. **"Built on real attacks"** (next 60vh):
   - Three columns: "Identify" (mini preview of the taxonomy browser — 5 most severe attacks, click to see all), "Generate" (a single live "Generate an attack" widget that runs the LLM path or a rule-based fallback), "Defend" (a single live "Predict on this transaction" widget that calls `predict_single` and shows the probability).
   - Each column is a fully working miniature of its dedicated page. This is the "before you scroll, you've already seen all three pillars" treatment.

4. **"Numbers that hold up"** (next 60vh):
   - Per-fraud-type PR-AUC table (recovered from `data/processed/evaluation_reports/...` or recomputed by a one-off eval script). 7 rows. Each cell has a micro-bar showing the value relative to the column max.
   - Honest about Tier 2's near-random number — that's part of the story, not a weakness.

5. **"The loop in motion"** (next 80vh):
   - A static illustration (SVG, not a video) of the loop in its "after 5 cycles" state — a small narrative block: "Cycle 1: 1,060 fraud tx, 0.794 PR-AUC, 84 false negatives. Cycle 5: 1,290 fraud tx, 0.812 PR-AUC, 62 false negatives." Real numbers from a real run, or pre-baked but labeled.
   - This is the "if you only read one section, read this" of the page.


#### 3.1.1 The 4-node loop diagram (the centerpiece)

Fixed proportions: total width 480px, total height 480px, viewBox-based SVG so it scales.

```
            [IDENTIFY]
                ↓ (left side,  attack-orange)
       ↓                       ↑
[DEFEND] ←——  [IMPROVE]   [GENERATE]
 (cyan)        (green)       (purple)
```

Top: IDENTIFY. Right: GENERATE. Bottom: IMPROVE. Left: DEFEND. Arrows flow clockwise. Each node:
- 96px x 96px rounded square (8px radius), `--bg-panel` fill, 2px border in the leg color.
- Icon centered, 32px, in leg color.
- Label below, `--font-display` 16px, `--text-primary`.
- One-line tagline below label, `--text-secondary` 13px.

**Animation (locked, 2.4s total, plays once on mount):**
- 0.0s: all nodes at 0.2 opacity.
- 0.0-0.4s: IDENTIFY fades in, pulses once.
- 0.4-0.8s: arrow IDENTIFY->GENERATE lights up in attack-orange, traveling dot.
- 0.8-1.2s: GENERATE fades in, pulses once.
- 1.2-1.6s: arrow GENERATE->IMPROVE lights up in purple.
- 1.6-2.0s: IMPROVE fades in, pulses once.
- 2.0-2.4s: arrow IMPROVE->DEFEND lights up in green.
- 2.4s onward: DEFEND fades in last (so the eye lands on "we defend") and all nodes settle to a 4s soft pulse cycle, each in its own color. The traveling dot continues clockwise, one revolution every 8s, forever. This is the "the loop is alive" signal.

### 3.2 Identify — `/identify`

The taxonomy browser. Answers "diversity" and "novelty."

**Layout:**
1. **Header strip** (no full hero): page title "Attack Taxonomy" in `--font-display` 32px, subtitle "25 attack vectors across 5 categories. Each tagged Implemented / Partial / Conceptual with a feasibility rating and a mapping to the generation pipeline."
2. **Filter bar:** 5 category chips (A: AI Social Engineering, B: Synthetic Identity, C: Payment Rail, D: AI-Specific, E: Behavioral) + a status filter (All / Implemented / Partial / Conceptual) + a search input. Chips are colored with the leg color of the closest loop stage, not with random category colors.
3. **Attack list:** virtualized list (only ~25 items, so this is overkill, but read for the day-2 refactor). Each row: ID (SE-001 mono), name (16px), category chip, feasibility stars, status badge, a "->" that opens a right-side drawer with the full description and a "View in dataset" link that filters the Defend page's test set to that fraud_type.

### 3.3 Generate — `/generate`

The "see an attack being made" page. Answers "fidelity" and "novelty."

**Layout:**
1. **Header:** "Generate an attack" + subhead "The LLM writes a fraud *narrative*; a judge model validates it doesn't leak card data; we materialize the conversation into a transaction row that the rest of the system can train on."
2. **Two-column workspace:**
   - **Left (40%):** Controls. Pick an attack type (dropdown sourced from the taxonomy), pick a target user (a randomly chosen real user from the test set, or "random"), pick an urgency level (high/medium/low for AI-impersonation), then "Generate ->" button.
   - **Right (60%):** Live output. Three stacked panels, all in `--bg-panel`:
     - **Conversation transcript:** the LLM-generated pretext messages, with a small "✓ validated" or "✗ rejected — leaked card data" badge.
     - **Materialized transaction:** the resulting row, with all fields shown in monospace, the same data the Defend page would receive.
     - **Diff against normal:** small side-by-side showing the new row's feature values vs. the same user's median for amount, channel, hour, device_trust_age_days. This is the "fidelity" answer — we can show that the synthetic attack is realistic, not a caricature.

### 3.4 Defend — `/defend`

The "this is the model" page. Answers "detection efficacy." This is the Sift-style "embedded real dashboard" page.

**Layout:**
1. **Header:** "Defense model · Tier 1 XGBoost on a 23-feature engineered transaction representation" + subhead "Trained on 745,474 transactions (70% time-split), validated on 106,496, tested on 212,993. Class imbalance handled via `scale_pos_weight` and temporal holdout."
2. **Live single-tx predictor (hero of the page, 320px tall):** a single-row form on the left (amount, hour, channel, new_device, tx_last_1hr, device_trust_age_days, count_30d — these are the 7 features the model leans on most), a "Predict ->" button, and on the right a probability gauge (custom SVG, 0-100, with a tick at the chosen threshold 0.95) and a SHAP waterfall for the prediction.
3. **Per-fraud-type performance table:** 7 rows, columns: fraud_type, count, precision, recall, PR-AUC, FPR. Sourced from a `GET /api/eval/per-class` endpoint.
4. **Confusion-matrix-style heatmap** (small, 240px): rows = fraud_type, columns = predicted_label, cells = count, normalized by row. Color scale: `--bg-elevated` to `--status-threat`.
5. **PR curve** (Recharts, 400x300): test-set precision-recall curve with the operating point marked. This is the single chart judges will recognize as "oh, this is real."

### 3.5 Loop — `/loop`

The "watch the loop run" page. Answers "novelty" and "real-world feasibility." This is also the destination of the "Run the loop ->" button in the global nav.

**Layout:**
1. **Header:** "Run the closed loop" + subhead "Generate adversarial examples from the current model's misses, add them to the training set, retrain, measure the delta. Each cycle takes ~30-60s on the dataset's current scale."
2. **Cycle controls:** pick fraud_type focus (all / one), pick number of new attacks (50 / 100 / 200), pick max cycles (1 / 3 / 5), then "Run ->" button.
3. **Live progress pane (left, 60%):** a vertical timeline of cycle events. Each event has a timestamp, a 1-line description, and a delta. Events stream in as the cycle progresses.
4. **Cycle deltas (right, 40%):** the same KPI tiles as the home hero, but updated in-place after each cycle with the new values and a "+/-" delta chip.
5. **History (bottom):** a table of past runs in this session, with start time, duration, final PR-AUC, and "View artifacts" link that goes to the model's output directory.

---

## 4. The API contract (locked; implementation depends on this)

FastAPI app lives at `src/api/main.py`, mounted at `/api/*`. No endpoint should require auth in the prototype (judges won't have credentials), but every endpoint accepts an `?demo=true` query that returns canned data so the demo never breaks if the model fails to load.

```
GET  /api/health
  → { status: "ok" | "degraded", model_loaded: bool, data_loaded: bool, n_users: int }

GET  /api/attacks
  → full taxonomy list, 25 items, with category, status, feasibility, fraud_type, description

GET  /api/attacks/{id}
  → single attack, with the full description and a link to its generation config

POST /api/generate
  body: { attack_id: str, user_id: int | "random", urgency: "low"|"medium"|"high" | null }
  → { run_id, conversation: [...], transaction: {...}, accepted: bool, rejection_reason?: str }
  streams as SSE if the run > 2s; otherwise returns the full payload

POST /api/predict
  body: { transaction: {...} }   // FEATURE_COLS-shaped dict
  → { probability: float, threshold: float, label: "legit"|"fraud", shap: [{feature, value, impact}, ...] }

GET  /api/eval/per-class
  → [{ fraud_type, count, precision, recall, pr_auc, fpr }]

GET  /api/eval/pr-curve
  → { precision: [...], recall: [...], thresholds: [...], operating_point: {precision, recall, threshold} }

GET  /api/loop/history
  → [{ run_id, started_at, duration_s, final_pr_auc, n_cycles, n_new_attacks }]

POST /api/loop/run
  body: { fraud_type: "all"|"...", n_new_attacks: int, max_cycles: int }
  → streams SSE: each event is { type: "cycle_start"|"cycle_end"|"miss_added"|"metric_update", ... }

GET  /api/system/status
  → { online: bool, n_users, n_transactions, fraud_rate, pr_auc_test, last_retrain_at }
```


---

## 5. The 3-day sequence

The earlier vision doc had Days 1-2 on "taxonomy / generation / detection" with frontend as Day 3. That's backwards. **The prototype is the star** (decision #5). Revised sequence:

### Day 1 (today, 28 Aug) — foundation
- **Morning:** FastAPI skeleton (`src/api/main.py`) wrapping `FraudInferenceService.predict_single` and a thin read API over the eval results. Verify with `curl` + Postman that `/api/predict` returns a real probability on a hand-crafted transaction.
- **Afternoon:** Next.js app scaffold (App Router, shadcn init, Tailwind tokens from §2.2 wired in), homepage with the loop diagram (static, then animated), navigation, footer. End of day: a working homepage that loads, the loop animates once, the nav links go to placeholder pages.

### Day 2 (29 Aug) — the four pages
- **Morning:** Defend page (the strongest one — has the SHAP waterfall, the per-class table, the PR curve, the live predictor). This is the page judges will look at longest, build it first.
- **Afternoon:** Generate page (the LLM path *with a hard fallback to rule-based if LLM is unreachable* — never fail the demo on a flaky API). Then Identify page (pure read view over `docs/ATTACK_TAXONOMY.md` data).

### Day 3 (30 Aug) — the loop, polish, freeze
- **Morning:** Loop page (the "Run the loop" button wired to `/api/loop/run` with SSE or polling). The 5-cycle history view. The home page's "Numbers that hold up" section. The "The loop in motion" section. End of morning: every nav item works end-to-end.
- **Afternoon:** Playwright-screenshot every page at 1440x900 and 390x844 (mobile). Self-review against the §2 anti-patterns. Fix anything that violates them. Run the full demo twice from a cold start to catch race conditions.
- **Evening:** The docx walkthrough — a 6-page doc that opens with a screenshot of the homepage loop and points to the prototype for everything else. Repo `README.md` updated to start with the same screenshot. Freeze.

### Day 4 (31 Aug) — submit, don't refactor
- Only emergency fixes. Don't add features. Don't restructure.

---

## 6. What the implementation phase is forbidden from doing

Codified from the §2.6 anti-patterns and the §1.2 audit, so the implementer (Cline or otherwise) has no wiggle room:

- No new color outside the §2.2 tokens. No `bg-blue-500` or `text-purple-300` anywhere.
- No glassmorphism (`backdrop-blur`, `bg-white/10` over backgrounds). The aesthetic is opaque panels with borders.
- No emoji in body copy. Icons only via Lucide.
- No `motion` / `framer-motion` for anything other than the homepage loop and the count-up numbers. Plain CSS transitions elsewhere.
- No Lottie, no video, no animated GIFs. Static SVG illustrations only.
- No "powered by AI" / "intelligent" / "smart" copy. The system is intelligent or it isn't.
- No fake numbers. Every metric on the homepage is sourced from a real eval or recomputed. The "1,064,963 transactions" number is the actual row count from the current `data/raw/transactions.csv`.
- No shadcn `bg-gradient-*` anywhere.
- No sidebar. The 4 nav items are the IA.
- No Tailwind defaults — every color is a token, every spacing is a multiple of 8.
- No emoji icons. Lucide only.

---

## 7. Open questions this doc intentionally doesn't answer

These were *not* locked in this session and are flagged as "implementer's discretion" — each has a default below so nobody's blocked:

- **Icon set for the nav:** Lucide (default, free, consistent stroke weight, already shadcn default).
- **Chart library:** Recharts (locked in §1.3). Don't substitute without breaking the §2.6 rule.
- **Linting / formatting:** default Next.js + Prettier config. No bikeshedding.
- **Testing:** smoke tests only — the prototype isn't a product, it's a demo. One happy-path Playwright test per page is plenty.
- **Hosting for the demo:** local-only `npm run dev` + `uvicorn src.api.main:app`. No Vercel/Netlify deploy. The submission requires the repo, not a live link.
- **Live LLM calls during the demo:** rule-based fallback in `generate` is the default behavior. LLM path is enabled by env var (`AFL_USE_LLM=1`) and silently skipped on any error. The demo never fails because of a flaky LLM endpoint.

---

## 8. The one rule that overrides all others

**If a section of this doc is in tension with "ship something on time", ship on time.** Every screen above exists because it answers one of the five scoring questions (diversity, fidelity, detection efficacy, novelty, real-world feasibility). If a page is behind, cut from the bottom (Loop -> Generate -> Identify). The homepage, the Defend page, and the closed-loop animation are the only non-negotiables.
