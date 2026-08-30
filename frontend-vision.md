# Frontend Vision — Adversarial Fraud Lab (AFL)
### Research doc, not a spec. No code, no colors — just what to build and why.

Written: Aug 28, 2026 · Deadline: Aug 31, 2026 (**3 days**)

---

## 1. What's actually being judged

Read literally, the brief scores five things: **diversity** of attacks identified, **fidelity** of simulated attacks, **detection efficacy**, **novelty**, and **real-world feasibility**. Three deliverables carry that score: a GitHub repo, a `.docx` walkthrough, and — the one this doc is about — **a working web prototype with a presentable UI**.

That prototype isn't a demo of a demo. Given the timeline, judges will spend minutes with it, not the hours you've spent with the code. It is the artifact that has to *prove*, at a glance, that the closed loop (Identify → Generate → Defend → feed misses back into Generate) is real and not a slide. Every screen should answer one of the five scoring questions, or it's not earning its space.

Your own `docs/HACKATHON_MASTER_PLAN.md` ranks the web prototype **P2, "last."** I'd push back on that ordering: for a judge who has three minutes, the prototype *is* the evidence layer for the other four artifacts. The taxonomy doc and the metrics table only matter if something on screen makes them credible.

---

## 2. What the codebase actually is right now

I read the repo directly (`src/`, `docs/`, `app.py`, `config.py`, the graphify graph in `graphify-out/`) rather than taking the README's framing at face value. Here's the honest state:

| Layer | What exists | Maturity |
|---|---|---|
| **Identify** | `src/identify/attack_profiles.py` — 4 profiles wired to generation. `docs/ATTACK_TAXONOMY.md` — 25 attacks *described*, each tagged Implemented / Partial / Conceptual, with a feasibility rating | Two disconnected sources of truth |
| **Generate** | `src/generator/rule_generator.py` (rule-based injection per fraud type) + `src/generator/llm_generator.py` (1347 lines — LLM writes a fraud *narrative/pretext*, a judge model validates it doesn't leak full card data, then `materialize_llm_transaction()` turns the conversation into a transaction row) + `anti_leakage.py` | Real and substantial — genuinely more interesting than a typical hackathon generator |
| **Defend** | `src/fraud_model/inference.py` — `FraudInferenceService` with `predict_single`, `predict_batch`, `get_business_metrics`, `health_check`. Tier 1 XGBoost (96.3% PR-AUC). Tier 2 Isolation Forest ensemble. `src/models/explain.py` — SHAP, but only ever run offline to save static PNGs | Tier 1 strong, Tier 2 weak (per your own plan: 6.2% PR-AUC), explainability not servable live |
| **Feedback loop** | `src/models/failure_analyzer.py` (finds misses, extracts evasion patterns) + `src/models/feedback_loop.py` (synthesizes new adversarial rows, retrains, compares val F1) | Real, and the CHANGELOG has genuine before/after numbers (val recall 0.8200→0.8467, FN 34→32) — this is your best story, currently invisible to anyone who isn't reading `CHANGELOG.md` |
| **Web prototype** | `app.py` — a single-file Streamlit script, currently syntactically broken (a `with col2:` block is stranded after the footer), and the "Live Demo" tab **doesn't call the model at all** — it's `if amount > 5000: risk_score += 0.3`, hardcoded | Not usable as-is |
| **Frontend tooling** | `package.json` contains one dependency: `graphifyy`. There is no frontend framework, no design system, nothing else installed | Blank slate |

Two structural gaps matter more than anything cosmetic:

1. **No API layer exists.** `FraudInferenceService` is a Python class with a docstring that says "REST API Ready," but nothing serves it over HTTP. Same for the generators and the feedback loop — everything is a CLI script (`python -m src.models.train`, etc.). A frontend cannot talk to any of this yet.
2. **The taxonomy has a split brain.** The 25-attack catalog lives in a markdown table (for the human-readable doc); the 4 profiles that actually drive simulation live in a Python dict. A frontend that wants to show "25 attacks identified, here's which ones are live" currently has to read two unrelated files to do it.

---

## 3. The interaction model — what a person can actually *do*

This is the part you asked to nail down first, before any visual direction. I've mapped it to the pillars you already use (so the frontend's information architecture matches the codebase's, not a generic dashboard template's), and grounded every interaction in a real backend capability above — not an imagined one.

### 3.1 Identify — the attack surface
- Browse all 25 attacks as a filterable set (category: SE / KYC / PR / AI / BM; status: Implemented / Partial / Conceptual; feasibility). This is a straight read of the unified taxonomy source (see §4).
- Open any attack to see its description, feasibility rationale, and — critically — **whether it's wired to a live generator profile**, and if so, a "generate a sample" action that jumps straight into §3.2 pre-filled.
- The AI-specific category (LLM-Jacking, Autonomous Fraud Agent) is your named differentiator — it should be visually distinguishable from the rest, not as a badge for its own sake but because a judge scanning "novelty" should be able to find it in under five seconds.

### 3.2 Generate — the attack simulation console
This is where "fidelity of attacks in simulation" gets proven, and it's the part of your codebase most hackathon judges will never have seen done this way: the LLM doesn't just spit out feature values, it writes the fraud *pretext* (a voice-clone script, a fake support call) and that pretext is what produces the transaction.
- Pick a profile (or "All"), pick a count, run a generation batch.
- Show the result as **paired evidence**, not a table dump: the generated narrative/pretext text on one side, the transaction fingerprint it produced (amount, device, geo, 3DS outcome) on the other, with a visible line connecting `urgency_level` → `new_device_prob` / `three_ds_failure_prob` so a judge can see the simulation isn't just random noise wearing a costume.
- A running fidelity readout: how many candidate cases were generated vs. dropped (your `drop_stats` — `transaction_not_attempted`, `insufficient_prior_history`, etc. are already tracked, just not exposed) vs. accepted. Showing the *drop rate* is more convincing than hiding it — it demonstrates you're validating fidelity, not rubber-stamping LLM output.

### 3.3 Defend — the live inference view
- A transaction builder (sliders/inputs over the real `FEATURE_COLS`, not the 4 fake ones `app.py` currently uses) that calls `predict_single` for real, or a picker that loads a transaction just generated in §3.2 and scores it immediately — same screen, closing the Generate→Defend loop physically, not just narratively.
- Per-prediction explainability as data, not a baked PNG: top contributing features with signed SHAP values, rendered as an interactive bar/waterfall. This requires turning `explain.py`'s logic into something callable per-transaction (see §4).
- A business-metrics view: precision/recall/F1/alert-rate at each of your four thresholds (0.30/0.50/0.70/0.90) — `get_business_metrics` already computes this, it just needs a table/chart, and a way to see how the operating point trades detection for false positives.

### 3.4 The closed loop — your strongest, least-visible asset
- A "run a feedback cycle" action: analyze current misses → surface the evasion patterns `FailureAnalyzer` finds (e.g. "30%+ of misses are under $100," "60%+ land in normal business hours") → generate steered adversarial rows → retrain → show the delta.
- Show it as **before/after**, using real numbers like the ones already in your `CHANGELOG.md` (val recall 0.8200 → 0.8467, FN 34 → 32, precision 0.9044 → 0.8562 reported honestly as a tradeoff, not hidden). A system that visibly gets harder to fool, with the actual regression disclosed, is a stronger "real-world feasibility" argument than a system that only ever reports wins.
- This is the single best three-minute demo beat you have: click one button, watch Detect → Analyze → Generate → Retrain happen, watch the metric move. Design the whole information architecture around making this sequence physically visible (a loop diagram that animates as each stage completes), not around five disconnected tabs the way `app.py` is today.

### 3.5 Cross-cutting
- One global "run the whole loop" macro for the actual live demo moment (generate → defend → feedback cycle, chained), separate from the manual step-by-step controls used for judges who want to click around themselves.
- A persistent header state: total attacks catalogued / live PR-AUC / cycles run — the four numbers `app.py`'s Overview tab already surfaces, just kept honest and always visible instead of siloed on one tab.
- Command palette (`⌘K`) to jump between attacks, transactions, and cycles — cheap to add with the stack below, and it's a texture that reads as "built by someone who uses these tools daily" rather than "first web app."

None of this needs to be five separate pages the way `app.py`'s sidebar radio implies. A single scrolling narrative (taxonomy → generation → defense → loop) with deep-linkable sections would let you *present* it top-to-bottom in the live demo and let a judge *explore* it out of order afterward — worth deciding early since it changes the nav pattern entirely.

---

## 4. What the project itself needs to change

You asked for this explicitly, so to be direct: don't shape the frontend around what Streamlit can render. Shape the backend around what the interaction model in §3 needs, then build the frontend against that. Concretely, in priority order:

1. **Stand up a real API.** Thin FastAPI service wrapping what already works — don't rewrite the ML code, just expose it:
   - `POST /predict` → wraps `predict_single`
   - `POST /predict/batch` → wraps `predict_batch`
   - `GET /metrics/business` → wraps `get_business_metrics`
   - `GET /attacks` → serves the unified taxonomy (see #2)
   - `POST /generate` → triggers `rule_generator` / `llm_generator` for a profile + count, returns generated cases with their `drop_stats`
   - `POST /feedback/run-cycle` + `GET /feedback/status` → wraps `feedback_loop.py`, ideally as a background job with pollable/streamed status so the frontend can show progress instead of a spinner-then-nothing
   - `GET /explain/{transaction_id}` → see #3

2. **Unify the taxonomy into one source of truth.** Right now `docs/ATTACK_TAXONOMY.md` (25 entries, human-readable) and `src/identify/attack_profiles.py` (4 entries, machine-readable) drift independently. One `attacks.yaml` (or JSON) that both the doc generator and the API read from means the frontend's "25 attacks, N implemented" claim is never at risk of being wrong or out of sync on demo day.

3. **Make `explain.py` callable, not just runnable.** Split the SHAP computation from the matplotlib rendering: a function that takes a transaction (or id) and returns `[{feature, value, shap_contribution}, ...]` as JSON. The plotting code can stay for the `.docx` walkthrough's static figures; the API needs the raw values.

4. **Persist what gets generated.** A generation run, a prediction, a feedback cycle — right now these are ephemeral script outputs. Even SQLite is enough for three days: it lets the frontend list "transactions generated this session," re-open a past feedback cycle's before/after, and survive a page refresh mid-demo without losing state.

5. **Kill `app.py` as the prototype**, but keep it (fixed) as a quick internal sanity-check tool if useful — it's cheap to repair and occasionally handy for checking the model still loads. It should not be what's submitted.

6. **Update the quickstart.** `README.md`'s "Quick Start" and the master plan both still say `streamlit run app.py`. Once the API + real frontend exist, that instruction becomes actively misleading for anyone (a judge included) who tries to run the repo locally.

---

## 5. Design direction — what to look at, and what to actively avoid

You asked to hold off on the palette, so this section is about *visual language and reference points*, not colors or type.

### 5.1 What this product actually is
Strip the "hackathon" framing off for a second: what you're building is a **security-operations console** — closer in spirit to a fraud-ops platform (Sardine, Unit21, Feedzai, SEON) or a builder-facing dashboard (Stripe, Plaid) than to a consumer fintech app (Revolut, Monzo). That distinction matters for every design decision downstream: ops tools are dense, fast-scanning, numeric-first, and trustworthy through restraint — not friendly, not playful, not trying to reduce "money anxiety" the way a consumer banking app does. You're not onboarding a nervous first-time user; you're presenting evidence to someone technical who will judge you faster if the UI *reads* competent.

### 5.2 Concrete references worth actually opening
- **Stripe Dashboard** — the reference for handling real complexity (payments, disputes, fraud signals) without it reading as cluttered. Study the left-nav + breadcrumb pattern and how dense data tables stay legible.
- **Plaid's dashboard** — a builder-facing console over financial data rather than a customer-facing app; the "connection health" / environment-state vocabulary (live vs. test, healthy vs. degraded) is exactly the register your Tier 1 / Tier 2 / feedback-loop states need.
- **Mobbin's admin dashboard collection** — [mobbin.com/explore/web/screens/admin-dashboard](https://mobbin.com/explore/web/screens/admin-dashboard) — real, in-production screens, not concept art. Better signal than Dribbble for a tool like this.
- **SaaSUI** — [saasui.design](https://www.saasui.design/) — curated by screen type (dashboards, empty states, settings), useful for finding the exact pattern you're stuck on rather than browsing whole apps.
- **shadcndashboard.dev** and similar shadcn/ui-based dashboard kits — worth a skim not to clone, but to see current conventions for KPI cards, data-table density, and dark-mode token structure done well. (More in §6 on why shadcn as a *foundation* rather than a template you keep whole.)
- The **"dark, dense, financial-terminal" register** (several current templates, e.g. "Fortress"-style kits, lean explicitly on Bloomberg Terminal conventions: monospace numerals, muted surfaces, color reserved for gain/loss or risk state) is a legitimately good reference *vocabulary* for a fraud console — not because you should look like a trading terminal, but because "reserve saturated color for meaning, keep everything else quiet" is exactly the discipline a fraud-severity UI needs.

### 5.3 What to actively avoid — the "this was obviously AI-built" tells
Worth naming explicitly since it's your stated concern. Right now (2026) AI-generated interfaces cluster into a few unmistakable defaults:
- Warm cream background + high-contrast serif + a terracotta/clay accent
- Near-black background + a single bright acid-green or vermilion accent, usually paired with a glowing-orb or gradient-blob hero
- Generic "AI product" tells: a chat-bubble icon standing in for the whole product, purple-to-blue gradients on buttons/badges, sparkle icons next to anything the model touched, robot/shield mascot iconography (your current `app.py` literally opens with a 🛡️ emoji title — that's the exact texture to move away from)
- Overuse of glassmorphism, excessive motion on every card, and numbered-step markers (01/02/03) applied to things that aren't actually a sequence

None of these are wrong per se — they're wrong *by default*, applied regardless of subject. The antidote isn't "avoid dark mode" or "avoid gradients," it's: every visual choice should trace back to something true about *this* product (transaction data, model scores, an attack taxonomy) rather than being reachable from any generic "AI dashboard" prompt. That's a decision for the palette/type pass later — flagging it now so it shapes the interaction and layout thinking above, not just the final coat of paint.

---

## 6. Tooling for building this with Cline in three days

### 6.1 Framework
Given the timeline and that "working web prototype" almost certainly means a judge opens a URL: **Next.js (App Router) + TypeScript + Tailwind v4 + shadcn/ui**. Reasoning, not just default-reaching:
- shadcn/ui gives you unstyled-but-structured primitives (Radix underneath) you *own the code for* — you can make it look nothing like a template, unlike a heavier prebuilt admin kit, while still moving fast because the accessibility and interaction plumbing is already correct.
- Vercel deploy from a Next.js repo is a one-command judge-facing live link, which matters more than SSR performance for a 3-day build.
- It's the best-supported stack for AI-agent-assisted building right now (see 6.2) — less friction, less hallucinated API surface, in exactly the tool you're planning to use.

### 6.2 What to hand Cline
Cline (used via CLI or its VS Code extension) does its best work as a long-running agent loop against real context, not one-shot prompts. Worth wiring up before you start generating code:

- **[Context7 MCP](https://github.com/upstash/context7)** — pulls real, version-pinned library docs into context so Cline isn't guessing at a Next.js 16 / Tailwind v4 / shadcn API from stale training data. Install first; it's cited across current MCP roundups as close to mandatory for frontend work.
- **shadcn MCP** — exposes the actual shadcn/ui component registry as tools, so Cline picks real components instead of hallucinating props. You can constrain it explicitly ("use only Card, Tabs, and Sheet for this view") when you want to keep the vocabulary tight.
- **Playwright MCP** — lets Cline open a real browser, screenshot its own output, and iterate against what's actually rendering rather than what it assumes is rendering. This is the single highest-leverage tool for the "doesn't look like an amateur built it" goal: have Cline screenshot every screen it builds and self-critique against this doc before moving on, the same discipline a senior engineer would apply informally.
- **GitHub MCP** — commit/PR flow straight into your existing repo, useful once the FastAPI layer and frontend both need to land in the same place as `src/`.
- **Filesystem access** — Cline typically has this natively depending on host; only add a standalone Filesystem MCP if your setup doesn't already grant it.

Feed Cline this document plus `src/config.py` (the real `FEATURE_COLS`/`MODEL_COLS`/`FRAUD_TYPE_TARGETS`) and the unified `attacks.yaml` from §4 as up-front context on day one — that's the schema it needs to stop guessing field names, and it's cheaper than having it re-derive the schema from scratch by reading every source file itself.

### 6.3 Supporting libraries, chosen for reasons
- **Charts**: Recharts (via shadcn's chart wrapper) for the SHAP bar/waterfall and metric trend lines — mature, composable, doesn't carry the "generic AI dashboard" look that some heavier chart kits (Tremor especially) have picked up recently just from overuse.
- **Data + streaming**: TanStack Query for API state; Server-Sent Events (or simple polling to start, given the timeline) for the feedback-cycle progress view in §3.4 — that live "watch it happen" moment is worth the small extra plumbing.
- **Motion**: Motion (the current Framer Motion) used sparingly — one orchestrated moment (the loop diagram animating through its four stages) beats scattered hover effects everywhere, and matches the restraint principle in §5.3.
- **Backend**: FastAPI + Pydantic for the API layer in §4 — minimal new surface area, and it sits naturally next to the existing Python codebase rather than requiring a second language/runtime.

---

## 7. Suggested sequencing (not a spec — a starting point)

Given 3 days and that your own plan already has Days 1–2 committed to taxonomy/generation/detection work:

- **Now → end of Day 1**: unify the taxonomy (§4.2), stand up the FastAPI skeleton (§4.1) over what already works — this is almost entirely wiring, not new logic, and it's the dependency everything else in the frontend blocks on.
- **Day 2**: build the frontend against the interaction model in §3, in this order — Defend (single prediction + explainability, since `predict_single` already works end-to-end) → Generate (paired narrative/transaction view) → Identify (taxonomy browser, mostly a read view once §4.2 exists) → the closed-loop sequence last, since it's the most valuable but depends on everything else being wired first.
- **Day 3 morning**: the "run the whole loop" macro (§3.5), a pass of Playwright-MCP-driven screenshot self-review against §5, then freeze for the walkthrough doc and demo recording.

---

## 8. Open questions worth deciding before Cline starts generating anything

- **Hosting for the demo**: a Vercel-deployed live link, or a local-only prototype run at presentation time? Changes whether the FastAPI layer needs real deployment config or can stay `localhost` with a `.env`.
- **Live LLM calls during the judge demo, or pre-baked?** `llm_generator.py` calls out to a real model (Anthropic/OpenAI/local per `config.py`); if judges will watch generation happen live, that's a latency and API-key-availability question worth settling now, not on Day 3.
- **Single scrolling narrative vs. multi-view app** (§3, closing note) — this decides the nav pattern and is expensive to change once built.
- **Team split**: if there's more than one person on this, the FastAPI layer (§4) and the frontend (§6) can genuinely proceed in parallel once the API contract (endpoint shapes in §4.1) is agreed — worth locking that contract down explicitly on Day 1 rather than discovering mismatches on Day 3.
