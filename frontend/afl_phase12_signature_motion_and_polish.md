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

A one-time entrance is still allowed and is a good idea, but it must be
**fast and complete, not staged**: the whole topology (all four nodes, all
four traces) may fade+scale in together over ~300–400ms on first mount,
using a single `useInView`/mount trigger — never sequenced node-by-node.
Skip this entirely under reduced motion (render the final state
immediately, per `H.23.1`'s existing pattern).

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
   interface from a template-grade one.
2. **Re-run the `H.68` icon and tabular-nums rules against everything this
   phase touches** — any new numeric display (ambient-mode labels, new
   delta indicators) must use `tabular-nums`; any new icon usage must go
   through the existing locked `design-system/icons.ts` wrapper, not a
   fresh Lucide import with its own stroke width.

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
exactly as `H.1` already requires project-wide.

---

## 12.14 If time runs out — minimum viable checkpoints

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

At every checkpoint above, the app must be left in a state that is fully
working end to end — never stop mid-change with something visibly broken.
This is the same standard the rest of this build bible already holds
itself to, and it matters more, not less, the closer the deadline gets.
