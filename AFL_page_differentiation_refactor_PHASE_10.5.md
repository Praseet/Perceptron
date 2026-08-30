# AFL — Page Differentiation & Redundancy Refactor
### A standalone execution document — run as "Phase 10.5b" alongside/after the existing Phase 9.5 and Phase 10

---

## 0. What this document is, and how it relates to everything else

This is **not** a replacement for `afl_phases_0-11_FRONTEND_CLARIFICATIONS.md` (the "build bible"). It is a
focused, additive execution plan for one specific, real problem that the build bible's existing phases
never targeted: **cross-page content redundancy** — the same information, and in two cases the same
literal interactive component, appearing on the Home page and again on the feature page it's supposed to
be a preview of.

This is a distinct problem from what Phase 9.5 ("Motion & Visual De-Genericization Pass") already fixed.
Phase 9.5's job was *how things move and feel* (motion restraint, icon/numeral precision). This document's
job is *what information appears where* — a content/information-architecture problem, not a visual-polish
problem. Every finding in this document was verified against the actual current source code (see §2), not
inferred from a description of it, and against a real automated design-audit tool's output run against the
live Home page (see §3). Where the two disagree with each other or with the build bible's own original
intent, this document says so explicitly rather than picking a side silently.

**Before doing anything in this document:**

1. Read `frontend/PROGRESS.md` in full, and confirm Phase 9.5 and Phase 10 (whichever has run so far) are
   at the state you expect. This document assumes Phases 0–9.5 are functionally complete and Phase 10
   (QA/accessibility/performance) is either in progress or done.
2. Read this document in full before touching any file. Sections are ordered so that §1–§4 build the case
   and §5 is the actual instructions — do not skip to §5 without reading why each change is being made,
   because several of the fixes below are narrower than they might sound and it matters which three fields
   get kept, not just that three get kept.
3. This work sits **between Phase 10 and Phase 11** in the existing sequence, for the same reason Phase 9.5
   sits between 9 and 10: Phase 10's own locked text says "this phase produces zero new features and zero
   new visual components" and its DO-NOT list opens with "Add, remove, or restyle any component" — this
   document's changes are precisely that, so they cannot be folded into Phase 10 without contradicting text
   already locked there. Phase 11's DO-NOT list similarly forbids new component work. If your `PROGRESS.md`
   already has a Phase 9.5 entry, add this as its own entry (call it "Phase 10.5" if you want a name that
   sorts correctly in your log) rather than merging its checklist into Phase 10's.
4. **Every rule in the build bible still applies and is not repeated in full here**: H.27's anti-pattern
   grep, H.67's numbered checklist, H.68's tabular-nums/icon lockdown, H.71's motion restraint. This
   document assumes you will re-run all of them after making these changes (see §6), the same discipline
   every phase before this one has used.
5. If you have a Playwright MCP tool (or any live-browser screenshot capability) available in this session,
   use it — §7 gives you a specific, ordered set of comparisons to run with it. If you do not have one, say
   so plainly before starting, the same as previous phases have, and fall back to the DOM/code-level
   verification each acceptance criterion also lists.

---

## 1. The actual complaint, stated precisely

The person building this product looked at the finished five-page site and had this reaction, in their own
words: *"a frontend must show maximum things with minimal effort... looking at my frontend it will look
like there was nothing else to show so they just filled the website with repetitive things."*

That is a real, legitimate, and — per the verification in §2 below — **partially but not entirely
correct** diagnosis. Do not treat this document as license to tear up pages that are actually fine. Two of
the five "redundancy" concerns turn out, on inspection of the real code, to already be legitimate
progressive-disclosure patterns that just need sharper presentation, not removal. Two others are real,
concrete, fixable problems — one of which is a straightforward gap between what the build bible originally
specified and what actually got built, not a new judgment call. Treat each item in §4's verdict table on
its own merits; do not apply a uniform "cut everything in half" instinct.

### The underlying principle, and why it's not just opinion

Jakob Nielsen defined progressive disclosure in 1995 specifically to solve this class of problem: reduce
what's shown at once by deferring detail to the point where the user actually wants it, rather than
removing detail or duplicating it. The applicable framing for a data-dense product like this one — from a
2026 industry write-up on progressive disclosure specifically for SaaS dashboards — describes it as three
layers: **high-level signals visible at a glance, detail available on click, and configuration available on
deliberate intent.** That maps directly onto this project's own already-existing structure:

- **Home = the glance layer.** KPI numbers, a compressed system map, a taste of each pillar.
- **Identify / Generate / Defend / Loop = the click layer.** The actual working tool for each job.
- **Defend's "Advanced fields" disclosure, Loop's run-history table = the intent layer.** Detail you asked
  for by taking a deliberate extra action.

The complaint isn't that this three-layer shape is wrong — it's that **two specific components on Home
currently skip the "glance" compression and paste the "click" layer's actual controls in at a smaller size
instead of a real summary.** That's the difference between progressive disclosure (a genuine summary that
earns the click-through) and what the person is correctly sensing: the same screen, shrunk.

---

## 2. Ground-truth findings from the actual current code

Everything in this section was verified by reading the real files as they exist right now — not assumed,
not paraphrased from an earlier report. File paths are exact.

### 2.1 A real structural duplication: Home introduces Identify/Generate/Defend *twice*, back-to-back

`src/features/home/home-page.tsx` composes, in this exact order:

```
<Hero />
<HeroKpiRow />
<ClosedLoopStages />        <- introduces Identify, Generate, Defend, Improve
<PillarPreviewCards />      <- introduces Identify, Generate, Defend again
<NumbersThatHoldUp />
```

`ClosedLoopStages` (`src/features/home/closed-loop-stages.tsx`) renders four cards — icon, leg-color name,
one-sentence description, "Try it →" link — for Identify, Generate, Defend, and Improve.

`PillarPreviewCards` (`src/features/home/pillar-preview-cards.tsx`) renders, immediately below it, three
more cards — icon, name, a live widget, "See all" link — for Identify, Generate, and Defend again. Only
"Improve" doesn't get a second card, because Improve doesn't have a mini (it's folded into the Loop route).

Concretely: a judge scrolling Home reads "Generate: materialize each attack as a real transaction row via
the LLM-backed narrative path" in one card, then scrolls a few hundred pixels and sees a second, different
card also headed "Generate," this time with a live form in it. Same is true for Identify and Defend. This
is the single most fixable, highest-leverage finding in this whole document, because it's a structural
fact about the page's outline, not a matter of taste — **two consecutive sections each independently
introduce the same three things.**

### 2.2 A real component duplication, but only for two of the three minis — and one of them is a documented spec deviation, not a judgment call

`pillar-preview-cards.tsx` implements its three miniatures very differently from each other. Read carefully,
because the fix is different for each:

**Identify mini — legitimate, not a duplicate.** It fetches the real attack list and shows the top 5 by
feasibility, each linking to `?attack_id=` on the full page. This is a genuine curated summary — a
different framing (top-5 highlights) from the full page's job (browse/filter all 25). This is the *model*
the other two should be closer to, not a component that needs fixing.

**Generate mini — duplication, but it was explicitly pre-approved by Phase 5's own locked spec.** The mini
renders:
```tsx
<GenerateControls controls={controls} variant="compact" />
```
— the literal same control surface (attack picker, urgency select, user select, Generate button) as the
full `/generate` page, just visually smaller. This looks like exactly the kind of duplication the person is
complaining about. But re-read Phase 5's own original locked text: *"Generate (a collapsed version of the
Generate page's control panel — **it is fine and expected for this to share the actual `GenerateControls`
component** once Phase 7 exists)."* This sharing was intentional and sanctioned from the start — it is not
a deviation. The real problems with the Generate mini are narrower and more fixable (§2.3 and §2.4 below),
not "it reuses the component."

**Defend mini — duplication, and this one *is* a real, provable deviation from the locked spec.** The mini
renders:
```tsx
<TransactionBuilderForm onSubmit={handleSubmit} variant="compact" />
```
Read `transaction-builder-form.tsx` itself — its own top comment says *"7 visible fields (amount,
hour_of_day, channel, new_device, tx_last_1hr, device_trust_age_days, count_30d)"* and the `isCompact` flag
derived from `variant === "compact"` is used in exactly one place in the whole file: to set the submit
button's `size` prop (`sm` vs `md`). **All 7 primary fields render identically in both `variant="full"` and
`variant="compact"`** — "compact" currently means "same form, smaller button," not "fewer fields."

Compare this against Phase 5's own original locked instruction, which this build has drifted from:
*"Defend (same pattern — **collapsed `TransactionBuilderForm` to three fields**, TODO-linked to Phase 8 if
it hasn't run yet)."*

This is not a matter of opinion or taste. The document you are already building from says "three fields."
What exists is seven fields at two different button sizes. This is the single cleanest, lowest-risk,
highest-confidence fix in this whole document — restoring what was already specified, not inventing a new
direction.

### 2.3 A real functional bug, independent of the visual-redundancy question: the Generate mini silently discards the user's result

`DefendMini`'s submit handler does this:
```tsx
function handleSubmit(tx: TransactionRowWithId) {
  void tx;
  navigate(ROUTES.defend);
}
```
— and the full Defend page correctly reads `lastGeneratedTransaction` back out of the shared Zustand store
at mount (this was verified and locked earlier in this project specifically for the Generate→Defend
handoff). Continuity is preserved: generate something on Home, land on Defend, see it pre-filled.

`GenerateMini` has no equivalent. Its "See all" button is a bare `navigate(ROUTES.generate)` with no id, no
query param, no store write for "the result I just produced on Home." The full Generate page's own
`useGenerateControls()` call is a **separate hook instance** from the mini's — it does not share React
state with the mini, and nothing persists the mini's result anywhere the full page reads from.

Concretely: a judge picks an attack on the Home Generate mini, clicks Generate, sees a result, clicks "See
all" expecting to see more detail about what they just made — and instead lands on a completely empty
Generate page and has to redo the whole thing. This directly contradicts the product's own "information
gained per interaction" goal (the click should teach the user something new, not throw away what they had)
and it is inconsistent with the Defend mini's correct behavior sitting right next to it in the same
section. This is a functional gap to close, not a visual one — fix it in §5.3.

### 2.4 The loop diagram appearing twice is *less* of a problem than it looks, and here's the proof

`hero.tsx` renders `<LoopDiagram mode="static" />` inside a bordered "console" panel with a "static · v1"
label — explicitly decorative, no live data, no event wiring, plays one intro animation and settles.

`loop-page.tsx` renders `<LoopLiveDiagram activeLeg={liveLeg} />`, where `liveLeg` is derived live from
`run.events` — an actual different component, driven by real SSE/demo event data, whose whole job is to
show the system *actually doing something* during a run.

This already **is** the "two zoom levels of the same concept" pattern that solves the redundancy problem
correctly — Home says "here is the system," Loop says "here is the machine operating," which is exactly
right. Do not delete or radically shrink this. The only real gap: nothing on Home visually or verbally
signals *why* seeing the diagram again on Loop is worth it. §5.4 gives a small, cheap fix for that
perception gap — it is not the same category of fix as §2.1–§2.3.

### 2.5 A small, real copy inconsistency, cheap to fix while you're in these files anyway

Every feature page except one uses a `"Step N of 4"` eyebrow label above its title (Generate = Step 2 of 4,
Defend = Step 3 of 4, Loop = Step 4 of 4). `identify-page.tsx` has no `HEADER_STEP` constant at all, and its
title reads **"Attack Taxonomy"** rather than the single-word leg name **"Identify"** every other page uses
for its own title. This is a minor, low-risk consistency fix — include it in the same pass since you'll
already be looking at this file's neighbors.

---

## 3. What the automated design-audit tool found, and which findings to trust

An automated "AI-slop" style audit was run against the live Home page and returned a 54/100 score with 24
findings. Some of these are worth acting on directly. At least one is very likely a **false positive**, and
you should verify this yourself before "fixing" something that was never actually broken — this is the
same discipline this project has already applied to confident-sounding claims all the way through (the
`useLegacyTable`/`@hookform/resolvers` checks, the `activeLeg` edge-direction check). An automated tool's
confident score is not a source of truth any more than a confident paragraph from an AI assistant is.

**Findings worth acting on directly** (cross-referenced against real code above where relevant):

- **"Three/four-card feature row" + "Identical feature cards" + "Icon-heading-paragraph cards"** — this is
  §2.1's `ClosedLoopStages` section, confirmed structurally identical-shaped cards (icon → title → one
  sentence → link) repeated four times, immediately followed by a second three-card row. Fixed by §5.1/§5.2.
- **"Excessive cardification"** — every one of Home's sections wraps its content in a bordered
  `bg-[var(--bg-panel)] border ... rounded-[var(--radius-card)]` container with near-identical padding.
  Addressed by §5.5.
- **"Nested rounded containers"** — likely the KPI tiles and mini-cards both using the same card treatment
  at two different nesting depths. Addressed by §5.5.
- **"Generic section IDs"** (the tool specifically flagged `features`, `benefits`, `how-it-works`,
  `testimonials`, `pricing`, `faq`-style IDs) — grep the actual codebase for these before assuming they
  exist; AFL's real section IDs seen in the code so far (`built-on-heading`, `closed-loop-heading`,
  `numbers-that-hold-up`) are already specific and fine. If the grep in §5.6 finds nothing generic, this
  finding was a false positive on a template baseline the tool assumes by default — note that in
  `PROGRESS.md` and move on, don't invent generic IDs to "fix."
- **Typography findings** ("muted gray body copy," "tiny labels," "excessive font variety," "inconsistent
  inline fonts/colors") — worth a real pass, but do **not** touch anything H.5/Appendix D already locks
  (font family tokens, the two locked fonts). These findings likely point at specific size/color/weight
  choices within already-approved tokens, not the token system itself. Verify against the design tokens
  before changing anything — see §5.7.

**A likely false positive — verify before touching anything:**

- **"Purple-blue AI gradient"** — this project's `src/index.css` contains **zero** occurrences of the
  string `gradient` anywhere (confirmed directly). There are no CSS gradients in this codebase; H.5.4 and
  H.27 both explicitly ban them and the build has been audited against that rule every phase. This finding
  almost certainly comes from the `LoopDiagram`'s four distinct **solid** per-leg colors (`--loop-identify`
  purple, `--loop-attack` orange, `--loop-defend` cyan, `--loop-improve` green) sitting close together,
  which a generic heuristic scanner can misread as a gradient blend when it's actually meaningful, discrete
  color-coding — a legend, not a gradient. **Do not add anything to "fix" this finding.** Confirm the
  absence of any real gradient with `grep -rn "gradient" src/` yourself (§6), log the null result in
  `PROGRESS.md`, and move on. Inventing a fix for a finding that doesn't correspond to anything real is
  exactly the kind of wasted, harmful-if-acted-on-blindly output an automated grader can produce — this
  project's own build bible has already flagged this general risk ("don't let an AI website grader's score
  become your source of truth") and it applies here concretely.

**Findings this document takes no position on either way** (the remaining copy-slop findings — "next-gen
wording," "round-number metrics without source," etc.) — these concern marketing copy tone, which is
outside this document's scope. If you want to address them, treat them as optional and low-priority
relative to §2's structural findings; do not spend the limited remaining time before submission on copy
polish while §2.1–§2.3's structural fixes are still open.

---

## 4. The verdict, section by section — do not skip straight to §5 without reading why

Apply this test to every section on every page, per the product's own already-established priority order
(Home → Defend → Loop → Generate → Identify): **could a judge lose real understanding if this section were
deleted? If yes, keep it. If a section's information already appeared earlier on the same page or the same
information will appear again one click later, either compress it into a genuinely smaller summary, or cut
it — do not let it survive unchanged in two places.**

| Section | Verdict | Why |
|---|---|---|
| Hero + static LoopDiagram | **KEEP, unchanged** | Confirmed genuinely differentiated from Loop's live diagram (§2.4). Not a duplicate. |
| HeroKpiRow | **KEEP, unchanged** | Numbers that don't appear in full anywhere else on Home; genuinely a "glance" layer. |
| ClosedLoopStages | **MERGE into PillarPreviewCards, don't run both** | §2.1 — two sections independently introducing the same three pillars is the clearest actual redundancy on the page. See §5.1. |
| PillarPreviewCards → Identify mini | **KEEP, unchanged** | Already a legitimate curated summary (§2.2). Do not touch its logic. |
| PillarPreviewCards → Generate mini | **KEEP the shared component (per original spec), FIX the continuity bug** | Reuse was explicitly pre-approved (§2.2); the real problem is §2.3's data loss on navigate. |
| PillarPreviewCards → Defend mini | **REDUCE to 3 fields, matching the original locked spec** | §2.2 — this is a documented deviation from Phase 5's own text, not a new design decision. |
| NumbersThatHoldUp | **KEEP, unchanged** | Distinct content (per-fraud-type eval table) that doesn't appear elsewhere on Home. |
| Loop page's LoopLiveDiagram | **KEEP, sharpen the framing copy only** | §2.4 — genuinely different from Home's; just make the "why look again" case explicit. See §5.4. |

---

## 5. Implementation instructions — do these in order

### 5.1 Merge `ClosedLoopStages` and `PillarPreviewCards` into one section

Do not simply delete `ClosedLoopStages` — its "Improve" card is the *only* place on Home that introduces
the fourth pillar, and its asymmetric-width, leg-colored-border card shell (already H.67-compliant: no
equal-width grid) is good, keep it. Instead:

1. In `pillar-preview-cards.tsx`, change the section heading from "Built on real attacks" to something that
   reads as a continuation/deepening rather than a fresh restart — e.g. **"See it work"** or **"Try each
   stage"** (final wording is your call; the constraint is that it must not repeat the word "closed loop"
   or otherwise announce itself as a second introduction to the same four things).
2. Delete `ClosedLoopStages`'s Identify, Generate, and Defend cards' *description-and-link-only* content —
   that information now only needs to exist once, and it should exist in the section that also gives the
   user something to actually interact with, not the one that's purely descriptive.
3. Keep `ClosedLoopStages`'s **Improve** card exactly as it is today (icon, one sentence, "Try it →" link to
   `/loop`) — it has no live-mini equivalent, so it isn't being duplicated by anything.
4. Restructure the layout so the flow reads as one deliberate section: Identify/Generate/Defend as the three
   live mini-cards (already built, per §5.2/§5.3's fixes), with the Improve card visually integrated as a
   fourth item in the same row/grid rather than sitting in its own separate section above. On the `lg`
   breakpoint this likely means a 4-column grid (3 live minis + 1 static Improve card) instead of today's
   two separate grids (a 4-card row, then a 3-card row below it). Preserve the asymmetric-width principle
   from H.67 #10 — do not let this become a new equal-width 4-up grid. A reasonable approach: give Improve
   the same visual weight as one of the three minis rather than reintroducing the old 1.25× weighting math,
   since the "strongest demo" cards argument was about Defend and Loop specifically, and Loop is reached via
   this same Improve card's link.
5. Update `src/App.tsx`'s or `home-page.tsx`'s composition to remove the now-separate `<ClosedLoopStages />`
   line if you've folded its remaining content entirely into `<PillarPreviewCards />`; if you keep it as a
   thin wrapper that only renders the Improve card, that's acceptable too — just don't render both a
   "closed loop overview" heading and a "built on real attacks" heading back to back the way it does today.

### 5.2 Fix the Defend mini: restore the originally-specified 3-field version

Open `src/features/defend/transaction-builder-form.tsx`. Currently `isCompact` (derived from
`variant === "compact"`) only affects the submit button's size. Change this so `isCompact` actually reduces
the visible field set to 3, per Phase 5's original locked text.

1. Pick the 3 fields that make the strongest, fastest, most legible illustrative case for what Defend does.
   A reasonable choice, since it doesn't require inventing new UI: **`amount`, `hour_of_day`, `channel`** —
   these are the three a person can read and understand in one glance without domain knowledge (a dollar
   amount, a time, a channel type), versus fields like `device_trust_age_days` or `count_30d` which need
   more context to mean anything at a glance.
2. When `isCompact` is true, render only those 3 fields' inputs (reuse the existing field components/logic
   — do not rebuild them from scratch) plus the submit button. Do not render the "Advanced fields" disclosure
   at all in compact mode — that's an intent-layer feature (§1) that has no place in a glance-layer preview.
3. All other logic — `defaultValues`, `lastGenerated` pre-fill, the `onSubmit` contract, validation — stays
   exactly as it is. This is a rendering change, not a data-model or validation change.
4. Confirm the full `/defend` page's own usage (`variant="full"`, no prop passed, or explicitly `"full"`)
   is completely unaffected — it must still render all 7 primary fields + the 16-field advanced disclosure,
   unchanged. This is the one non-negotiable page per the build bible's own priority order; do not regress it.
5. In `PROGRESS.md`, log this explicitly as "restored to Phase 5's original locked '3 fields' instruction,
   which Phase 8's implementation had drifted from (both variants rendered all 7 fields)" — this is
   correcting a real, provable deviation, not introducing new scope, and it should be logged that way so a
   future reader understands why the diff touches an already-"complete" Phase 8 file.

### 5.3 Fix the Generate mini's continuity bug

Open `src/features/home/pillar-preview-cards.tsx`'s `GenerateMini` and `src/features/generate/use-generate-controls.ts`.

1. When the mini's `useGenerateControls({ lockAttackId: true })` produces a result, persist enough
   information for the full Generate page to recover it — the same pattern already correctly used for the
   Generate→Defend handoff (`lastGeneratedTransactionId` / `lastGeneratedTransaction` in the Zustand store).
   The cleanest option: add the full `GenerateResult` (or just its `run_id`, if you'd rather have the full
   page re-fetch/reconstruct from a cache) to the store under a new field, e.g. `lastHomeGenerateResult`, or
   reuse the mini's produced attack id via a URL param on navigate — either approach is fine as long as it's
   consistent with how the rest of this codebase already does one-time cross-page handoffs (see the
   `?attack_id=` pattern and the Zustand-for-data / URL-for-navigation-hint split this project already
   settled on for the Loop `?prefill=` question).
2. Update `GenerateMini`'s "See all" button so that if a result exists in the mini's local state, clicking
   through actually restores that result on the full Generate page (pre-selects the attack and/or shows the
   already-generated conversation/transaction), rather than resetting to the page's empty state. If no
   result exists yet (user hasn't generated anything on Home), the button should behave exactly as it does
   today — a plain navigate to `/generate`.
3. Do not change `GenerateControls` itself, and do not change the full Generate page's default empty-state
   behavior when arriving with no prior context (e.g. from the nav bar directly) — this fix only changes
   what happens when there *is* a real result to carry forward.

### 5.4 Sharpen the Home→Loop diagram framing (small, cheap, not a rebuild)

In `hero.tsx`, the "static · v1" label already signals this is a snapshot, not the live thing. Add one
small, specific improvement: make the connection between this diagram and the real one on `/loop` explicit
in the copy, so a judge who does eventually see both doesn't wonder if they're looking at the same screen
twice. A minimal version: change the "Run the loop" button's context, or add a one-line caption under the
console panel — something like *"This is what the system looks like idle. Run a real cycle to watch it
move."* Keep this to a single short line; do not add a second CTA or a new section for this.

### 5.5 Reduce "excessive cardification" without touching the token system

Do not remove the card treatment from every section — some content genuinely needs a bounded, bordered
container (the KPI tiles, the mini-widgets). The fix is **variety of treatment, not zero treatment**:

1. Audit Home's sections for how many consecutive elements use the exact same
   `bg-[var(--bg-panel)] border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4` (or `p-5`)
   combination. If more than ~4 consecutive sibling elements share the identical treatment, vary at least
   one dimension for the most important one (e.g., the merged pillar-preview section's featured/live cards
   could use a slightly different border-top accent per H.67's own asymmetry principle, rather than an
   identical box for every card).
2. Do not introduce a new visual style (no glass, no shadow, no gradient — all still banned per H.27/H.67).
   The available levers are: border color/weight, whether a card has a top accent border vs. a full border,
   internal padding, and grid position/width — the same levers `ClosedLoopStages` already uses correctly
   for its asymmetric widths. Apply that same instinct one level further into the merged section from §5.1.

### 5.6 Verify (don't blindly act on) the automated audit's remaining findings

```bash
# Confirm zero real CSS gradients exist (expect 0 hits):
grep -rn "gradient" src/index.css src/**/*.tsx 2>/dev/null

# Confirm no generic template section IDs exist (expect 0 hits on Home specifically):
grep -rn 'id="\(features\|benefits\|how-it-works\|testimonials\|pricing\|faq\)"' src/features/home/
```
If either command returns hits, address them directly (remove the real gradient; rename the real generic
ID to something AFL-specific, matching the pattern of `built-on-heading` / `closed-loop-heading`). If both
return nothing, log that explicitly in `PROGRESS.md` as "verified false positive, no change made" — do not
invent a fix for a problem that isn't actually present in the code.

### 5.7 Typography findings — verify against locked tokens before changing anything

Before changing any font size, weight, or color for the "muted gray body copy" / "tiny labels" /
"excessive font variety" findings, re-read Appendix D's locked type scale and the two locked font families.
Any fix here must stay within already-approved token values — this is a matter of which existing token gets
applied where, not introducing new type-scale values. If a specific paragraph or label is using an
ad hoc size/color instead of an existing `text-*`/`--text-*` token, that's the actual bug to fix (an
untokenized value slipping through review), not the token system itself.

### 5.8 The small copy-consistency fix from §2.5

In `identify-page.tsx`, add a `HEADER_STEP = "Step 1 of 4"` constant and render it the same way the other
three pages do. Change the page's displayed title from "Attack Taxonomy" to **"Identify"**, matching the
single-word leg-name pattern every other feature page uses (`Generate`, `Defend`, `Loop`). If "Attack
Taxonomy" is used anywhere else as a proper section label (e.g. inside the page as a sub-heading for the
table itself), that usage is fine to keep — this change is specifically about the page's top-level `<h1>`
matching its siblings.

---

## 6. Full audit suite — run all of this before declaring the phase done

This is the same discipline every phase in the build bible has already used. Do not skip any of these:

- `npx tsc --noEmit` — must exit 0.
- `npm run build` — must exit 0; note new bundle sizes for `home-page` and `defend-page` chunks specifically,
  since both changed.
- The H.27 anti-pattern grep, re-run against every file this document touched.
- H.67's numbered 12-item checklist, walked explicitly against the diff.
- `icon-audit.ps1` (H.68 lockdown) — must remain CLEAN; this document didn't add or resize any icons, but
  verify nothing regressed while touching these files.
- The two `grep` commands from §5.6.
- Re-run the existing Playwright test suites for `identify.spec.ts`, `generate.spec.ts`, and `defend.spec.ts`
  — the Defend mini field-count change and the Generate mini continuity fix both touch code paths those
  tests may already cover; if any test asserts the mini renders 7 fields or asserts the old "See all"
  behavior, update the test to match the new, intended behavior rather than treating a failure as a
  regression to revert.
- Write **new** Playwright test coverage specifically for:
  - The Defend mini renders exactly 3 fields (not 7) and the full `/defend` page still renders 7 + advanced.
  - Generating on the Home Generate mini, then clicking "See all," shows the same result on `/generate`
    rather than an empty state.

## 7. If you have Playwright MCP or any live-browser tool available

Run this comparison explicitly — it's the most direct way to confirm the redundancy is actually reduced,
not just structurally different in the code:

1. Screenshot Home's merged pillar-preview section (post-§5.1) and the full `/identify`, `/generate`, and
   `/defend` pages, side by side.
2. For Defend specifically: confirm visually that the Home mini now shows 3 inputs, not 7, and that the full
   page is unchanged from before this document's changes.
3. For Generate specifically: generate a result on the Home mini, screenshot it, click through, and confirm
   the full page's screenshot shows the same result rather than an empty state.
4. Screenshot Home's hero diagram and the Loop page's live diagram side by side, and confirm they read as
   visually distinct in *state* (static/settled vs. mid-animation or clearly "live-labeled") even though
   they share the same underlying node/edge geometry — this is the check for §5.4's fix.
5. If you don't have this tool, perform the same four checks via DOM assertions in the new Playwright tests
   from §6, and say plainly in `PROGRESS.md` that visual confirmation is DOM-only, the same honest framing
   used in every prior phase's report this session.

## 8. `PROGRESS.md` entry — required format

Match the format every phase since Phase 6 has used: file table, decisions/deviations (explicitly separate
"restored to originally-locked spec" items from "new judgment calls" — §5.2 is the former, §5.1/§5.3/§5.4
are the latter), quality additions, test mapping, audit results with exact pass/fail counts, and an honest
statement of what was and wasn't visually verified per §7.
