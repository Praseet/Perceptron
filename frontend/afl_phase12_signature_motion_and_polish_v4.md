# Phase 12 — Signature Motion Engine & Production Polish Pass

> Authority note, read first: `H.0.2 Phase Sequencing` in the combined build
> bible (`afl_phases_0-11_FRONTEND_CLARIFICATIONS_v2.md`) states "There is no
> Phase 12." That was true when Phases 0–11 were the entire authorized scope.
> It is no longer true: this document **is** Phase 12, explicitly authorized
> by the project owner after watching a recording of the running Phase 10.5
> build and deciding the Loop page's signature moment and the site's overall
> execution level both need to go further than Phase 9.5 took them. Per
> `H.1`'s own authority order, the project owner outranks every locked
> decision in this document — that's what makes this a legitimate extension
> rather than a contradiction. Every place this phase overrides a prior
> locked decision (`H.16`, `H.71` most notably), it says so explicitly,
> names the section it overrides, and explains why, in the same voice the
> rest of the build bible already uses for its own contradiction ledger
> (`H.2`). Nothing in Phases 0–11 that this document doesn't explicitly
> touch changes.
>
> Run this only after Phase 10.5 is merged and the app is in a known-good,
> running state. Read this whole document before writing any code — it is
> long on purpose, the same way Phases 9.5 and the H-appendix are long: a
> half-read version of this spec produces exactly the "diagram suddenly
> appears, four boxes pulsate" result this phase exists to fix.

> **Revision 2 note, read second:** the project owner reviewed a recording
> of Phase 12 as originally written and asked for two things this revision
> adds, in the same additive, say-so-explicitly style `H.2`/`H.67`/`H.71`
> already use elsewhere in this build: (1) this phase must be executed
> *with* the Cline skill set now available in this environment, used
> deliberately rather than left idle — §12.2.1 is the new governing
> section for that, and it is not optional; and (2) the execution should
> be pushed to the actual ceiling of what §12.10's non-negotiables allow,
> not stopped at the first adequate result — closer to the Wiz/Darktrace/
> Datadog/Stripe bar the project owner named, gotten the same way §12.2
> already says to get it (density, branching, synchronization — never
> decoration). Nothing already locked in §12.0–§12.14 below is
> relitigated, weakened, or silently changed by this revision — every
> insertion says where it is and why, the same discipline `H.2`'s
> contradiction ledger already holds this whole build to. Skim for the
> `(Revision 2)` marker if you've already internalized the original
> Phase 12 and only need the delta.

> **Revision 3 note, read third:** this revision exists because the
> project owner reviewed the actual result and asked for three more things,
> explicitly with more latitude than Revision 2 had — "more drastic and
> free," substantial visual redesign and not just polish, first-class
> responsive design and performance work, and two specific bugs fixed.
> The project owner also shared a long third-party (non-Cline) critique of
> Phase 12 as **background material, explicitly not as instructions** —
> it is not reproduced here; instead, the ideas in it worth keeping have
> been individually evaluated against this project's own locked rules,
> the real remaining time, and what's actually buildable without new
> backend infrastructure, and folded into §12.5.2.1 (the two bugs),
> §12.8.6 (responsive), and §12.17 (visual substance) below — with
> §12.14's priority ladder updated to reflect all of it — and the
> reasoning kept visible so you can see why something was kept, narrowed,
> or cut — not adopted wholesale. **Two real-world caveats govern this
> whole revision and take priority over its own ambition if they ever
> conflict:** (1) per this project's own logged submission-deadline date,
> today is the deadline — §12.14 restates the priority ladder with that
> literally in mind, and it is the actual authority on what to do if time
> is short, not the length of §12.17's idea list; (2) "substantial visual
> design" in this revision means **structural and typographic boldness —
> real information-hierarchy decisions, reusable primitives that replace
> generic containers, one dominant object per page** — it does not mean
> a second motion spectacle competing with the Loop. §12.2's original
> "spend your boldness in one place" instinct about *motion* stays
> exactly as locked; §12.17 explains why that's compatible with going
> substantially further everywhere else.

> **Revision 4 note, read fourth:** this pass was requested directly by
> the project owner — hand this document to a second, independent AI
> assistant (Claude) with instructions to research it properly and
> harden it, not just re-polish it — under the same real constraint
> Revision 3 already named: today is the deadline, and there is less
> time left now than when Revision 3 was written. Nothing in §12.0–§12.17
> is weakened, relitigated, or silently changed here, matching every
> prior revision's own rule for itself. What this revision actually did,
> in the same "show the work" spirit as `H.44`: **re-ran §12.1.2's own
> measurement from a clean install against this exact tree** (not
> reasoned about from the prose) and confirms the bundle diagnosis is
> still exactly right, down to the same 48/5 `react-flow`/`reactflow`
> string counts; **found and fixed one concrete, code-breaking error**
> inherited from Revision 3 (§12.9 step 6's `LazyMotion` import path,
> corrected in place — see the marked note there and §12.16.2 for the
> verification); **flags one real contradiction this document never
> resolved**, between §12.5.1's claimed node size and what the actual
> shipped component renders (marked in place at §12.5.1, detailed at
> §12.16.3 — this is a flag, not a silent pick, per `H.1`/`H.2`'s own
> standard); **downgrades §12.2.1's skill mandates from "binding" to
> "use opportunistically, never blocking"** so tooling availability or
> slowness can never be the reason a checkpoint slips past the deadline
> (§12.2.1's own text, and a new note at the top of §12.14); and **adds
> one mechanical rule to §12.14** (new §12.14.1) that makes "the app is
> submission-ready at any stopping point" true by construction rather
> than by discipline alone — the `LoopFlowScene` cutover itself only
> happens as the literal last commit of Phase 12.A, after the new
> component already passes its own fitness check in isolation, so an
> interrupted Phase 12 always leaves either the untouched, known-good
> Phase 10.5/11 build or a strictly-better one running — never a
> half-built one wired live into Home or Loop. A short, source-grounded
> research addendum (exact `MOTION_EASE` value, a concrete Tailwind v4
> technique for §12.8.6.4's minimum-size rule, and current, stable
> Core Web Vitals thresholds to give §12.9's "re-measure" step an actual
> pass/fail bar instead of only a relative one) is new §12.16, at the
> end, so it never breaks the flow of the sections it supports. Skim for
> the `(Revision 4)` marker if you've already internalized Revisions
> 1–3 and only need the delta — six marked insertions plus one new
> section (§12.16), all small, all in the same additive spirit this
> document has used for itself from the start.

---

## 12.0 What this phase is, in one paragraph

The current build is honest, coherent, and — per the project owner's own
review of the running app — not yet distinctive. Phase 9.5 succeeded at its
actual goal (stop the build from looking like generic AI-slop) by being
extremely conservative: no glow, no particles, no gradients, and the Loop
diagram's only "animation" is four squares fading in and then breathing an
opacity pulse forever. That conservatism solved the wrong half of the
problem. It's now time to spend the boldness Phase 9.5 deliberately withheld
— in exactly one place it will do the most good (the Loop diagram, which is
this project's entire thesis made visual), and in a disciplined, secondary
way everywhere else (typography, spacing, chrome, page-to-page polish,
performance). The rest of this document is the "how," precisely enough that
an agent that has never seen this codebase before can execute it without
guessing.

**Explicit product decisions already made** (do not re-litigate these; they
were resolved directly with the project owner):

1. **Scope**: not just the Loop page. Every page should read one clear tier
   above where Phase 10.5 leaves it — Home, Identify, Generate, Defend, and
   the shared chrome all get a pass in this phase, not only Loop.
2. **Two animation modes on the flow diagram**: an **ambient/generalized**
   mode that plays automatically once the page has loaded (Home *and* Loop
   both get this — Home no longer stays static), showing what the closed
   loop conceptually does; and a **live/reactive** mode, entered only when
   the person presses "Run the loop," that is specific to the actual run in
   progress and driven by real event data. The ambient mode must never
   impersonate a specific real case — it's explicitly the generalized
   preview, not a fake instance of the live thing. See §12.2 and §12.5.4 for
   exactly how that line is drawn.
3. **Not a "pulsating line."** The project owner explicitly rejected a
   single glowing dot traveling a path as the deliverable — that reads as
   thin no matter how smooth it is. The animation must be dense enough to
   read as a real system doing real work: batched motion, a visible
   branching decision (caught vs. missed), and synchronized numeric
   consequence — detailed fully in §12.5.
4. **Grounded, not decorative.** Every visual element must trace to
   something true about this project — real event fields, real historical
   numbers already trusted elsewhere in this app, or a real structural fact
   (four pillars, one feedback branch). Nothing is invented for spectacle.
5. **Performance is in scope, explicitly** — the current build has a real,
   measured problem (§12.1.2) that is very plausibly why the Loop page
   "takes time to load." Fixing it is part of this phase, not a follow-up.
6. **Nothing breaks.** Every route, every existing acceptance criterion
   from Phases 0–11, and the entire non-negotiables list in §12.10 must
   still hold when this phase is done. If a choice in this document would
   require breaking one of those, stop and flag it in `PROGRESS.md` rather
   than silently picking one — the same standard `H.1` already sets.

---

## 12.1 What was actually measured before writing this spec

Per this whole project's own standard (`H.44` Step D/E: "run the app," "read
the actual output," not "reason about correctness from memory"), the
following is from direct inspection of the Phase 10.5 source and the
checked-in `dist/` build in `_env.zip`, not assumption. Re-verify all of it
against the tree you're actually working in before you start — this
snapshot may already have moved on.

### 12.1.1 What the current Loop diagram actually does

`src/design-system/patterns/loop-diagram.tsx` (the shared `LoopDiagram`,
used by both `Hero.tsx` on Home and `LoopLiveDiagram` on `/loop`):

- Renders through **React Flow v11**. Four nodes at hardcoded positions in a
  480×480 canvas: `identify (240,56)`, `generate (424,240)`,
  `defend (56,240)`, `improve (240,424)` — a diamond, top/right/bottom/left.
  Each node is a plain `<motion.div>` 88×88 box with a 2px leg-color border,
  centered icon, label underneath. No dragging, no dynamic layout — the
  positions are constants (`LEG_META[...].position`), not a graph layout
  algorithm's output.
- **Intro**: over 2.4s (`ANIM_TOTAL_MS`), nodes and edges fade in one at a
  time in a fixed 8-step sequence (`STEP_MS = 300ms` each). This is the
  "diagram suddenly appears" feeling — 2.4 continuous seconds where the page
  shows an incomplete, partially-invisible diagram before anything is
  actually there to look at.
- **Settled state**: each node independently pulses a plain opacity ring
  (0 → 0.25 → 0) on its own 4-second loop, forever, with no relationship to
  what's actually happening in the app. This is the "four blocks in
  different areas which pulsate" the project owner flagged.
- **Live/active state**: when `activeLeg` is set (from real `LoopEvent`
  data via `activeLegForEvents()` in `loop-live-diagram.tsx`), the one
  active node's `boxShadow` inset animates in over 220ms. That is the
  *entire* visual vocabulary for "something is happening" — one property,
  on one node, no motion through space at all. Nothing ever travels between
  nodes; the edges are static colored lines that only change opacity/stroke
  width.
- The **locked event → leg map** actually implemented (not the earlier,
  looser "recommended mapping" in `H.18.5`, which this supersedes per
  `H.1`'s "actual code over prose description" instinct — the code comment
  in `loop-live-diagram.tsx` explicitly calls this the "LOCKED 7-event
  mapping"):

  ```text
  run_start      → identify
  cycle_start    → generate
  miss_added     → improve
  metric_update  → defend
  cycle_end      → null (settled-pulse takes over)
  run_complete   → null
  error          → null
  ```

  Keep this exact map for the new engine's live mode — it's already tested
  and it's semantically right (§12.5.5 extends it with *motion*, it doesn't
  change *which* leg lights up for which event).

### 12.1.2 The measured performance problem

Built output in `_env.zip`'s `dist/assets/` (sizes are what's actually on
disk in this snapshot; re-measure after your changes, don't trust these
numbers by the end of the phase):

| Chunk | Size (raw / gzip) | Contains |
|---|---|---|
| `index-C2hM-Hjg.js` | 492,439 / 156,105 B | React, Router, TanStack Query, Zustand, Motion — loaded on every route |
| `kpi-tile-Cjvl5R6d.js` | 129,524 / 40,614 B | `KpiTile` **and, confirmed by string search, React Flow itself** (48 `react-flow`-prefixed class strings, 5 `reactflow` references) |
| `kpi-tile-8hax8RNO.css` | 6,990 / 1,541 B | includes React Flow's own shipped `reactflow/dist/style.css` |
| `defend-page-CD6JMwDZ.js` | 386,450 / 106,314 B | Recharts (16 references) — correctly scoped to Defend per `H.24.3`, not a Loop problem |
| `loop-page-CMERkZp1.js` | 42,517 / 13,270 B | Loop page's own code |
| `home-page-CAOUOfDV.js` | 11,960 / 3,081 B | Home page's own code |

`grep -rn "from \"reactflow\"" src/` returns **exactly one hit**:
`src/design-system/patterns/loop-diagram.tsx`. Nothing else in the app
imports it.

**The diagnosis:** Home renders `HeroKpiRow` (which uses `KpiTile`) directly
above the fold, and `Hero` renders the static `LoopDiagram` (which pulls in
React Flow) in the same viewport. Loop renders `CycleDeltaTiles` (also
`KpiTile`) alongside `LoopLiveDiagram` (React Flow again). Because
`KpiTile` and the React-Flow-based diagram are both imported, directly or
transitively, by both the Home and Loop route chunks, Rollup's automatic
chunk-splitting merged them into one shared chunk — and that chunk happens
to be named after `kpi-tile`, which hides the fact that ~40.6KB gzip of
what it ships is React Flow, a library whose only actual job in this app is
drawing four fixed, non-draggable squares. Landing on `/loop` cold means
downloading and parsing `index` (156KB gzip) + `loop-page` (13.3KB gzip) +
this shared chunk (40.6KB gzip JS + 1.5KB gzip CSS) before the page is
interactive — and React Flow's own runtime cost (resize observers, internal
viewport/zoom state, its store) adds real main-thread work on top of the
transfer size. This is almost certainly what "the loop takes time to load"
is actually measuring. §12.9 fixes it at the root by removing the
dependency for this component entirely, not by further chunk-splitting
around it.

### 12.1.3 The H.71 / H.16 tension, and how this phase resolves it

Two prior locked decisions this phase deliberately, narrowly overrides:

- **`H.16` (React Flow implementation contract)** assumed React Flow was
  the right tool for a four-node diagram. `ADR-1` in §12.3 replaces it with
  a hand-built SVG component for exactly this one diagram. Nothing else in
  `H.16` (there is nothing else — it's a single-purpose contract) survives,
  because there's no other React Flow usage left in the app.
- **`H.71` §8 use case C** ("Active LoopDiagram leg transition... subtle
  node/edge state change, geometry and dimensions unchanged, no glow/
  particles/beams") and §9's per-page motion budget for Loop restricted the
  diagram to *state changes on fixed geometry* — deliberately ruling out
  anything traveling through space. That restriction is what produced the
  "four pulsating boxes" result. This phase supersedes §8-C and the Loop
  line of §9 specifically, and only those — replacing them with the fuller
  spec in §12.5. Every other line of `H.71` (§4–7's Tier A allowlist and
  rejected list, §13's fitness check, §14/15's dependency discipline)
  remains in force and this phase's new animation must still pass it. The
  new engine is a *bigger, more consequential* use of exactly the same
  disciplined visual language `H.71` already established — not a departure
  from it. If you find yourself reaching for glow, blur, particles, or a
  gradient to make this feel more impressive, that's the signal to make the
  *choreography* richer instead (§12.2), not to break the color/surface
  rules that are still very much in force.

---

## 12.2 Creative direction: what "mind-blowing but grounded" means here

The project owner's bar is explicit: several levels above the current
build, "mind-blowing," referencing Wiz, Darktrace, Datadog, and Stripe —
and explicitly *not* a single traveling dot, however smooth. At the same
time: still grounded in this project, nothing fabricated, and the existing
anti-AI-slop rules (no gradients, no glass, no glow, no particles — see
§12.10) are not up for renegotiation. Those two instructions are only in
tension if "impressive" is assumed to mean "more decoration." It doesn't
have to. Here's what it means instead, and why each reference product
actually earns its reputation this way rather than through glow effects:

- **Wiz's Security Graph / attack-path animation** is impressive because a
  *persistent, always-present graph* lights up a specific, causal path
  through itself in response to a real query — the viewer watches cause
  connect to effect across a structure they can already see, not a
  particle flying through empty space. AFL's equivalent: the four-leg
  topology is always fully visible (no more 2.4s reveal), and what's
  impressive is watching a real event light up a specific, legible path
  across it.
- **Darktrace's Threat Visualizer** is built around a real-time event feed
  driving a graph, with an explicit timeline/replay affordance and an
  emphasis on the *moment an anomaly is confirmed* — a specific, dramatic
  state change, not ambient motion. AFL's equivalent: the "miss detected /
  branches to feedback" moment (§12.5.4) is this project's version of that
  confirmed-anomaly beat, and it should be the single most dramatic instant
  in the whole animation.
- **Datadog** earns its "impressive" reputation from density and
  liveness of *real numbers* — request waterfalls, live-tailing logs,
  counters that visibly tick — rendered with total typographic precision
  (tabular figures, exact alignment), not from background effects. AFL
  already has this instinct (`H.68`'s tabular-nums rule); this phase
  extends it by tying the flow animation's beats directly to the same
  `CountUp` / delta-tile mechanics already built for Loop, so the motion
  and the numbers change in the same instant, not near each other.
- **Stripe's** interface polish comes from precision and restraint at the
  micro-interaction level — consistent easing, no wasted motion, motion
  that always corresponds to a real state change — applied with total
  consistency across the whole product, not from any one hero effect.
  (Stripe's *marketing* pages do use gradients and mesh backgrounds; that
  part is explicitly not the reference — AFL's "no gradients" rule stands.
  The reference is the interaction precision, not the marketing palette.)

**The actual instruction, stated plainly:** get "mind-blowing" from
*information density, real branching, multiplicity, and precise
synchronization with real numbers* — not from glow, particles, or
gradients. A scene where a batch of cases moves together, visibly splits at
a decision point, and the split outcome immediately shows up as a moving
number is more impressive than a smooth single dot, and it's also more
honest about what this product does. Spend the boldness this phase
authorizes entirely inside the new flow-diagram component (§12.5). Every
other page in §12.8 gets disciplined, quiet, precision-grade polish — not a
second competing spectacle. ("Spend your boldness in one place" — an
orchestrated moment lands harder than scattered effects, and stacking a
second showy element elsewhere would undercut the Loop scene rather than
add to the impression.)

**(Revision 2) One honest addition to this section's own reasoning:**
independent research into what currently reads as templated/AI-generated
frontend design (not specific to this project — general calibration
notes used by frontend-design-review tooling) names three clusters that
statistically dominate AI-generated interfaces right now, and one of them
is *"a near-black background with a single bright accent color"* — which,
described at that level of abstraction, is also a fair one-line summary
of AFL's own locked palette (`--bg-base` + `--accent-cyan`, Appendix D).
This is not a reason to touch the palette — it's locked since Phase 1, it
is genuinely well-executed and non-generic in its actual application (a
five-tier semantic risk spectrum, mono figures for data, restrained
single-accent discipline, real grounding per ADR-4), and re-opening it
this close to submission would violate this phase's own "nothing breaks,
nothing already-settled gets relitigated" rule. It's included here because
it sharpens *why* §12.2's actual instruction is correct: the color palette
alone will not be what separates AFL from a generic AI dashboard in a
judge's eyes, because at a glance, a lot of generic output shares that
same high-level palette shape. What separates them has to be exactly the
things §12.2 already prioritizes — information density, a real branching
decision, numbers that move in sync with what's on screen, typographic
precision — because those are the things a templated dashboard doesn't
have and can't fake. Treat this as reinforcement for executing §12.5 and
§12.8.5 as precisely as written, not as a new instruction.

---

## 12.2.1 Mandatory skill-directed execution (Revision 2)

This section is new in Revision 2 — the project owner's explicit
instruction was that the Cline skill set visible in this environment must
be used deliberately to execute this phase, not left idle while the agent
works from spec text alone. Read this section in full before starting
§12.4's Phase 12.A. Every skill below was checked against what it
actually does (not assumed from its name) before being placed in one of
the three categories — the same "verify against the real thing, don't
reason from memory" discipline `H.44` already requires project-wide,
applied here to tooling instead of code.

**(Revision 4) — "required" means "use it when it's available and
cheap," not "block the phase on it."** The word "binding" in this
paragraph, and "Required use" on the individual skill entries below, are
downgraded to that reading — restated once here rather than edited into
every occurrence below, so nothing below needs to change. §12.14's own
priority ladder already treats most of these skills as low-priority
under real time pressure (it cuts `image-to-code` first, then
`design-taste-frontend`'s Home audit); this note just makes that same
instinct explicit for the two skills the ladder currently calls
required regardless of time (`review-animations`, `emil-design-eng`).
If a skill is unavailable, errs, hangs, or would cost more time than the
work it's reviewing, skip it, note the skip in `PROGRESS.md`'s §12.13
entry exactly as any other consciously-deferred item is already logged,
and move on — a missing tool-review pass is a worse outcome to avoid
than a missed deadline, but it is never as bad as one, and this document
should never be the reason an agent sits blocked on tooling instead of
shipping. The content each skill was checking for — GPU-only properties,
a shared easing curve, asymmetric card widths — is still fully specified
in prose elsewhere in this document (§12.5.7, §12.8.5, `H.67`) and
remains checkable by hand if the skill itself isn't available.

### 12.2.1.1 Use these, at the specific point named — this is the required set

**`review-animations`** — the single highest-value skill available for
this phase, and the one with the most direct, literal overlap with work
this document already specifies. It reviews motion code against a strict
craft bar: justified motion (every animation must answer "why does this
animate"), GPU-only properties (`transform`/`opacity`, never
`width`/`top`/`box-shadow` blur — exactly ADR-3 and §12.9 step 4),
asymmetric timing and `ease-out` over `ease-in`, sub-300ms UI timing,
interruptibility, and `prefers-reduced-motion` handling that *simplifies*
rather than just shortens motion — all of which are independently already
locked in this document (§12.5.7, §12.9, §12.10). **Required use:** run it
against `LoopFlowScene`'s finished implementation before checking any box
in §12.5.7, and again against the nav `layoutId` underline from §12.8.1,
treating a "Block" verdict exactly the way an unchecked §12.5.7 item is
already treated — not done until it clears. This is a review skill only;
it does not write code and does not replace the fitness check, it gates
it.

**`emil-design-eng`** — a design-engineering-taste skill built around the
same instinct §12.8.5 is already reaching for: one shared easing curve
used everywhere, sub-300ms UI motion, transitions (not keyframes) for
interruptible state, and the belief that most of what makes an interface
feel expensive is invisible detail, not a visible effect. **Required
use:** consult it while doing §12.8.5's shared-`MOTION_EASE`-constant work
specifically — it's a direct authority on picking that one curve well
(a "confident, slightly decelerating" cubic-bezier, which is already the
family `count-up.tsx` uses) and on auditing the small things around it:
timer pause-on-hidden-tab-style edge cases, whether a transition or a
keyframe is the right primitive for a given state change, and the general
principle that the best version of this pass is the one nobody consciously
notices.

**`design-taste-frontend`** — an anti-generic-frontend skill, but scoped
by its own documentation to landing pages, portfolios, and redesigns —
explicitly **not** dashboards, data tables, or multi-step product UI. Read
literally, that scoping note matters here: it is the right tool for
**Home only** (Home is genuinely landing-page-register: hero, headline,
CTA, pillar cards), and the wrong tool to run against Identify, Generate,
Defend, or Loop, which are dashboard/product-UI pages this skill's own
documentation excludes. **Required use, Home only:** run it in its
"redesign, preserve" mode (it supports this explicitly — "audit-first on
redesigns" — rather than its from-scratch mode) as a second, independent
pass over §12.6's hero integration and the pillar-card row, specifically
checking for the generic-tells its own audit already knows about: equal-
width cards where a real priority order exists (anti-pattern #10 in this
project's own `H.67` — check the two lists agree), a centered-hero-over-
dark-mesh default, and generic three-card symmetry. **Do not** let it run
against Identify/Generate/Defend/Loop or propose new visual direction for
Home — Home's headline, palette, and layout are already locked; this is
an audit pass against those, not a redesign.

### 12.2.1.2 Use narrowly, with an explicit constraint — do not use as documented

**`gsap-react`** — this is a real tension, stated plainly the way this
document states every other tension (§12.1.3's H.16/H.71 precedent): the
skill's own documented usage is `npm install gsap @gsap/react` and the
`useGSAP()` hook, and this project's dependency discipline (`H.71` §14/15,
restated in §12.10 below) explicitly forbids adding GSAP "without an
extraordinary, product-specific reason, which does not currently exist
for this project" — and Revision 2 does not manufacture one. **Resolution:
use the skill as a source of technique, never as a source of a
dependency.** GSAP's own React skill encodes a genuinely useful mental
model this phase's choreography needs anyway — scoped animation via a
container ref, killing/reusing in-flight tweens on rapid state changes
instead of letting them queue (this is precisely §12.5.5's "On
interruptibility" requirement), externally-controlled timeline refs
(play/reverse/progress) for a parent to drive. Read the skill for that
pattern language, then implement the equivalent with what's already
installed: Motion's `useAnimate()` + an imperative `animate()` sequence
gives the same scoped-ref, externally-controllable, interruptible-timeline
shape ADR-3 already committed to. **Do not run `npm install gsap` or
`@gsap/react` at any point in this phase** — if you find yourself reaching
for the real GSAP package because the Motion equivalent feels harder,
that difficulty is signal to simplify the choreography (fewer concurrent
tokens, per §12.9 step 4), not to add the dependency `H.71`/§12.10 already
rule out.

**`stitch-design-taste`** — this skill's actual job is generating a
`DESIGN.md` file to hand to Google Stitch, a separate design-generation
product; it does not review or write React code in this repository at
all, and one of its own documented default behaviors is enforcing
"perpetual micro-motion," which is a direct, named contradiction of
`H.71`'s rejected-effects list and §12.10 (this document forbids exactly
the "animation that plays automatically and cannot be interrupted"
pattern that phrase describes). **Do not invoke it this phase.** If a
future phase ever needs a portable, human-readable description of AFL's
design tokens for some other tool to consume, that's a legitimate,
narrow use of its semantic-naming discipline (name colors by purpose,
e.g. `--risk-critical` not "red") — but that is not this phase's problem,
and its default motion posture must never reach this codebase.

**`image-to-code`** — its documented workflow is: generate a reference
image first, then implement "faithful" to that image. That is a real risk
for this specific project, because the image-generation step has no
knowledge of ADR-4's data-grounding rule or the token/no-gradient
discipline in §12.10 — an unconstrained reference image is exactly the
kind of "fabricated for spectacle" input §12.1's whole first decision
list already rules out. **Narrow, optional use only:** if it would help
to *see* a candidate treatment before committing engineering time to it
(for instance, roughing out what the Beat-3 gate split might look like at
a few different tick-mark densities), generate the reference image, look
at it, then discard the image entirely and re-implement by hand against
§12.5's actual spec and the real token file — never adapt generated
markup, never let a generated image's colors, gradients, or invented
motifs reach the codebase even indirectly. Skip this entirely if time is
short; it is not required for a correct result.

**`pick-ui-library`** — its job is choosing a library for an unconstrained
new project. AFL's dependency set has been locked since `H.71` §14/15 and
restated in §12.10; there is no open library decision for this skill to
resolve, including the React-Flow-removal decision ADR-1 already made.
**Do not invoke it** — if a fresh instinct to reach for a new library
comes up anywhere in this phase, that instinct is answered by ADR-1
through ADR-5 already existing, not by asking this skill to re-derive an
answer this document already gives.

### 12.2.1.3 Not relevant to this phase — skip without spending time on them

`ask-sonner` (this project's `Toast` is a fully custom abstraction per
`H.4.6`; introducing Sonner-specific knowledge here risks exactly the
"don't add both Radix Toast and Sonner just because both appear in
documentation" mistake `H.4.6` already warns against, and Toast isn't
touched anywhere in this phase's scope), `imagegen-frontend-web` /
`imagegen-frontend-mobile` / `brandkit` (image-only concept-board/mockup
generators for products that don't yet have a locked visual identity;
AFL's identity has been locked since Phase 1 and these skills produce
nothing that lands in the running app), `python-appservice-deploy` and
`azure-upgrade` (backend/infra tooling, no surface area in a frontend
phase), `find-skills` (a meta-discovery tool for locating more skills —
this section already resolves which ones apply; spending a turn
rediscovering that is wasted time this close to the deadline).

---

## 12.3 Architecture decisions

Written in this codebase's own `H.2` contradiction-ledger voice: decision,
then reasoning, so a future agent auditing this change understands *why*,
not just *what*.

### ADR-1 — Replace React Flow with a hand-built SVG `LoopFlowScene`

**Decision:** delete the React Flow implementation in
`src/design-system/patterns/loop-diagram.tsx` and replace it with a new,
dependency-free component, `src/design-system/patterns/loop-flow-scene.tsx`
(name it `LoopFlowScene` — it now does meaningfully more than "a diagram,"
so don't keep the old name). Remove `reactflow` from `package.json`
entirely (§12.1.2 confirmed it has exactly one call site).

**Reasoning:** the diagram's own locked geometry (`H.16.4`: fixed 96×96
nodes at fixed positions, not draggable, `H.16.2`: even "interactive" mode
never lets the graph be redesigned) never actually needed a general graph
library — it needed four squares and four lines at coordinates known ahead
of time. React Flow's entire value proposition (dynamic layout, draggable
nodes, connection editing) is unused. Meanwhile it costs ~40.6KB gzip
shared into two above-the-fold surfaces (§12.1.2) and its own internal
viewport/transform stack makes precise, GPU-cheap, pixel-crisp token motion
harder to build reliably than plain SVG would. Removing it is a strict
improvement on every axis that matters for this phase: smaller bundle,
faster perceived load, and full control over the exact animation this phase
requires.

**Compatibility:** preserve the existing public contract as closely as
sensible so callers don't need invasive changes:

```ts
interface LoopFlowSceneProps {
  mode: "ambient" | "live";       // was mode?: "static" | "live"
  activeLeg?: LegId | null;       // unchanged
  events?: LoopEvent[];           // NEW — live mode reads real event data directly
  interactive?: boolean;          // now means "hover/focus affordances enabled", not pan/zoom
  className?: string;
}
```

`"static"` becomes `"ambient"` (Home's old idle preview *is* the new
ambient loop, just no longer inert — see §12.2's decision that Home also
gets real motion now). Update both call sites (`hero.tsx`,
`loop-live-diagram.tsx`) accordingly; there are only two.

### ADR-2 — Two render modes, one engine

**Decision:** `LoopFlowScene` has exactly two modes, not three or a
spectrum:

- **`ambient`** — plays automatically on mount, loops on a calm interval,
  shows the *generalized, conceptual* version of the loop using only
  already-real, already-displayed aggregate numbers (§12.3 ADR-4). Used on
  Home (replacing the old static hero diagram) and on `/loop` before the
  user presses Run.
- **`live`** — entered the instant `run.start()` fires on `/loop`, driven
  directly by the real `LoopEvent` stream (demo or live backend,
  indistinguishable to this component — it only ever reads `events`).
  Reverts to `ambient` automatically once a run reaches a terminal state
  (`run_complete` / `error`) after a short settle beat, so the page doesn't
  strand itself on a "finished" visual forever.

**Reasoning:** this is exactly the distinction the project owner asked for
("in preview it must be... generalized, not some fake case" /
"in loop page it will react to run loop and be specific to what is being
done") and it maps directly onto data that already exists: `ambient` reads
zero live state, `live` reads only the real event stream. There's no third
mode because a third state (e.g., a "recently finished" persistent state)
would need its own invented data to look different from `ambient`, which
would violate ADR-4.

### ADR-3 — Token motion mechanism: manual path sampling, not CSS `offset-path`

**Decision:** implement token movement with a small reusable hook,
`usePathProgress(pathRef: RefObject<SVGPathElement>, progress: number)` →
`{x, y, angle}`, using the path element's own `getPointAtLength()` /
`getTotalLength()`, driven by `requestAnimationFrame`, not CSS
`offset-path`/`offset-distance`.

**Reasoning:** the project owner's single hardest constraint is "must not
be blurry." CSS `offset-path` motion is composited by the browser and can
introduce sub-pixel positioning and rendering-engine-dependent
anti-aliasing seams at arbitrary points along a curve, especially at the
88–96px node scale this diagram uses, and behavior differs slightly across
Chromium/Firefox/WebKit — real risk for a live demo on unknown hardware.
Manually sampling the path with `getPointAtLength()` gives full control:
round the resulting `x`/`y` to the nearest `0.5px` before rendering (crisp
on both 1x and 2x/retina displays), drive opacity/transform only (cheap,
compositor-friendly, no layout thrash — see §12.9's performance rules), and
there is zero cross-browser feature-support risk. This is a small amount of
extra code for a meaningfully more reliable result, which is the right
trade this close to a deadline.

### ADR-4 — Data-grounding rule (this is the rule that keeps "mind-blowing" honest)

**Decision, binding on every visual element the new engine ever renders:**

| Mode | Allowed data sources | Explicitly forbidden |
|---|---|---|
| `ambient` | Only numbers already displayed elsewhere in this app: `ATTACKS_GENERATED_TOTAL` (1,390), the CHANGELOG recall/FN delta (0.8200→0.8467, 34→32), `getSystemStatus()` fields already used on Home (`n_transactions`, `fraud_rate`, `pr_auc_test`). Token labels in ambient mode are the four leg names/icons and, at most, one of these real aggregate figures — never a manufactured per-case identifier. | Any fabricated case ID (`SE-003`, `CASE-017`, etc.), any invented count not sourced from the above, anything implying this is a specific live event. |
| `live` | Only fields present on the actual `LoopEvent` union (`fraud_type`, `cycle`, `count`, `metric`, `value`, `run_id`, `duration_s`, `final`, `baseline`) as they arrive. | Anything not present on the event payload. Do not invent a per-case serial number — the backend doesn't emit one, so don't display one. Use the real `fraud_type` (formatted per the existing `.replace(/_/g, " ")` convention already used in `cycle-timeline.tsx`) as the token's label instead — it's real, it's specific to the run, and it reads exactly as well as a fake ID would. |

**Reasoning:** this is the same instinct already locked into this project
in `H.43` ("a green pulsing dot does not make a system live" / demo status
must say what's actually true) and in `numbers-that-hold-up.tsx`'s own
comment ("Real numbers, no fabrication"). A judge who notices a case ID
that doesn't correspond to anything real is a worse outcome than a slightly
less flashy label that's entirely true. This rule is not a suggestion —
treat it with the same weight as the color-token and no-gradient rules in
§12.10.

### ADR-5 — Code-splitting fix ships with the new component, not after it

**Decision:** `LoopFlowScene` itself becomes a `React.lazy` boundary,
loaded independently from `KpiTile` and from the rest of the Home/Loop page
chunks. See §12.9 for the exact mechanism.

**Reasoning:** simply swapping the implementation without also fixing how
it's chunked would still leave whatever *does* end up shared between Home
and Loop (even just the new component's own code, now heavier because it
contains real choreography logic) blocking KPI-tile rendering the same way
React Flow did. Do this as one change, verify the fix with the same
measurement technique as §12.1.2, don't assume it worked.

---

## 12.4 Phased implementation plan, with safe stopping points

The project owner asked for this to be structured in phases they can stop
at, because the exact time available before submission isn't fixed. Each
phase below ends at a state that is fully working and demo-safe — never
leave the app mid-phase with something broken overnight. Work top to
bottom; do not start a later phase before the one above it is verified
working end to end in the running app (`H.44` Step D/E discipline applies
here exactly as it does everywhere else in this build).

```text
12.A  LoopFlowScene core (ambient + live, geometry, motion engine)   — P0
12.B  Home hero swap-in                                              — P0
12.C  Loop page integration (state machine, timeline/tiles tie-in)   — P0
12.D  Performance remediation (bundle fix, verify the numbers)       — P0/P1
12.E  Cross-page polish (Identify / Generate / Defend / chrome)      — P1
12.F  Signature micro-interaction pass (nav, KPI reveals, etc.)      — P2
12.G  QA, accessibility, cross-browser, anti-pattern audit, PROGRESS — P0 (always)
```

**If you can only do one thing**, do 12.A + 12.C with the ambient/live
distinction working and reduced-motion respected — that alone directly
answers the project owner's original complaint. **12.G's audit is not
optional at any stopping point** — never hand back a build that hasn't at
minimum been re-checked against §12.10's grep list and had reduced-motion
manually toggled once. Each phase section below states its own minimum
acceptance bar so you know what "done enough to move on" looks like.

**(Revision 2)** fold the `review-animations` skill run (§12.2.1.1) into
the end of 12.A, before moving on to 12.B — reviewing `LoopFlowScene`'s
motion once, right after it's built, is cheaper than reviewing it once
per later phase that touches it again. See §12.14's explicit priority
placement for the rest of §12.2.1's skill work.

---

## 12.5 `LoopFlowScene` — full component spec

This is the single most important section of this document. Read all of
it before writing code.

### 12.5.1 Geometry — keep the existing coordinate system exactly

Do not redesign the layout. Reuse the exact existing constants from
`LEG_META` in the current `loop-diagram.tsx`:

```text
viewBox: 0 0 480 480
identify: center (240,  56)   — top
generate: center (424, 240)   — right
defend:   center ( 56, 240)   — left
improve:  center (240, 424)   — bottom
node size: 96×96 (H.16.4's final decision — not 88; 88 was only ever the
           inner content box, per H.16.4's own note)
```

Reasoning: this geometry is already correct, already tested, already what
`H.9.6`'s responsive contract and every existing screenshot assume. Keep it
identical — the whole point of this phase is deeper motion on the same
trusted skeleton, not a redesign that reopens already-settled questions.

**(Revision 4) — flagged, not resolved: check the 96 vs. 88 claim against
`H.16.4` directly before writing this value into the new component.** A
fresh read of the actual pre-Phase-12 `LegNode` (the component this whole
section says to port) shows the bordered box itself — the whole
`motion.div`, border and all, not an inner content box inside a larger
96px frame — built at `width: 88, height: 88`, with the settled-pulse
ring's own geometry computed directly from that 88 (`position.x + 44 - 60`,
where 44 is half of 88). There is no second, larger 96px box anywhere in
the current implementation for an inner 88px box to sit inside. That
doesn't make this section's claim wrong — `H.16.4` may well have locked
96 as a later, correct decision the shipped code simply never picked up —
but it does mean the two sources actively disagree, and per `H.1`'s own
standard this document already applies to every other tension it finds
(§12.1.3), that gets flagged rather than silently decided by whichever
number happened to get typed into this document. Confirm against the real
`H.16.4` text before touching this: if 96 is genuinely current, the port
is also a bugfix and every other constant this file derives from the old
88 (the pulse-ring offset math above, any corner-turn padding in the new
tick-mark traces per §12.5.2, the `viewBox`'s own 480×480 padding relative
to node size) needs to be re-derived from 96, not just the two headline
`width`/`height` values — don't change one number and leave the rest
quietly assuming the old one. If 88 is what's actually locked and this
section's "96, not 88" is simply stale, keep 88 and fix this document's
own text later; either way, don't guess. Full detail and the exact
verification commands used to establish this at §12.16.3.

### 12.5.2 Persistent topology — always fully visible, no reveal-in

Render all four nodes and all four connecting paths at full opacity
**immediately on mount** — no 2.4-second staged fade-in. This alone removes
the "suddenly appears" complaint and meaningfully helps perceived load time
independent of the bundle fix in §12.9.

Route the four connecting paths as **orthogonal, right-angled traces**
(perimeter routing — top→right→bottom→left→top), not straight diagonals —
this is a refinement of, not a departure from, the existing smoothstep-style
routing already in the current implementation. Render each trace with a
restrained technical texture appropriate to the "cyber-instrument" language
this app already has: a thin base stroke in the leg-of-origin's color at
low opacity (≈0.35), with small perpendicular tick marks at regular
intervals along its length (like a ruled scale or a PCB trace) — plain
strokes, no gradient, no blur, no glow, `stroke-width` between 1 and 1.5px.
This is the "always-there structure" a token will travel across; getting it
right is what makes the later motion read as *moving through a real system*
rather than moving through empty space.

**(Revision 2) Implementation refinement — build the tick marks as one
tiled SVG `<pattern>`, not N individual elements.** Because the traces are
strictly orthogonal (§12.5.2's own routing rule — horizontal/vertical
segments only, perimeter routing), a small `<pattern>` (`patternUnits=
"userSpaceOnUse"`, a single short line at a fixed spacing) tiled along
each straight segment via `stroke="url(#trace-ticks)"` produces the exact
same ruled-scale look as manually generating a tick element per interval,
at a fraction of the DOM node count — one `<path>` with a patterned
stroke per trace instead of dozens of individual tick lines across four
traces. This is a strict improvement on the same axes ADR-1 already
argued for removing React Flow: fewer nodes, cheaper paint, same visual
result, and it keeps the "hand-built, not a library" story ADR-1 tells
honest at the implementation-detail level too, not just the dependency
level. The only place this needs manual handling is the four corner
turns, where a short, unpatterned solid segment (a few px either side of
each turn) reads better than a tile seam — a small, one-time detail, not
a reason to abandon the tiled-pattern approach for the straight runs.

A one-time entrance is still allowed and is a good idea, but it must be
**fast and complete, not staged**: the whole topology (all four nodes, all
four traces) may fade+scale in together over ~300–400ms on first mount,
using a single `useInView`/mount trigger — never sequenced node-by-node.
Skip this entirely under reduced motion (render the final state
immediately, per `H.23.1`'s existing pattern).

### 12.5.2.1 Two known regressions, Revision 3 — fix these before any new Loop work

The first Phase 12 pass is already running, and the project owner has
observed two concrete visual bugs in it. Both are diagnosed below against
the actual pre-Phase-12 code (`loop-diagram.tsx` as it existed before
ADR-1's rewrite), not guessed — fix both **before** touching anything
else in §12.8.6 or §12.17, because both sit in the exact code this phase's
other work builds on top of, and building new choreography on top of an
unfixed coordinate bug will just make the bug harder to find later.

**Bug A — the Loop scene is a solid black box for a moment, then the
whole diagram appears at once ("black then instantly loads").** This
project's routes are already lazy-loaded at the page level (`App.tsx`,
`React.lazy` + one shared `<Suspense fallback={<PageFallback />}>`, and
`PageFallback` is a plain centered "loading..." text with no dark
background) — so this is **not** the route-chunk-load flash; the page
itself is already showing by the time this happens. That points at
`LoopFlowScene` itself: §12.5.1's geometry is defined in a fixed 480×480
viewBox, and making that genuinely responsive (as §12.8.6 below now
requires) means the component needs to know its actual rendered container
size before it can pick a scale — the standard way to get that is a
`ResizeObserver` read after mount. **The bug is almost certainly the gap
between "container has mounted" and "ResizeObserver has reported a real
size":** if the component renders nothing (or an unstyled/default-colored
box) during that gap and then swaps to the fully-scaled scene the instant
a size arrives, that is exactly "black, then instantly loads" — MDN's own
docs on this API name this exact failure mode ("visitors may see a flash
of broken layout, as a sequence of changes... instead happening over
multiple frames"). **Fix:** render an explicit skeleton for that gap,
styled with the real design-system panel token (`var(--bg-panel)` or
whichever token the rest of the app's card surfaces already use — never
literal `black` or an unstyled default) so the "loading" moment reads as
an intentional, on-brand loading state rather than a broken one — this
is also just the standard 2026 dashboard pattern (skeleton loading states
are table stakes alongside the sidebar/KPI-row/grid conventions this kind
of product already follows). Then **crossfade** from skeleton to the real
scene via a plain opacity transition (~150–200ms, the shared `MOTION_EASE`
from §12.8.5) once the size is known — never a hard cut. Gate this on one
signal, not two: if `LoopFlowScene` itself ever becomes independently
`React.lazy`-loaded in addition to being measured (it doesn't need to be
— it's not egregiously heavy on its own, and the page-level lazy-load
already covers the initial-load case), make sure the same skeleton covers
both waits so there's one loading state, not a flash-then-a-second-flash.

**Bug B — "the four nodes' outline color square is misplaced."** This one
has a specific, high-confidence root cause once you look at what the old
node actually was: the pre-Phase-12 `LegNode` component (in the
React-Flow-based `loop-diagram.tsx` this phase's ADR-1 replaces) rendered
each node as an HTML `<motion.div>` — "88×88 square, 2px leg-color
border... centered icon" per that file's own comment — positioned by
React Flow's internal engine, which handles centering for you. §12.5.1
resizes this to 96×96 and moves it into a hand-built SVG scene using
*center* coordinates (`identify: center (240, 56)`, etc.) — and native SVG
`<rect>` **positions from its top-left corner via `x`/`y`, not its
center.** The single most common bug in exactly this kind of port is
using the center coordinate directly as `x`/`y` on the `<rect>` instead of
offsetting by half the node size — i.e. writing `x={center.x}
y={center.y}` instead of `x={center.x - 48} y={center.y - 48}` (48 = half
of 96), or equivalently wrapping the rect in a `<g
transform="translate(${center.x}, ${center.y})">` and drawing the rect at
`x={-48} y={-48}`. That produces exactly "the square is offset from its
node" while everything positioned correctly relative to the *center*
(the icon, if it's drawn separately and correctly centered) looks fine —
matching the reported symptom precisely. **Verify this first** — check
whether the leg-colored square's `x`/`y` (or its wrapping transform) is
derived from the *same* half-offset math as every other centered element
in the scene, not a separate, independently-computed value. **If it
turns out the square was instead built as an HTML overlay positioned
outside the SVG** (rather than a native SVG `<rect>`) — the second most
likely cause — the fix is different: an HTML element positioned via CSS
outside the SVG's own coordinate system will drift from the SVG content
under it whenever the SVG's `viewBox`-to-container scale isn't exactly
1:1, which is true at almost every real container width. In that case,
move it inside the SVG proper — either a native `<rect>` positioned in
viewBox units (preferred, simplest, matches "hand-built SVG, not a
library" per ADR-1), or if it genuinely needs to be HTML (unlikely for a
plain bordered square), a `<foreignObject>` at the node's viewBox
coordinates, which establishes its own correctly-scaled containing block
for HTML content inside an SVG — never a `position: absolute` HTML div
living outside the `<svg>` element and computed against a size that may
not match what's actually rendered. **Verification for both:** check
visual alignment of the square against its node/icon at three widths
(desktop ~1280px+, tablet ~768px, phone ~375px) once §12.8.6's responsive
scaling is in place — this is precisely the scenario that would re-expose
either root cause if the fix only happened to work at one specific size.

### 12.5.3 The four beats of any cycle (ambient and live share this shape)

Every cycle — whether the generalized ambient loop replaying itself, or a
real run reacting to real events — tells the same four-beat story, because
that story is this project's actual thesis. Design the choreography around
these four beats explicitly; don't let it become a vaguer, continuous
shimmer:

```text
BEAT 1 — SPAWN (at Identify)
    A small cluster (not one item) of case tokens appears at the
    Identify node and begins moving along the Identify→Generate trace.

BEAT 2 — MATERIALIZE (at Generate)
    The cluster arrives at Generate, briefly holds (≈250–400ms) while a
    small count/label updates near the node, then continues along the
    Generate→Defend trace, now visually representing transactions
    rather than abstract attack concepts (a subtle shape or fill change
    is enough — do not overdesign this into a second full animation).

BEAT 3 — THE GATE (at Defend) — this is the single most important beat
    The cluster reaches Defend and hits a visible decision boundary: a
    short horizontal threshold line at the Defend node that the cluster
    passes through. On contact, the cluster visibly SPLITS:
      - the majority continue past the node and fade out along a short
        "caught" tail (muted/desaturated — these are correctly handled,
        the story is over for them)
      - a small minority visibly change color to the improve-leg green
        and turn to travel the Defend→Improve feedback trace instead
    This is the dramatic, causal moment — the equivalent of Darktrace's
    "anomaly confirmed" beat and Wiz's "here is the path that matters."
    Spend your most careful easing/timing work here, not on the travel
    segments.

BEAT 4 — FEEDBACK (at Improve, then back to Identify)
    The diverted (missed) tokens arrive at Improve. The node shows a
    brief "incorporating" state (a small fill-level indicator filling
    slightly, using only fill/opacity — no progress-bar gradient). The
    moment this resolves, trigger the tied numeric consequence
    (§12.5.6) — a delta tile or inline figure updates in the same
    instant, not near it. The cycle then either loops back toward
    Identify (ambient) or settles (live, once run_complete arrives).
```

Multiplicity (a cluster, not a single dot) and the visible branch at Beat 3
are what make this "not a pulsating line" — there is a real decision with a
visible, unequal outcome, which is the actual content of what this product
does.

### 12.5.4 Ambient mode — exact script

Runs automatically on mount (Home and Loop-before-run), loops on a calm
interval (recommend a full cycle taking **6–8 seconds**, then a **4–5
second** pause before repeating — calm enough to sit in a hero section
without being distracting, not so slow it reads as static). Must be
fully pausable/interruptible the instant `live` mode is requested (Loop's
"Run" press) — never let an ambient cycle finish playing out before
switching; the transition should feel immediate.

Content, per ADR-4 (only real, already-trusted numbers):

- Beat 1 label near Identify: cycle through the four fraud-type category
  groupings already defined in `Appendix A`/`Appendix B` conceptually — or,
  simpler and safer, just show the generic "attack surface" framing with no
  per-item label at all. Do not invent category names not already in this
  project's taxonomy.
- Beat 2/3 count, if shown: `1,390` (the real `ATTACKS_GENERATED_TOTAL`
  constant already displayed on Home's KPI row) — reuse it, don't
  reinvent a smaller demo number.
- Beat 4 consequence: the real CHANGELOG delta, `0.8200 → 0.8467` recall /
  `34 → 32` FN, exactly as already written in `numbers-that-hold-up.tsx`.
  This is the single best real payoff already sitting in this codebase —
  use it as the ambient loop's punchline every cycle.

Label the scene honestly and unobtrusively, the same register as the
existing hero caption ("This is what the system looks like idle. Run a
real cycle to watch it move.") — something like a small caption reading
*"Illustrative — press Run for a live cycle"* is reasonable if it helps,
but don't over-caption; the visual difference between ambient and live
(§12.5.5's labeling) should mostly speak for itself.

### 12.5.5 Live mode — exact event-to-visual mapping

Live mode consumes the real `events: LoopEvent[]` array (the same one
`use-loop.ts` already produces) directly — do not re-derive a single
`activeLeg` string and throw the rest away the way the current
implementation does. The richer engine needs the actual event payloads to
label tokens correctly.

| Event | Visual response |
|---|---|
| `run_start` | Topology settles into "armed" state (already visible per §12.5.2 — just stop any ambient loop cleanly, no restart-from-zero). Baseline metrics available for later delta context. |
| `cycle_start` | **Beat 1 fires.** A token cluster spawns at Identify, sized to feel like "a cycle," and begins traveling toward Generate. Label: `Cycle {n}`. |
| *(materialize)* | When the cluster's travel animation reaches Generate (a client-side timing derived from real event arrival, not a fixed clock — see note below), **Beat 2 fires** automatically; no separate event needed for this. |
| `miss_added` | **Beat 3/4 fires**, specifically. This event is the real, honest trigger for "some cases were missed" — use its actual `fraud_type` and `count` fields as the diverted token(s)' label (e.g. `2 × card_testing`, formatted with the existing `.replace(/_/g, " ")` convention). This is the one event in the whole stream that should feel like the dramatic beat — treat its arrival as the moment to trigger the Defend-gate split animation described in §12.5.3 Beat 3, even if the cluster hasn't finished its own travel timer yet (interrupt/redirect the in-flight animation to the branch point — see the interruptibility note below). |
| `metric_update` | The relevant `CycleDeltaTiles` tile gets its existing emphasis flash (keep that mechanic exactly as built — it already passes `H.71` §8-B). Additionally, the Defend node gets a brief settle/confirm pulse (opacity only, ≤300ms) synced to this event, so the diagram and the tile update in the same visual instant. |
| `cycle_end` | Any tokens still in flight for this cycle complete their travel and are cleared; topology returns to its resting (fully-visible, non-empty) state. Do **not** treat this as "improve" per the older `H.18.5` prose table — follow the actually-locked map from `loop-live-diagram.tsx` (§12.1.1): `cycle_end` is a settle point, not an active leg. |
| `run_complete` / `error` | Settle fully. After a short pause (~1.5–2s) so the final state is actually visible and readable, transition back to `ambient` mode automatically. On `error`, the settle state should visually communicate "stopped," not "succeeded" — reuse the existing `--risk-critical` token for whatever indicator is present, consistent with `CycleTimeline`'s existing error row treatment. |

**On timing**: cycles happen roughly every 3–5 seconds in demo mode
(`H.21.3`, unchanged by this phase). Size each beat's travel duration so a
full spawn→gate→feedback sequence comfortably fits inside that window
without feeling rushed or, conversely, sitting idle waiting for the next
event — roughly 800–1200ms of travel per leg is a reasonable starting
point; tune by actually watching a real demo run, per `H.44`'s standing
instruction to verify against the running app rather than reasoning from a
spec in the abstract.

**On interruptibility**: real events can arrive faster than a full
choreographed beat sequence completes (this is explicitly anticipated —
§12.5.7's fitness check requires every animation here to be interruptible).
If a new event arrives mid-beat, don't queue a growing backlog of pending
animations — either let the in-flight beat finish quickly and drop
immediately into the new one, or (preferred, and closer to how Wiz/Darktrace
handle a fast-moving real feed) redirect the in-flight token toward the new
target rather than finishing its old path pointlessly. Never let the visual
fall behind the real event stream by more than about one beat's worth of
time — the diagram must always be telling the truth about what's actually
happening, not replaying a stale queue.

### 12.5.6 Metric tie-in — motion and numbers change in the same instant

Wire `LoopFlowScene`'s Beat 4 resolution directly to the same data
`CycleDeltaTiles` already tracks (`trackMetric()` in
`cycle-delta-tiles.tsx`) — either by having the Loop page pass a small
`onBeatResolve` callback down, or by having both components derive from the
same `events` array with the diagram's beat timing computed from the same
event timestamps the tiles already key off. The goal is one specific,
testable thing: when a viewer's eye is on the feedback token arriving at
Improve, the recall/PR-AUC/FN numbers on the delta tiles update at that
exact moment, not half a second before or after. This synchronization is
worth real engineering care — it's the single detail most likely to make a
judge feel like they're watching one connected system rather than two
components that happen to be near each other, which is precisely the
"collection of well-made screens vs. a system that happens to have screens"
distinction this whole phase exists to close.

### 12.5.7 Fitness check for this component specifically

Before considering `LoopFlowScene` done, confirm all of the following —
this extends `H.71` §13's general fitness check with points specific to
this component:

- [ ] Topology is fully visible within one frame of mount; nothing takes
      2+ seconds to become visible.
- [ ] Every token label traces to a real field or a real, already-displayed
      aggregate number (ADR-4). Grep the new component's source for any
      string literal that looks like a fabricated ID (`SE-`, `CASE-`, a
      bare incrementing number with no unit) and remove it if found.
- [ ] The Beat 3 gate/split is visually the most emphasized moment in the
      whole sequence — if you can't point to it being more dramatic than
      the travel segments, redo the timing/easing until it is.
- [ ] All animated properties are `transform`/`opacity`/SVG attribute
      values driven via rAF — no animated `box-shadow` blur radius, no
      animated `filter`, no CSS gradient at any point (§12.9's performance
      rules and §12.10's non-negotiables both apply here).
- [ ] Reduced motion: topology renders in its final, fully-visible resting
      state immediately; no token travel plays at all; if a metric changed,
      show the new value immediately (reuse `CountUp`'s existing reduced-
      motion behavior). Verify this by actually toggling
      `prefers-reduced-motion` in devtools and watching both Home and Loop,
      not by reading the code and assuming it's correct.
- [ ] Ambient and live modes are visually distinguishable at a glance (a
      judge who has seen the ambient loop once should immediately recognize
      that pressing Run produced something different/specific), without
      needing to read a caption to tell them apart.
- [ ] Interrupting an in-flight ambient cycle by pressing Run never leaves
      a stray token frozen mid-path or causes a visible jump/flash.
- [ ] No new dependency was added (`H.71` §14/15 dependency discipline still
      applies — this entire spec is achievable with Motion/Framer Motion,
      already in `package.json`, plus plain SVG).
- [ ] **(Revision 2)** The finished component has been run through the
      `review-animations` skill per §12.2.1.1 and does not carry an
      unresolved "Block" verdict — treat this exactly like every other
      unchecked box above, not as a nice-to-have.

---

## 12.6 Home hero integration

Replace the static hero diagram (`Hero.tsx`'s current `<LoopDiagram
mode="static" />` inside the `.console`-wrapped panel) with
`<LoopFlowScene mode="ambient" />`, same panel treatment (keep the
`.console` instrument-surface wrapper, the "closed loop" / version label
row, and the border/radius treatment exactly as they are — those are
already correct and not in scope for this phase). Update the caption
beneath the panel from "This is what the system looks like idle. Run a
real cycle to watch it move." to something that still sets accurate
expectations now that Home *is* moving — e.g. "This is the loop, running
continuously in preview. Press Run for a live cycle." (exact copy is not
locked; keep it short, honest, and consistent with this app's existing
plain-spoken voice per the content-writing rules in `H.42`).

**Performance discipline specific to Home:** Home is the first thing every
judge loads. `LoopFlowScene` must be a `React.lazy` boundary here (§12.9)
so the ambient animation's own code doesn't block the hero's text and CTA
button from rendering immediately — render the copy column and buttons
first, let the diagram panel show a simple static resting-state placeholder
(the topology, no motion yet) for at most one frame while the component
chunk loads, then hand off to the live component once it's ready. This
should be invisible in practice if the chunk is small, but don't skip
verifying it.

---

## 12.7 Loop page state machine

Make the Loop page's own state explicit and drive `LoopFlowScene` from it
directly — this replaces the current `liveLeg` single-string derivation in
`loop-page.tsx` with something richer, but keeps everything else about the
page (the `LoopControls`, `CycleTimeline`, `CycleDeltaTiles`,
`RunHistoryTable`, the run-start/cleanup logic in `use-loop.ts`) exactly as
built — none of that needs to change for this phase.

```text
IDLE      → LoopFlowScene mode="ambient" (auto-playing on mount, per §12.5.4)
RUNNING   → LoopFlowScene mode="live" events={run.events}   (§12.5.5)
SETTLING  → live mode, showing the final state, ~1.5-2s hold
IDLE      → back to ambient (loop closes)
```

Preserve every existing acceptance criterion from `H.18.5` exactly: the Run
button still disables while a run is active, two simultaneous streams are
still impossible, the `aria-live="polite"` status summary and
`CycleTimeline`'s own event rows are unchanged, `RunHistoryTable` still
gets a new row on `run_complete`. This phase only changes what the diagram
itself looks like and how it's driven — it does not change the page's data
flow, routing, or the underlying `use-loop.ts`/`use-event-stream.ts` hooks.

---

## 12.8 Cross-page polish — Identify, Generate, Defend, chrome

This is deliberately the *quiet* half of this phase — precision and
consistency, not a second spectacle (§12.2). Work page by page; each item
below is independent and safe to skip if time runs out without affecting
the others.

### 12.8.1 Shared chrome (`top-nav.tsx`, `footer.tsx`, `command-palette.tsx`)

- **Active-route indicator**: replace the current plain `border-b-2` active
  state with a single shared underline element that animates its position
  via `layoutId` when the active route changes (e.g. `layoutId="nav-
  active-underline"` on a small absolutely-positioned span under the active
  `NavLink`). This is a legitimate, narrow use of `layoutId` per `H.71`
  §4/5 — it is genuinely the same object (the "this is where you are"
  indicator), now positioned under a different item, not a shared-element
  showcase effect. Keep the transition quick (~200ms) and use the project's
  standard `easeOut`.
- **`SystemStatusPill`**: confirm it still says exactly what `H.43` requires
  (demo-data-available honesty, not fake liveness) — no changes to its
  logic, just verify while you're in this area of the code.
- **Command palette**: no functional changes required; if time allows,
  confirm its open/close transition matches the restrained
  `AnimatePresence` pattern already used elsewhere (opacity + small
  directional movement only, per `H.71` §5).

### 12.8.2 Identify

- Confirm `AttackFeasibilityDots` and `RiskBadge` use the locked
  `H.68`-style single stroke-weight/two-icon-size system consistently — if
  Phase 10.5 already handled this, this is a five-minute verification, not
  new work.
- `AttackDetailDrawer` open/close: verify it matches `H.71` §8-G exactly
  (intentional, no gallery/shared-element drama) — again, mostly a
  verification pass if Phase 9.5/10.5 already did this correctly.
- If time allows: a very restrained `layout`-animated reflow when the
  filter bar changes the visible row count (`H.71` §8-H — "use with
  caution," a tiny reflow, never a visible cascade across all 25 rows).
  Skip entirely if it's not clearly correct — this is explicitly the
  lowest-priority item in this whole document.

### 12.8.3 Generate

- Verify the transcript → transaction → diff sequence is a **coordinated,
  immediate reveal** (`H.71` §8-D) — no typing effect, no fake "thinking"
  delay beyond the real fixture delay already specced in `H.21.2`
  (150–400ms). This is a place worth double-checking specifically because
  "make it more impressive" is an easy instinct to misapply here as "make
  it feel like the AI is working harder than it is" — that would directly
  violate `H.71`'s own explicit prohibition on fake thinking/typing
  effects and this phase does not relax that prohibition anywhere outside
  the Loop diagram.
- `DiffAgainstNormal`: if there's room for a `layout`-animated highlight of
  which fields diverge from the user medians, that's a legitimate, useful
  use of motion here (it communicates a real state — which numbers are
  actually anomalous) — but keep it to a border/background-color change,
  not a scale or glow effect.

### 12.8.4 Defend

- `ProbabilityGauge`, `ShapWaterfall`, `ConfusionHeatmap`, `PrCurveChart`:
  verify none of them animate continuously (`H.71` §9 explicitly forbids a
  "continuously animated chart" or "speedometer gauge" on this page) — the
  gauge should settle once to its real value and stop; the SHAP waterfall
  enters once. If Phase 9.5 built these correctly already, this is
  verification, not new work.
- Advanced-fields disclosure (7→23 fields): confirm the `layout` animation
  on expand/collapse is smooth and doesn't cause the page below it to jump
  — `H.71` §8-F is already a "medium-high" priority item; if it's rough,
  this is a good use of remaining time.

### 12.8.5 General precision pass, all pages

Two small, high-leverage additions in the same spirit as `H.68`'s existing
precision addenda (which this phase's own `H.68`-style items below extend,
not replace):

1. **One shared easing curve, named and reused everywhere new motion is
   added in this phase.** Define it once (e.g. a `MOTION_EASE` constant, a
   cubic-bezier in the "confident, slightly decelerating" family already
   implied by `count-up.tsx`'s existing `easeOut` cubic) and import it into
   `LoopFlowScene`, the nav underline, and anywhere else this phase touches
   — rather than each new animation picking its own easing ad hoc. Small
   inconsistencies in easing across a page are exactly the kind of detail
   `H.68` already flagged as separating a "Wiz/Datadog/Darktrace-grade"
   interface from a template-grade one. **(Revision 2)** this is the one
   task in the whole phase most worth running past the `emil-design-eng`
   skill per §12.2.1.1 — picking a single curve well, and using
   transitions rather than keyframes so it retargets smoothly if a token's
   animation is interrupted mid-flight (§12.5.5's interruptibility
   requirement), is exactly its domain.
2. **Re-run the `H.68` icon and tabular-nums rules against everything this
   phase touches** — any new numeric display (ambient-mode labels, new
   delta indicators) must use `tabular-nums`; any new icon usage must go
   through the existing locked `design-system/icons.ts` wrapper, not a
   fresh Lucide import with its own stroke width. **(Revision 2) One
   correction while you're in this file, in the same voice `H.2`'s
   contradiction ledger already uses elsewhere:** `H.68`'s own prose says
   "exactly two icon sizes app-wide," but `icons.ts` as actually shipped
   documents four named tokens — `inline` (16), `node` (26), `empty` (32),
   `pillar` (88) — with its own comment explaining the grow-from-two-to-
   four decision and citing `H.68`'s own escape hatch for it ("if
   something genuinely needs a different size, add a properly named third
   token... not bypass locally"). The code is right and current; `H.68`'s
   summary sentence is what's stale. Verify against the actual four tokens
   in `icons.ts`, not the "two" figure in `H.68`'s prose — `H.44`'s "actual
   code over prose description" instinct, applied here exactly as it's
   applied everywhere else in this build. **(Revision 2)** if you run
   `design-taste-frontend`'s audit pass over Home per §12.2.1.1, this is
   one of the concrete things worth checking it against: icon sizing and
   stroke-weight consistency across the hero and pillar cards is exactly
   the kind of small tell it's built to catch.

---

## 12.8.6 Responsive design — first-class, Revision 3

The original Phase 12 didn't treat responsiveness as its own concern, and
the project owner has correctly flagged that as a real gap, not a nice-
to-have — a judge could easily open this on a laptop with a narrower
window, a tablet, or a phone during review. This section makes it a
required, explicit part of this phase rather than something left to
whatever Tailwind's defaults happen to do.

**The honest scoping call, stated up front:** not every page needs (or
should get) a bespoke, hand-composed mobile layout. Current guidance on
dashboard/analytics interfaces specifically (as opposed to marketing
sites) is that this class of product is overwhelmingly used on 1366px+
screens, and over-investing in full mobile-first table-to-card rebuilds
for a desktop-first tool is often wasted effort that a general-purpose
"don't break, reflow gracefully" pass would have covered just as well.
That reasoning applies differently to different pages here, so the bar is
explicitly different per page:

- **Every page, no exceptions (P0):** nothing overflows, clips, or
  requires horizontal scrolling of the whole page at any width from
  ~320px to ultra-wide; text remains readable (no font shrinking below
  usable sizes); every interactive element remains reachable and at least
  ~44×44px on touch; the nav collapses to a drawer/sheet below the `md`
  breakpoint rather than compressing into unreadable icons-only tabs.
  This is the floor, and it's cheap — it's mostly making sure nothing
  currently assumes a fixed pixel width.
- **Home and Loop (P1 — bespoke composition):** these are the two pages
  most likely to be screenshotted for submission materials or opened on
  a phone by a judge skimming between sessions, and they're also the
  pages with a real "hero" visual (the pillar row; the flow diagram) that
  degrades badly under naive reflow. These two get an actual, specified
  narrow-width composition, not just "let it wrap" — see below.
- **Identify, Generate, Defend (P1/P2 — graceful reflow, not a rebuild):**
  these follow the "priority + column hiding" pattern rather than a full
  card-per-row mobile redesign: show the columns/fields a user genuinely
  can't decide without, tuck the rest behind an existing disclosure
  pattern this app already has (`AttackDetailDrawer` on Identify already
  *is* the "tap for more" surface a mobile table would otherwise need to
  invent — reuse it, don't duplicate it). If there's time left after
  Home/Loop and the P0 floor, a true card-per-row Identify table is a
  reasonable P2 addition, not a requirement.

### 12.8.6.1 Technique: container queries over viewport media queries where the component's context varies

Tailwind v4 (already installed, `@tailwindcss/vite`) ships native
container-query utilities (`@container`, `@sm:`/`@md:` variants inside a
`container-type: inline-size` ancestor). Prefer this over a plain
viewport media query for any component that can appear at different
widths depending on where it's placed (the pillar cards, evidence rows,
`RunHistoryTable`'s rows) — a component that's aware of its own
available width, not just the window's, is the more correct 2026 default
and avoids the classic bug where a component looks right on the page it
was built against and wrong the moment it's reused somewhere narrower.
Reserve plain viewport media queries for genuinely page-level layout
decisions (the nav drawer collapse, the overall grid-template-areas
reflow for a whole page).

### 12.8.6.2 Technique: fluid type scale, not breakpoint-jump type scale

For the Home hero headline and any other large display type, use
`clamp(min, preferred, max)` instead of a fixed size that jumps at each
breakpoint (e.g. `font-size: clamp(1.75rem, 4vw + 0.5rem, 3.25rem)` in
the app's existing rem-based scale) — this keeps type genuinely
proportionate across the whole range instead of visibly "snapping" at
768px/1024px, which is one of the small tells that separates hand-tuned
type from a default Tailwind breakpoint stack. Body copy and data figures
should stay on the existing fixed type scale — this technique is for
display/heading type specifically, not for `tabular-nums` data, which
must stay predictable and unshifting.

### 12.8.6.3 Home at narrow widths

Keep the locked hero copy, palette, and headline exactly as they are —
this is about composition, not content. Stack the hero's copy column
above the diagram/visual column (not beside it) below the `md` breakpoint.
The pillar row (§12.17.2 below) reflows to a single column, preserving
its asymmetric-width storytelling by using height/weight (a taller,
heavier first card) rather than width once there's only one column to
work with — don't let it silently become four equal-height stacked boxes,
which would undo `H.67` anti-pattern #10 the moment the layout goes
single-column.

### 12.8.6.4 Loop at narrow widths — a real composition, specified

This is the page where naive reflow fails worst: a 480×480 SVG scene
squeezed into a 375px-wide phone viewport becomes illegible. Below the
`md` breakpoint, restructure Loop from its desktop side-by-side layout
(diagram beside timeline/metrics) into a single vertical stack, in this
order, so the diagram stays the hero rather than becoming a postage
stamp competing with everything else on screen:

```text
[ compact system-state strip — §12.17.5 ]
[ LoopFlowScene — full available width, still square, min ~280px ]
[ event stream / CycleTimeline — condensed ]
[ CycleDeltaTiles / metrics — condensed ]
[ RunHistoryTable — condensed rows ]
```

`LoopFlowScene` itself should scale via the same responsive-container
technique §12.5.2.1's Bug A fix already requires (`ResizeObserver` +
skeleton-then-crossfade) — that fix and this requirement are the same
piece of work, not two separate ones. Set an explicit minimum rendered
size (do not let it shrink below roughly 280×280 — past that point the
tick-mark trace texture and node labels stop being legible; the
Advanced-fields-style "show less, keep it readable" instinct applies to
geometry too, not just data density).

### 12.8.6.5 Identify, Generate, Defend at narrow widths

- **Identify:** the attack table uses the "priority + column hiding"
  pattern (§12.8.6 intro) at `sm`/`md` — keep the attack name and status
  visible, hide category/feasibility columns behind the existing
  `AttackDetailDrawer` tap-to-open flow. The category-distribution strip
  (§12.17.3) reflows to a horizontal scroll-snap row rather than
  disappearing.
- **Generate:** the control rail (§12.17.4) moves above the generated
  artifact on narrow widths rather than beside it — controls first, then
  result, top to bottom, which is also just the natural reading order for
  a form-then-result flow on a phone.
- **Defend:** the verdict block (§12.17.6) stays first at every width —
  it's already the thing that should be first per that section regardless
  of screen size, so narrow widths mostly just mean the evidence rows and
  transaction fields below it go full-width single-column instead of a
  multi-column grid.

---

## 12.17 Product-level visual substance, Revision 3

This section is the direct answer to "not just polish — substantial
visual design." Read the reconciliation note below before the page-by-
page items; it explains why this section can be genuinely ambitious
without reopening §12.2's original creative direction, which stays
locked exactly as written.

**Reconciliation with §12.2's "spend your boldness in one place":** that
principle was, specifically, about *motion spectacle* — it's still true
that the Loop diagram should remain the only page with an orchestrated
animated set-piece, and nothing below adds a second one. But a page can
look substantially more expensive, more considered, more "someone with
real taste designed this" without moving a single pixel — through
**structural and typographic boldness**: real information-hierarchy
decisions (what's first, what's deferred), reusable primitives that
replace generic containers, and giving each page a visual grammar that
actually matches its job instead of five pages sharing one template. That
is what every item below does. None of it is decoration; all of it is
reorganizing content this app *already has* into a shape that earns its
"production-quality" read the same way Stripe/Wiz/Datadog earn theirs —
mostly through restraint and hierarchy, not effects (§12.11.1 already
found the same lesson independently).

**A rule that applies to every item below, no exceptions:** every new
visual element must be sourced from data or state this app **already
computes and already has flowing to the relevant page** — this section
adds *organization*, never new backend surface area, with the narrow
exceptions explicitly marked "small backend tweak, verify first" below,
consistent with the project owner's own "a little tweak is acceptable"
allowance. If a specific item below turns out to need a field the
current API response doesn't actually include, don't fabricate it —
either skip that item or make the minimal, additive backend change to
expose an already-computed value that just isn't surfaced yet (e.g. a
count already used server-side for pagination but not returned in the
payload). Never invent a metric, a score, or a dimension with no real
computation behind it — ADR-4's rule is unchanged and applies here at
full force.

### 12.17.1 Two new reusable primitives — use these instead of a generic card

Add these to `design-system/patterns/` alongside the existing
`count-up.tsx`/`cycle-delta-tiles.tsx` family, and reuse them everywhere
below rather than reaching for another bordered `<div>`:

- **`EvidenceRow`** — a label, a value (in `tabular-nums` where numeric),
  and an optional signed contribution/weight, laid out as a single row
  with rules rather than a boxed container: `geo_velocity_kmh   742
  +0.41`. This is the right primitive for SHAP-style feature contributions
  (Defend), materialized-feature values (Generate, §12.17.4), and any
  other "fact + its weight" content — it reads as *data*, not as a UI
  chrome decision, which is exactly the register this app's existing
  mono-figure, restrained-container language is already reaching for.
- **`DeltaRow`** — a metric name, a before → after pair, and the signed
  change, e.g. `Recall   0.8200 → 0.8467   +2.67 pts`. Reuse this
  specific shape everywhere a before/after number already exists in this
  app rather than inventing a new stat-card layout per page: `Cycle-
  DeltaTiles` on Loop, the Home metrics strip, and Defend's threshold
  comparison (§12.17.6) can all share one component instead of three
  bespoke ones. Consistency of this one shape *is* the polish — it's the
  kind of repetition a judge registers as "considered system," not as
  "the same box copy-pasted."

Both primitives are pure layout/typography — rules, alignment, and
`tabular-nums` doing the work `border` and `background` used to — and
both are exactly the kind of thing worth a `review-animations`-adjacent
sanity check (does the row's entrance, if any, use the shared
`MOTION_EASE`? does it respect reduced motion?) rather than a new bespoke
transition per usage.

### 12.17.2 Home — make the pillar row's causality visible, not just present

The `PillarPreviewCards` architecture and its asymmetric widths
(`H.67` anti-pattern #10) stay exactly as locked — this is not a
rebuild. Add one thing: a visible connective element **between** the
cards (a short horizontal rule with a small arrow glyph or chevron at
each gap, using the existing `icons.ts` inline size) so the row reads as
`01 IDENTIFY → 02 GENERATE → 03 DEFEND → 04 IMPROVE`, a single causal
sequence, rather than four independent tiles that happen to sit in a
row. This is a small, cheap addition (a handful of static connector
elements between existing cards) with real payoff — it's the difference
between "four features" and "one pipeline," which is this product's
actual thesis, stated visually instead of only in the surrounding copy.

### 12.17.3 Identify — a compact category-distribution strip above the table

Identify's 25 attack vectors already carry a category field the existing
table already filters by (per the existing `[Category]` filter control) —
computing a small distribution (`A 6 · B 5 · C 5 · D 5 · E 4`, or
whatever the real categories/counts are) from data already loaded
client-side needs no backend change at all. Render it as a single
compact horizontal strip of small labeled bars or figures above the
table, not a chart component — this is a five-number summary, not a data
visualization that needs `recharts`. This gives Identify a genuine
"threat surface at a glance" read (its dominant object, per §12.17's own
logic, is the attack surface as a whole, not any single row) before the
user drills into the table itself.

### 12.17.4 Generate — the control rail is narrow, the generated case is the star

Restructure Generate's layout (pure CSS grid/flex change, no new state)
so the attack/target/urgency controls occupy a narrow rail (roughly
25–30% width on desktop, full-width and moved above the result on
narrow viewports per §12.8.6.5) and the narrative → transaction → diff
sequence occupies the dominant remaining space. The form is the
instrument; the generated case is the result, and right now both
compete for the same visual weight. **Small backend tweak, verify
first:** if the Generate API response already includes both the raw
narrative signals (the phrases that drove generation) and the
materialized feature values derived from them, render the mapping
explicitly using `EvidenceRow` — signal on the left, the feature it
produced and its value on the right. If the API only returns the final
feature vector with no link back to which signal produced which feature,
do not fabricate that link — skip this specific sub-item rather than
inventing a mapping that isn't real; the coordinated transcript → 
transaction → diff reveal in §12.8.3 already stands on its own without
it.

### 12.17.5 Loop — a quiet system-state strip, a beat label, and a result that survives

Three additions, all subordinate to the diagram (per the "one dominant
object per page" framing already implicit in §12.5's own design) —
small, quiet typography, never a second visual center competing with
`LoopFlowScene`:

- **A compact state strip** above or beside the diagram: `50 GENERATED →
  42 CAUGHT · 8 MISSED → 8 FED BACK`, using `tabular-nums` and the
  existing muted-text token, one line, no borders. This gives the same
  information the animation already conveys a second, static form —
  useful for anyone glancing at the page mid-cycle, and it's exactly the
  "three synchronized representations" (graph / event stream / result)
  Darktrace's own triage-first pattern validates (§12.11.1).
  **Small backend tweak, verify first:** only build this if the running
  totals it needs are already available from `use-loop.ts`'s existing
  state (very likely, since `CycleDeltaTiles` already derives similar
  numbers) — if not, a minimal additive change to expose an already-
  tracked counter is the "little tweak" the project owner said is
  acceptable; don't invent a number with no real count behind it.
- **A beat label**, small and unobtrusive, reflecting §12.5.3's own four
  beats as they happen (`01 SPAWN` → `02 MATERIALIZE` → `03 GATE` → `04
  FEEDBACK`, current beat emphasized, others muted) — this is genuinely
  useful for accessibility too: it gives someone on reduced motion, or
  anyone who doesn't immediately parse the animation, a text anchor for
  what's happening, at near-zero implementation cost (four static labels,
  one active-state class toggle already driven by state this component
  already has).
- **Persist the settled result.** §12.5.3 Beat 4 and §12.5.6 already
  specify the metric tie-in and a 1.5–2s settle hold before the scene
  returns to ambient — add one thing: once settled, keep a small "last
  cycle" `DeltaRow` (§12.17.1) visible on the page even after the
  diagram itself returns to its ambient loop, rather than letting the
  result disappear the moment the animation moves on. The outcome should
  outlive the animation that produced it.

### 12.17.6 Defend — verdict before mechanics, and the threshold made visual

Two changes, both pure reordering/visualization of data this page
already receives in full (the probability, the threshold, the SHAP
values, the raw fields) — no new backend surface area at all:

- **Reorder so the decision leads.** The model's verdict and probability
  (`FRAUD · 0.873`) should be the first thing on the page, in the
  largest type on it — bigger than the page title, using the same "put
  the current result in the page identity" instinct that makes a page
  title like `DEFEND — FRAUD` more informative than a generic `DEFEND`.
  Then, in order: the top SHAP contributions (as `EvidenceRow`s, replacing
  whatever `ShapWaterfall`'s current container treatment is — verify
  `ShapWaterfall` itself still renders correctly reused inside this new
  ordering, this is a reorder, not a rebuild of that component), then
  the transaction fields, then the existing 7→23 advanced-fields
  disclosure (§12.8.4, unchanged), then `PrCurveChart`/`ConfusionHeatmap`
  evaluation content last. A judge should understand the outcome before
  being asked to parse the input surface that produced it — this is the
  single highest-value reordering in this whole section because it's
  purely information-architecture, costs no new component, and directly
  targets how Stripe/Wiz-grade interfaces actually earn their "instrument,
  not form" read (§12.11's own research already named this).
- **Make the threshold a visual decision boundary, not just two numbers
  in two separate places.** A single, simple horizontal number line (a
  plain SVG or even a styled `<div>` with a positioned marker — this does
  not need a charting library) spanning 0 to 1, with a fixed tick at the
  threshold (`0.500`) and the actual probability plotted as a dot on the
  line, colored by which side of the threshold it lands on. This
  connects probability + threshold + decision into one glanceable object
  instead of three separate facts the user has to mentally recombine —
  and it's a legitimate, non-decorative reuse of the exact "decision
  gate" visual language `LoopFlowScene`'s own Beat 3 already establishes
  (§12.5.3) — the same underlying concept, a threshold something either
  clears or doesn't, expressed twice in the product with two different,
  appropriately-scaled implementations. That's coherent visual vocabulary,
  not repetition.

### 12.17.7 Chrome — two cheap, high-signal changes

- **Give every primary button a specific, consequence-describing label**
  instead of a generic verb: `Score this transaction →` rather than
  `Continue`, `Run feedback cycle` rather than `Run`, `Inspect SE-001 →`
  rather than `Open`. This costs nothing beyond copy and is one of the
  highest signal-to-effort changes available in this entire revision —
  it's a real, if small, marker of product maturity, and it directly
  reinforces `H.42`'s existing plain-spoken-voice rule rather than adding
  anything new to it.
- **Small backend tweak, verify first — sharpen live/demo honesty.** If
  the existing `SystemStatusPill` (§12.8.1, governed by `H.43`) already
  tracks a real demo-vs-live distinction in its underlying state (it
  should, per `H.43`), consider surfacing one more line of already-real
  context when space allows — what's actually backing the current view
  (`Fixture-backed` vs. model/stream details) — but only using fields
  that already exist in that state object. Do not add new categories of
  status metadata (latency, node IDs, request hashes) that aren't already
  tracked — `H.43`'s existing "honest, not instrumented-for-its-own-sake"
  discipline governs this exactly as it already governs everything else
  on this page, and over-adding technical metadata here would actively
  work against the "instrument, not theater" read the rest of this
  section is built around.

### 12.17.8 Explicitly not in scope for this revision, and why

A few ideas worth naming explicitly as **cut**, so no one re-proposes
them mid-implementation under deadline pressure: a persistent cross-page
"case/provenance" object that follows a specific case through Identify →
Generate → Defend → Loop (this is a real state-architecture change, not
a visual one — genuinely good product thinking for a *next* version, but
not a same-day frontend-polish addition); replaying historical Loop runs
from stored event data (contingent on event-level history actually being
retained server-side, which is a backend data-retention decision, not a
frontend one — out of scope here); a "guided judge-mode" walkthrough
overlay (adds real complexity for a benefit the normal UI, done well,
should already deliver); and audio/sound of any kind (unanimously a bad
fit for a demo/judging context and adds deployment complexity for no
real benefit). If any of these turn out to be trivial given state that
already exists (verify before assuming), that's a legitimate P3/stretch
item — but none of them block, gate, or are required by anything else in
this document.

---

## 12.9 Performance remediation — exact steps and how to verify them

Do this as part of shipping `LoopFlowScene`, not as a separate cleanup
pass — ADR-5 already established why.

1. **Remove the dependency.** After `loop-diagram.tsx` is fully replaced
   and both call sites updated, delete `"reactflow": "^11.11.4"` from
   `package.json`'s `dependencies` and run your package manager's install
   step to update the lockfile. Grep the whole `src/` tree once more for
   `reactflow` to confirm zero remaining references before removing it from
   `package.json` — don't remove the dependency first and find out about a
   missed usage from a build error.
2. **Give `LoopFlowScene` its own lazy boundary**, independent of `KpiTile`
   and independent of the page-level route chunks:
   ```ts
   const LoopFlowScene = lazy(() =>
     import("../../design-system/patterns/loop-flow-scene")
       .then((m) => ({ default: m.LoopFlowScene })),
   );
   ```
   used from both `hero.tsx` and the Loop page's diagram slot, each wrapped
   in its own `<Suspense>` with a minimal fallback (the static resting-
   topology placeholder mentioned in §12.6 is a good fallback — not a
   generic spinner; this codebase has no spinners anywhere per `H.10`/
   `H.18.5`'s established empty/loading conventions, don't introduce the
   first one here).
3. **Re-measure.** Run a production build (`vite build`, matching however
   this project's existing `build.log`/`build-final.log` were produced) and
   inspect `dist/assets/` the same way §12.1.2 did: confirm (a) no chunk
   contains the string `react-flow` or `reactflow` anymore, (b) the chunk
   that used to be shared between Home's `KpiTile` usage and Loop's
   `KpiTile` usage has shrunk by roughly the ~40.6KB gzip that React Flow
   accounted for, (c) the new `LoopFlowScene` chunk is its own file, loaded
   only by the two pages that use it. Record the before/after numbers in
   `PROGRESS.md` (§12.13) — this project's own culture is "real numbers, no
   fabrication," and a before/after bundle-size table is exactly the kind
   of concrete evidence this build bible already values (see `Appendix F`'s
   whole existence).
4. **Animation performance rules**, applied throughout `LoopFlowScene` and
   anywhere else this phase adds motion:
   - Animate only `transform`, `opacity`, and plain SVG geometry attributes
     computed via `requestAnimationFrame` (ADR-3) — never animate
     `width`/`height`/`top`/`left`/`margin` or anything that forces layout
     recalculation on every frame.
   - Cap concurrent in-flight token animations at a small, fixed number
     (a handful per cycle, per §12.5.3's "a cluster, not a crowd" framing)
     — this is also a visual-quality decision, not only a performance one;
     an unbounded number of simultaneously animating elements is exactly
     how a "mind-blowing" ambition accidentally turns into a busy, generic-
     feeling particle field, which is precisely what this document is
     trying to avoid.
   - Clean up every `requestAnimationFrame` loop and any `setTimeout`
     scheduled by a beat sequence in a `useEffect` cleanup / on unmount —
     this codebase already has one documented, painful bug from an
     un-cleaned-up subscription (`use-loop.ts`'s extensive comments about
     the unsubscribe-on-cleanup requirement); don't reintroduce that class
     of bug in the new component.
5. **Do not otherwise chase performance you haven't measured** — `H.24.1`'s
   "do not optimize before measuring" instinct still applies to everything
   outside this section. If Lighthouse or a Playwright timing check surface
   a *different* concrete issue while you're in here, note it in
   `PROGRESS.md` as a finding; don't go on a broader unscoped optimization
   pass this phase doesn't call for.
6. **(Revision 3) A short, current, specific list — apply what's genuinely
   relevant, skip what isn't, and don't treat this as license to override
   step 5's "don't chase what you haven't measured":**
   - **`LazyMotion` + the `m` component for anything animated outside
     `LoopFlowScene`'s own imperative animation (which already uses plain
     `requestAnimationFrame`/SVG per ADR-3, not the `motion` component
     namespace).** The full `motion` import carries real bundle weight.
     **(Revision 4) — corrected import path, verified against this
     project's actual installed package, not the library's current docs:**
     use `import { LazyMotion, domAnimation, m } from "framer-motion"`,
     **not** `from "motion/react"`. Framer Motion was renamed to Motion,
     and current upstream docs default every example to the new
     `motion/react` path — but that path only resolves if the `motion`
     package itself is installed, and `package.json` here pins
     `"framer-motion": "^13.1.1"` with no `motion` entry (confirmed by
     installing this project's actual lockfile and running
     `require.resolve("motion/react")` against it — it throws
     `MODULE_NOT_FOUND`). `framer-motion` is now a republished alias of
     the same code, and its `13.1.1` root export genuinely does include
     `LazyMotion`, `domAnimation`, `domMax`, and `m` (confirmed the same
     way, against the same install) — so the fix is a one-word import
     change, not new work. Two things to actively avoid here: don't "fix"
     this by running `npm install motion` instead — that's a second,
     functionally-duplicate animation package added alongside the one
     already in use, which is exactly the kind of new dependency §12.10's
     non-negotiables list rules out, for no real benefit over just
     importing correctly from the package that's already there; and if a
     smaller `m`-only bundle is ever wanted, this version's equivalent of
     the old `framer-motion/m` subpath is `"framer-motion/m"`, not
     `"motion/react-m"`. Once corrected, this still measurably shrinks
     what §12.9 step 3's bundle comparison reports for `<m.div>` usage
     (nav underline, hero reveals, page-level `AnimatePresence` uses) vs.
     the full `<motion.div>` import — verify against the actual
     before/after number, don't assume, exactly as originally instructed.
   - **Never apply Framer Motion's `layout`/`layoutId` prop across an
     unbounded or large list** (a full `RunHistoryTable`, a long
     `Identify` result set) — this is a documented real-world performance
     cliff, not a style preference. The nav underline's single, bounded
     `layoutId` (§12.8.1) is exactly the right-sized use of this feature;
     a `layout`-animated table of dozens of rows is not, and if
     §12.8.2/§12.8.3's optional reflow animations are attempted, keep them
     scoped to the specific rows that changed, never the whole list.
   - **Hoist animation config objects out of render** (a `transition={{
     duration: 0.2, ease: MOTION_EASE }}` object literal written inline in
     JSX is a new object every render, which defeats memoization
     downstream) — define shared transition/variant objects as module-level
     constants (the shared `MOTION_EASE` from §12.8.5 is exactly this
     pattern) and reuse the same reference everywhere.
   - **`content-visibility: auto`** on below-the-fold sections that don't
     need to be measured/painted before they're scrolled into view (long
     table bodies, Home content below the hero) — a cheap, native-CSS way
     to keep the browser from doing rendering work for content nobody's
     looking at yet. Verify it doesn't clip anything that needs to be
     immediately measurable (it can interact awkwardly with intersection-
     observer-driven reveals — test, don't assume it's free).
   - **Virtualize a table only if it can actually grow past roughly 50-100
     rows** — Identify's 25 static attack vectors do not need this;
     `RunHistoryTable` might, if a long demo session can accumulate many
     runs. `@tanstack/react-table` (already installed) pairs cleanly with
     row virtualization if this turns out to matter — check the real
     row count this app can realistically reach before adding it; don't
     add virtualization pre-emptively to a table that will only ever have
     a handful of rows.

---

## 12.10 Non-negotiables — still in force, unchanged by this phase

Re-run the existing `H.27` grep audit and the existing `H.67` numbered
checklist (items 1–12) against every file this phase touches, exactly as
Phase 10 already required project-wide. Nothing in this document authorizes
any of the following, anywhere, including inside `LoopFlowScene`:

```text
backdrop-blur / any glassmorphism panel
bg-gradient / any gradient (background, text-fill, or border), including
    on the new flow traces — the "technical texture" in §12.5.2 is plain
    strokes and tick marks, not a gradient stroke
hover:scale / hover:-translate / any hover-lift transform
shadow-* used for elevation (borders and background-color steps only)
emoji as iconography
raw color literals outside the token file — every new color used by
    LoopFlowScene must be one of the existing --loop-*/--risk-*/--accent-*
    tokens, never a new hex value invented for this phase
glow or blur on any hover/active/pulse/travel state — this explicitly
    includes the token-travel motion itself: a moving element with a blur
    or box-shadow glow trailing it is exactly the "particle effect" look
    the project owner explicitly ruled out, however well-executed
console.log left in shipped code
TODO(Phase ...) markers left unresolved
```

Additionally, specific to this phase's own new surface area:

```text
No fabricated per-case identifiers anywhere (ADR-4 / §12.5.7)
No animation that plays automatically and cannot be interrupted by a real
    user action (the ambient loop must yield instantly to a real Run press)
No third LoopFlowScene mode invented to "bridge" ambient and live — exactly
    two modes, per ADR-2
No new runtime dependency (no GSAP, no Three.js, no OGL, no React Bits
    package installed wholesale) — everything in this spec is achievable
    with Motion (already installed) and plain SVG/DOM, per H.71 §14/15's
    unchanged dependency discipline
```

**(Revision 2)** this list governs even when a Cline skill's own
documented default would suggest otherwise — §12.2.1.2 already resolves
the one real case of this (`gsap-react` recommends installing GSAP; don't)
and §12.2.1.2's `stitch-design-taste` entry names another (its default
posture includes "perpetual micro-motion," which the "No animation that
plays automatically and cannot be interrupted" line above already
forbids). A skill's own opinion is not an authorization to override
anything in this list.

**(Revision 3)** everything above governs §12.17 exactly as much as it
governs `LoopFlowScene` — "substantial visual design" per §12.17's own
opening reconciliation means structure and typography, and every item in
that section was written to need zero new gradients, glow, blur, or
hover-lift to work. If an implementation of any §12.17 item starts to
feel like it needs one of the forbidden treatments to look finished,
that's a signal the item needs a simpler execution (more restraint in
spacing/type/rules), not an exception to this list. Two scope guardrails,
specific to this revision: don't build a full mobile-first card-per-row
transform for Identify's table as a P0/P1 item — §12.8.6's own research
note on desktop-first dashboard usage already makes the case for why
that's a P2, and treating it as required risks real time better spent on
§12.17.6's Defend reorder, which costs less and matters more; and don't
let §12.17's `EvidenceRow`/`DeltaRow` primitives sprawl into a general
component-library refactor — introduce them, use them in the specific
places named in §12.17, and stop there.

---

## 12.11 Design research this phase is grounded in

Brief, so this document doesn't sprawl further than it already has —
general, publicly-documented product principles, not any copied visual
design:

- **Wiz**'s attack-path/Security Graph material centers a persistent,
  unified graph that a specific, causal path lights up across in response
  to a real signal — context and lineage made visible on a structure the
  viewer can already see, rather than motion for its own sake. This is the
  direct model for §12.5.2 (always-visible topology) and §12.5.3's Beat 3
  (a specific path/branch, not ambient shimmer).
- **Darktrace**'s Threat Visualizer is explicitly a real-time event feed
  driving a graph, with a strong emphasis on the moment an anomaly is
  confirmed and an explicit replay/timeline affordance. This is the direct
  model for treating `miss_added` (§12.5.5) as this project's version of a
  "confirmed anomaly" beat, and for ambient mode functioning as a kind of
  replay/preview of the same story.
- **Datadog**'s density-and-precision approach to live numeric data
  (tabular figures, exact alignment, real counters visibly changing) is
  already the instinct behind this project's own `H.68` addenda; §12.5.6
  and §12.8.5 extend that same instinct rather than introducing a new one.
- **Stripe**'s interaction polish comes from consistency and restraint at
  the micro-interaction level, applied everywhere, not from any single
  flashy effect — the direct justification for keeping §12.8's cross-page
  work deliberately quiet while all the "impressive" budget goes into one
  place (§12.2).

None of the above should be read as "go look at their current marketing
pages and copy visual elements" — several of them use gradients, 3D, or
other treatments this project's own locked rules (§12.10) correctly rule
out. Take the *structural* idea from each (persistent graph + lit path;
real-time feed + confirmed-anomaly beat; numeric density and precision;
restraint everywhere except one place), not any specific pixel.

### 12.11.1 Deeper research grounding, Revision 2

A second pass specifically against Darktrace's own published product
material (not just the general secondary sources the original §12.11
drew on) confirms the same structural read and adds one concrete detail
worth carrying into §12.5.3's Beat 3: Darktrace's Threat Visualizer
communicates a confirmed anomaly primarily by **recoloring the specific
nodes and connections actually involved** — the device, its data streams,
and anything connected to it change color together, rather than a
separate alert element appearing elsewhere on screen. That's a validation
of the Beat 3 design already specced (the cluster itself changes color at
the gate and the diverted portion carries that color onward to Improve),
not a change to it — worth knowing as the reasoning *behind* the existing
instruction, in case a judge or teammate asks why the split works the way
it does. Darktrace's interface is also explicitly triage-first — a
compact, glanceable summary view before any drill-down — which is the
same instinct behind §12.5.7's "ambient and live modes are visually
distinguishable at a glance" requirement; that requirement is doing real,
externally-validated work, not just an internal preference.

Separately: general frontend-design-calibration guidance (the same source
§12.2's new addition above draws on) reinforces one specific, checkable
claim already implicit in `H.67`/`H.68` — that equal-width symmetric card
grids and generic three-column layouts are among the most common tells of
templated AI output, specifically *when the underlying content has a real
priority order the layout is flattening.* This directly supports keeping
`H.67`'s anti-pattern #10 (Home's asymmetric card widths) intact through
this phase's Home changes, and is worth having `design-taste-frontend`
(§12.2.1.1) check explicitly rather than assuming Phase 10.5 already got
it right everywhere the hero/pillar-row layout changes in §12.6.

---

## 12.12 Testing and verification protocol

Follow this project's own established testing culture (`H.25`–`H.26`,
`H.54`–`H.58`) — this phase doesn't introduce a new testing philosophy, it
applies the existing one to new surface area:

1. **Drive the running app, don't reason from the diff.** Start the dev
   server, actually watch Home load, actually watch the ambient loop play
   through at least two full cycles, actually press "Run the loop" and
   watch a real cycle including at least one `miss_added` event, actually
   let a run reach `run_complete` and watch it settle back to ambient.
2. **Reduced motion**, toggled in the OS/devtools, checked on both Home and
   Loop: confirm the exact fallback behavior in §12.5.7's checklist, not
   just "shorter" animations.
3. **Playwright**: extend the existing Loop test coverage (`H.54`'s "Loop"
   required-behaviors list, `playwright-defend.log` and similar existing
   logs in the repo show the established pattern) to cover: ambient mode
   auto-plays on mount, pressing Run transitions to live mode, a
   `run_complete` event returns the page to ambient mode, and reduced-
   motion produces the correct static end-state. Use the project's existing
   stable-selector conventions (`H.25.2`) — don't invent a new selector
   strategy for this component.
4. **Visual QA**: re-run the six-pass procedure in `H.26` (structure,
   visual language, interaction, data, accessibility, responsive) against
   Home and Loop specifically, since those are where this phase's largest
   changes land.
5. **Cross-browser**: this phase's `getPointAtLength()`-based motion (ADR-3)
   was specifically chosen to avoid cross-browser risk, but verify it
   actually renders crisply (not blurry, the project owner's explicit
   bar) in at least two engines if the environment allows it, per this
   project's existing cross-browser hardening standard (`H.10`'s Phase 10
   scope).
6. **Performance**: re-run whatever measurement this project already uses
   (Lighthouse, per `H.24.1`) on Home and Loop before/after, alongside the
   bundle-size comparison in §12.9 step 3.
7. **(Revision 2) Skill-gated review**: run `review-animations` against
   `LoopFlowScene` and the nav underline per §12.2.1.1 before considering
   this phase done — this is a formal step in this protocol now, not a
   suggestion, and its verdict gets logged in `PROGRESS.md` (§12.13) the
   same as every other check in this list.
8. **(Revision 3) Responsive verification, concretely** — don't just
   resize the window casually; check all five pages at three explicit
   widths (roughly 375px, 768px, 1280px+) per §12.8.6, with particular
   attention to `LoopFlowScene`'s scaling and the node-square alignment
   bug fix (§12.5.2.1 Bug B) at each width, since that bug is exactly the
   kind that can look fixed at one width and reappear at another.
9. **(Revision 3) Five quick design-quality gates** — cheap, and directly
   enforce "not AI-slop" the way no functional test can:
   - **Grayscale test**: temporarily strip color (devtools filter or a
     throwaway CSS override) from each page. If the visual hierarchy
     collapses without color, color was compensating for a structural
     problem §12.17's reordering/primitives work should have already
     fixed — don't ship a page that fails this.
   - **Card-removal test**: temporarily strip `background`/`border` from
     the new `EvidenceRow`/`DeltaRow` usages and the pillar cards. If the
     layout falls apart with containers removed, the design is over-
     dependent on boxes rather than on the rules/spacing/typography this
     revision is supposed to be built from.
   - **Motion-off test**: with reduced motion forced on, the product
     should still look complete and "designed," not like a broken or
     unfinished version of the animated one — this is the real test of
     whether this phase built a good product with a signature animation,
     or a spectacle that only looks good while moving.
   - **Silhouette test**: take one screenshot per page at desktop width.
     They should be obviously distinguishable from each other at a glance
     — different dominant object, different density, different grammar
     (§12.17's whole premise). If two pages could be mistaken for each
     other from a thumbnail, that's a real finding, not a nitpick.
   - **15-second test**: hand the running app to anyone who hasn't seen
     it and ask what it does. A reasonable answer sounds like "it
     generates hard fraud cases, tests a detector against them, and
     feeds the misses back in to improve it" — if that takes real
     explanation, Home (§12.6, §12.17.2) still needs work.

---

## 12.13 `PROGRESS.md` logging

Log this exactly the way every prior phase has, per the established
protocol (`H.44` Step G, and the `## Phase <N> — <Phase Name> — <ISO date>
— <model/session identifier>` format already used throughout this project):

```text
## Phase 12 — Signature Motion Engine & Production Polish Pass — <date> — <agent>
```

Include, at minimum: which of 12.A–12.G were completed vs. deferred, the
before/after bundle-size table from §12.9 step 3, confirmation that the
§12.10 non-negotiables audit was re-run and passed, and confirmation that
reduced motion was manually verified (not just implemented). If anything in
this document turned out to be wrong once you actually worked against the
real code (a prop name that doesn't match, a locked value that's since
changed) — flag it explicitly in this entry rather than silently deviating,
exactly as `H.1` already requires project-wide. **(Revision 2)** also log
which §12.2.1 skills were actually invoked and a one-line summary of the
`review-animations` verdict (clear / issues found and fixed / issues found
and consciously deferred with reasoning) — this is the concrete evidence
that the Revision 2 skill-usage requirement was actually followed, not
just present in the spec, matching this project's own "real numbers, no
fabrication" standard applied to process instead of metrics this time.

---

## 12.14 If time runs out — minimum viable checkpoints

**(Revision 4)** the skill-usage placements below (from Revision 2) are
guidance on sequencing *if* a skill is used, not a requirement that it
must be — §12.2.1's own text now says so directly; treat every "run it
even at..." instruction in this section the same way.

Stated plainly, in priority order, because the actual time available is
genuinely unknown as of writing this:

1. **Absolute floor**: `LoopFlowScene` exists, replaces React Flow, the
   four beats work in `live` mode when a real run happens, reduced motion
   is correct, and the app builds and runs with no regressions. Skip
   ambient mode's auto-play if you must (fall back to the topology sitting
   in its resting state until a run starts) — this alone already fixes
   "four boxes pulsating with no story" and the bundle-size problem.
2. **Next**: add ambient mode on Loop, then on Home (§12.4/§12.6) — this is
   what makes Home feel alive, which was an explicit, late-added
   requirement, so treat it as genuinely important once the floor above is
   solid, not as optional polish.
3. **Next**: §12.9's full performance verification pass (measure, don't
   assume it worked) and §12.8's quiet cross-page precision pass.
4. **Last, if there's real time left over**: §12.8.5's shared-easing-token
   cleanup and any of the explicitly-marked lowest-priority items (Identify
   filter reflow, Generate diff highlight).

**(Revision 2) Where the new skill-usage work fits this same ladder,
stated explicitly so it doesn't get treated as optional decoration or,
conversely, as a time sink it isn't:** `review-animations` (§12.2.1.1) is
a review pass on code that already exists by the time you'd run it, not
new work — run it even at the absolute-floor checkpoint (item 1 above),
right after `LoopFlowScene`'s live mode is working, because a "Block"
verdict caught early is cheap to fix and expensive to discover later.
`emil-design-eng`'s consult on the shared easing curve belongs with item
4/§12.8.5, where it already sits. `design-taste-frontend`'s Home audit
(§12.2.1.1) is genuinely optional under real time pressure — it's a
second opinion on work §12.6 already specs correctly, valuable if there's
room, skippable if there isn't. `image-to-code`'s exploratory use
(§12.2.1.2) should be the first thing cut if time is short; it was never
required.

At every checkpoint above, the app must be left in a state that is fully
working end to end — never stop mid-change with something visibly broken.
This is the same standard the rest of this build bible already holds
itself to, and it matters more, not less, the closer the deadline gets.

**(Revision 3) The reality check this ladder now needs, stated plainly:**
per this project's own logged submission date, today is the deadline.
Revision 3 substantially expanded this document's scope at the project
owner's explicit request, and that expansion is worth doing — but it does
not get to override the actual time available, and this ladder, not
§12.17's idea count, is the authority on what to do if time is short.
Revised order, folding Revision 3's work into the existing four tiers
rather than appending a fifth competing list:

0. **Before tier 1, if tier 1 (the original absolute floor) is already
   done because a first Phase 12 pass is already running:** fix the two
   named regressions first (§12.5.2.1) — both are already diagnosed with
   a specific, high-confidence root cause, both are cheap relative to
   almost everything else in this revision, and both are the kind of
   visible, easy-to-notice flaw that undercuts trust in everything else
   this phase built, however good the rest of it is. Do these before any
   new §12.17 work, not after.
1. **Tier 1 (unchanged)**: the original absolute floor above, if it isn't
   already done.
2. **Tier 1.5, new, cheap, do this even under real time pressure:**
   §12.8.6's P0 responsive floor (nothing overflows/breaks at any width —
   this is mostly verification and small CSS fixes, not new design work)
   and §12.17.7's CTA-label copy pass (near-zero cost, real signal). Both
   are cheap insurance against something looking visibly broken or
   generic in front of a judge, which is a worse outcome than a missing
   nice-to-have.
3. **Tier 2 (unchanged)**: ambient mode on Loop and Home.
4. **Tier 2.5, new:** of everything in §12.17, do §12.17.6 (Defend:
   verdict-first reorder + threshold visual) first if only one item from
   that section survives triage — it's contained to one page, needs no
   new components beyond what §12.17.1 already adds, and is argued above
   as the single highest-value reordering in the whole revision. After
   that, in descending order of value-per-effort: §12.17.1's two
   primitives (needed by several other items anyway), §12.17.2 (Home
   connective row — small), §12.17.5's beat label and persisted result
   (Loop — small), §12.17.3 (Identify strip), §12.17.5's system-state
   strip (needs the backend-availability check first), §12.17.4
   (Generate restructure).
5. **Tier 3 (unchanged)**: §12.9's full performance verification pass and
   §12.8's quiet cross-page precision pass, now including the Revision 3
   performance additions in §12.9 step 6.
6. **Tier 3.5, new, do only if tiers 0–5 are genuinely solid:** §12.8.6's
   bespoke Home/Loop narrow-width compositions (§12.8.6.3/§12.8.6.4) and
   the §12.12 step 9 design-quality gates — valuable, but a page that
   works correctly at every width without a hand-tuned composition is a
   perfectly acceptable submission state if time runs out here.
7. **Tier 4 (unchanged, still last)**: §12.8.5's shared-easing-token
   cleanup, any explicitly lowest-priority original items, and §12.17.8's
   explicitly-cut ideas if (and only if) they turn out to be trivial.

### 12.14.1 (Revision 4) — the always-shippable rule, made mechanical

Every revision of this document has said some version of "leave the app
working at every stopping point." That's the right instinct, but stated
as discipline alone it depends on the implementer correctly judging, in
the moment, whether *this* half-finished piece of work is safe to leave
overnight — and under real deadline pressure that judgment is exactly
what degrades first. This section replaces judgment with one mechanical
rule for the one place in this whole phase where getting it wrong would
actually break the submitted build: the `LoopFlowScene` cutover.

**The rule:** build and fully verify `LoopFlowScene` — geometry, both
modes, the full §12.5.7 fitness check, reduced motion — as a new,
additional file that nothing else in the app imports yet. Only once it
independently passes §12.5.7 in isolation do you touch `hero.tsx` and the
Loop page's diagram slot to actually switch them over to it. That switch
is the *last* commit of Phase 12.A, by itself, touching only those two
call sites — not bundled with any of the component-building work that
came before it. Do not delete or modify the existing `loop-diagram.tsx`
or remove `reactflow` from `package.json` as part of this same commit
either — per §12.9 step 1, that cleanup is already its own later step;
keeping the old file present and simply unimported for one extra commit
costs nothing and buys a lot.

**Why this is the whole point:** it means the state of "has `LoopFlowScene`
started but isn't finished" and the state of "the running app is
affected by `LoopFlowScene`" are never the same state. If work stops at
any point before that one swap commit — mid-function, mid-beat, midway
through §12.5.3's choreography, even mid-line — `git status` on `main`
shows either nothing in progress or a self-contained, unimported file;
the actual running app is still exactly the Phase 10.5/11 build this
project already froze and verified submission-ready in `PROGRESS.md`.
Nothing needs to be reverted, because nothing live was ever touched. If
work stops *after* that swap commit, the app is a strict improvement,
already fitness-checked before it went live, and — because the old
component still sits untouched and unimported in the tree until §12.9's
separate cleanup step — a single `git revert` of that one commit is a
complete, instant rollback to the old known-good diagram if a
late-discovered bug ever shows up in it, with no reconstruction needed.
Either way, "would this be ready to submit right now" is true by
construction, not by remembering to check it.

**The same shape, restated as a checklist, applies to every tier above
and to work sessions generally, not only to 12.A:** it is always safe to
stop between tiers, and it is just as safe to stop mid-tier, provided the
single most recent commit satisfies all four of the following — treat
this as the one thing to verify before walking away at any point, no
matter how little of a tier is done:

- [ ] The app actually builds (`npm run build`, or whatever this
      project's real build command is — don't trust that it would build).
- [ ] Every route still loads and every Phase 0–11 acceptance behavior
      this phase's own §12.10 says must survive still works — a quick
      pass, not the full suite, if time is genuinely critical.
- [ ] Reduced motion still produces a correct, complete-looking static
      state (§12.5.7's own check, or the pre-existing behavior if
      `LoopFlowScene` isn't live yet).
- [ ] Nothing new on screen is a lie — no fabricated ID, no dead button,
      no half-wired control that looks interactive but isn't (ADR-4,
      still the least negotiable rule in the whole document).

Commit at that granularity — a working tree after every small,
independently-verifiable change — rather than saving one large commit
for the end of a tier. A tier boundary is a good place to also update
`PROGRESS.md`; it is not the only place it's safe to stop.

---

## 12.15 Skill reference sheet (Revision 2) — one table, checkable at a glance

Everything below is already stated in context at the relevant section
above (§12.2.1 first introduces each one); this table exists so the
requirement is checkable in one place without hunting through the whole
document, the same reason `H.67` gathered the scattered anti-pattern list
into one numbered checklist instead of leaving it distributed across five
sections.

| Skill | Verdict | When / how | Governing section |
|---|---|---|---|
| `review-animations` | **Required** | Run against `LoopFlowScene` at the end of 12.A, and again against the nav underline in 12.F/§12.8.1. Treat a Block verdict as a blocking item. | §12.2.1.1, §12.5.7, §12.12 step 7 |
| `emil-design-eng` | **Required** | Consult while defining the shared `MOTION_EASE` constant in §12.8.5. | §12.2.1.1, §12.8.5 |
| `design-taste-frontend` | **Required, Home only** | Run its redesign/audit mode against the Home hero + pillar-card row after §12.6. Never against Identify/Generate/Defend/Loop — out of its documented scope. | §12.2.1.1, §12.6, §12.11.1 |
| `gsap-react` | **Technique only, no install** | Read for the interruptible-timeline / scoped-ref mental model; implement with Motion's `useAnimate()`. Never run `npm install gsap`. | §12.2.1.2 |
| `stitch-design-taste` | **Do not invoke** | Targets a different tool's pipeline; its default motion posture contradicts §12.10. | §12.2.1.2, §12.10 |
| `image-to-code` | **Optional, exploratory only** | Reference-image-then-discard, never adapt generated markup. First thing to cut under time pressure. | §12.2.1.2, §12.14 |
| `pick-ui-library` | **Do not invoke** | No open library decision exists — ADR-1 through ADR-5 already made it. | §12.2.1.2 |
| `ask-sonner` | **Not relevant** | `Toast` is a locked custom abstraction (`H.4.6`); out of this phase's scope entirely. | §12.2.1.3 |
| `imagegen-frontend-web` / `-mobile` / `brandkit` | **Not relevant** | Concept-image generators for an unlocked visual identity; AFL's has been locked since Phase 1. | §12.2.1.3 |
| `python-appservice-deploy` / `azure-upgrade` | **Not relevant** | Backend/infra tooling, no frontend surface area. | §12.2.1.3 |
| `find-skills` | **Not relevant** | Meta-discovery only; this table already resolves the question it would answer. | §12.2.1.3 |

---

## 12.16 Revision 4 — independent verification and research addendum

Everything in this section is either a direct measurement taken against
this exact codebase, or a check of a specific, checkable external claim —
not general commentary. It supports sections above rather than changing
them; nothing here overrides anything in §12.0–§12.17.

### 12.16.1 The bundle diagnosis in §12.1.2, re-measured from a clean install

Ran `npm install` against this project's actual `package.json`/lockfile,
then a real production build (`npm run build`, i.e. `tsc -b && vite
build`), and inspected the output the same way §12.1.2 did. Every figure
still holds, and the specific evidence §12.1.2 cites for *why* — not just
the top-line sizes — reproduces exactly:

```text
grep -o "react-flow\|reactflow" dist/assets/kpi-tile-*.js | sort | uniq -c
     48 react-flow
      5 reactflow
```

That is the identical 48/5 split §12.1.2 reports, from an independent
build. The chunk sizes moved by well under 1% run-to-run (hash/minifier
noise, not a real change) — `kpi-tile` still ships at ~129.7KB raw /
~41.1KB gzip with React Flow inside it, `defend-page` still correctly
isolates Recharts at ~386.5KB raw / ~107.8KB gzip, and `grep -rn "from
\"reactflow\"" src/` still returns exactly the one hit in
`loop-diagram.tsx` §12.1.2 names. Treat §12.1.2's diagnosis as current,
not stale — the phrase "this snapshot may already have moved on" in
§12.1's own opening does not apply here; it hasn't moved.

### 12.16.2 The `motion/react` import, verified against the real package

Detailed inline at §12.9 step 6; the verification steps, for the record:
`node -e "require.resolve('motion/react')"` against this project's real
`node_modules` throws `MODULE_NOT_FOUND` (no `motion` package is
installed — only `framer-motion`). `node -e "const m = require('framer-
motion'); console.log(Object.keys(m))"` against the same install confirms
`framer-motion@13.1.1`'s root export already includes `LazyMotion`,
`domAnimation`, `domMax`, and `m` directly. The fix is importing from the
package that's actually there.

### 12.16.3 The 88 vs. 96 node-size contradiction — detail

Flagged inline at §12.5.1. The pre-Phase-12 `LegNode` (the component
`loop-diagram.tsx` currently ships, and the one this phase's ADR-1 says to
port into `LoopFlowScene`) renders its bordered box as a plain
`motion.div` with `width: 88, height: 88` — not a 96px outer frame with an
88px box inside it. The file's own settled-state pulse ring computes its
position as `LEG_META[legId].position.x + 44 - 60` (`44` = half of `88`),
which only produces a correctly-centered ring if the node really is 88,
not 96 — i.e. the *rest of the same file* is internally consistent with
88 throughout, not just the one dimension. This document's §12.5.1 cites
`H.16.4` as locking 96 as "the final decision," a document not available
for cross-check here. Both things can't be true of the code as it
currently exists. Resolve this against the actual `H.16.4` text before
`LoopFlowScene` is built, not by assumption in either direction, and if
96 turns out to be correct, re-derive every other constant in the file
that currently assumes 88 (pulse-ring offset math at minimum; check for
others before assuming that's the only one) rather than changing only the
headline size.

### 12.16.4 A concrete `MOTION_EASE` value, sourced from code already in this app

§12.8.5 asks for "a cubic-bezier in the 'confident, slightly decelerating'
family already implied by `count-up.tsx`'s existing `easeOut` cubic" but
doesn't give a number. `count-up.tsx` implements its count-up easing
directly in JS as `1 - Math.pow(1 - t, 3)` — the standard "ease-out cubic"
curve, whose cubic-bezier equivalent (as used by, e.g., Framer Motion's
own named easing presets and easings.net's reference set) is
`cubic-bezier(0.33, 1, 0.68, 1)`. Define `MOTION_EASE` as exactly that
value. It isn't a new aesthetic choice — it's the precise curve this app
already uses for its most numbers-forward existing animation, made
reusable instead of re-derived.

### 12.16.5 A concrete technique for §12.8.6.4's "don't shrink below ~280×280" rule

Tailwind v4 ships native container-query support in core (confirmed
current as of v4.3, no plugin needed): `@container` on the ancestor,
`@sm:`/`@md:` etc. on descendants querying that container's width, and —
directly useful here — `@max-*` variants for the inverse ("apply this
when the container is *smaller* than a breakpoint"), plus container query
length units (`cqw`/`cqh`/`cqi`/`cqb`) for fluid sizing tied to the
container rather than the viewport. Concretely: wrap `LoopFlowScene`'s
slot in `@container`, and instead of leaving "min ~280px" as a prose
instruction, express it directly — e.g. `min-w-[280px] min-h-[280px]` on
the scene's own root plus a `@max-[320px]:` variant on the tick-mark
trace pattern and node labels (per §12.5.2's Revision-2 tiled-pattern
implementation) to drop the ruled-scale texture and shrink label text
specifically once the container itself has actually gotten that narrow —
querying the diagram's own box, not the page viewport, which is exactly
right for a component that can sit inside the Loop page's narrow-width
stack (§12.8.6.4) at a different width than it renders at on Home.

### 12.16.6 Concrete performance targets, tied to this project's own existing budget

§12.9 step 3 already asks for a before/after bundle comparison; that's a
*relative* check. Google's Core Web Vitals give a stable, external
*absolute* bar, unchanged since INP replaced FID in March 2024 and still
current: **LCP ≤ 2.5s "good"** (loading), **INP ≤ 200ms "good"**
(responsiveness), **CLS ≤ 0.1 "good"** (visual stability), each measured
at the 75th percentile of real sessions. Use these as the actual pass/fail
line for Home and Loop in §12.12 step 6's Lighthouse pass, rather than
only "smaller than before." Worth stating plainly because this project
has already committed to a stricter, more specific version of the same
idea: Phase 11's `PROGRESS.md` entry logged a **measured 5.4–6.5s
cold-start**, explicitly to fit "the 3-minute judge window defined by
FRONTEND_VISION §1.1." A Home page that clears LCP/INP/CLS's general
"good" bar but reintroduces meaningful load delay via this phase's own
new animation work would be a regression against a number this project
already measured and already committed to publicly in its own submission
notes — §12.9's performance work is in service of that already-logged
constraint, not a new one invented for this revision.

### 12.16.7 §12.11's structural framing, re-checked

§12.11 and §12.11.1's read of Wiz's Security Graph, Darktrace's Threat
Visualizer, Datadog's density-and-precision instinct, and Stripe's
micro-interaction restraint — persistent structure lit up by a real
signal, a real-time feed with a confirmed-anomaly beat, numeric density,
and consistency over any single flashy effect — still holds as the
correct structural read of each product's current public material. No
correction needed here; this entry exists only so a reader checking every
`(Revision 4)` marker for a substantive change knows this one was
verified and left as-is, not skipped.

