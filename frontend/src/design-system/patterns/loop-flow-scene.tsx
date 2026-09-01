// Phase 12 (12.A) - design-system/patterns/loop-flow-scene.tsx
//
// ADR-1: hand-built SVG replacement for the React-Flow-based
// `loop-diagram.tsx`. No graph library - four nodes and four traces at
// coordinates known ahead of time never needed one, and removing React
// Flow is what makes the bundle fix in §12.9 possible at all.
//
// ADR-2: exactly two modes. "ambient" plays automatically on mount and
// shows the GENERALIZED loop using only real, already-displayed
// aggregate numbers (ADR-4). "live" is driven by the real LoopEvent
// stream and shows the specific run in progress. No third mode.
//
// ADR-3: token motion is manual path sampling - getPointAtLength()
// driven by a single requestAnimationFrame loop - not CSS offset-path.
// All animated properties are transform / opacity / plain SVG
// attributes; nothing forces layout (§12.9 step 4).
//
// Geometry per §12.5.1 + H.16.4's FINAL decision: 96x96 nodes (the old
// component's 88 was stale - §12.16.3 confirmed against the real
// H.16.4 text), at the same four centers the old diagram used, in the
// same 480x480 viewBox (§12.5.1: keep the existing coordinate system).
//
// §12.5.2.1 Bug B: every node rect is positioned with half-offset math
// (x = center.x - 48) because SVG <rect> positions from its top-left
// corner - the exact bug class this phase was written to avoid.
//
// §12.5.2.1 Bug A: the component renders an explicit skeleton styled
// with the real --bg-panel token for the gap between mount and the
// first ResizeObserver size report, then crossfades (never a hard cut,
// never a black box).

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Radar, GitBranch, ShieldCheck, TrendingUp } from "../icons";
import { MOTION_EASE, MOTION_EASE_CSS, MOTION_FAST_MS } from "../motion";
import type { LoopEvent } from "../../lib/api/types";
import type { LegId } from "../../lib/constants";

export type { LegId };
// ---------------------------------------------------------------------------
// Props (ADR-1's compatibility contract)
// ---------------------------------------------------------------------------

export interface LoopFlowSceneProps {
  mode: "ambient" | "live";
  /** Kept for call-site compatibility until 12.C rewires the Loop page;
   *  drives the subtle node-border emphasis only. */
  activeLeg?: LegId | null;
  /** Live mode reads real event data directly (ADR-4: nothing invented). */
  events?: LoopEvent[];
  /** Now means "hover/focus affordances enabled", not pan/zoom. */
  interactive?: boolean;
  /** Ambient mode shows real aggregate numbers as the cycle punchline.
   *  On /loop's idle state those same numbers read as if they describe
   *  the current (non-existent) run - misleading - so the Loop page
   *  passes false. Default true (Home). */
  ambientLabels?: boolean;
  className?: string;
}

// ---------------------------------------------------------------------------
// Geometry (§12.5.1 - keep exactly; node size 96 per H.16.4 final decision)
// ---------------------------------------------------------------------------

const VIEW = 480;
const NODE = 96;
const HALF = NODE / 2; // 48 - the one number every centered element derives from

const CENTERS: Record<LegId, { x: number; y: number }> = {
  identify: { x: 240, y: 56 },
  generate: { x: 424, y: 240 },
  defend: { x: 56, y: 240 },
  improve: { x: 240, y: 424 },
};

type TraceId = "i2g" | "g2d" | "d2i" | "b2t";

interface TraceDef {
  id: TraceId;
  from: LegId;
  to: LegId;
  /** Full token-sampling path (may pass through a node interior). */
  d: string;
  /** Optional stroke override when the visible rail must exclude the
   *  through-node passage (the token still samples the full d). */
  visibleD?: string;
  segs: Array<{ x1: number; y1: number; x2: number; y2: number; dir: "h" | "v" }>;
}

// Orthogonal, right-angled traces (§12.5.2): top -> right -> bottom ->
// left -> top, routed through the empty corridors between node bands.
// i2g takes the top-right corner L; g2d takes the y=144 corridor and
// enters Defend from ABOVE (so the Beat-3 gate is a horizontal line the
// cluster crosses, per §12.5.3's "short horizontal threshold line");
// d2i takes the bottom-left corner L; b2t returns up the x=332
// corridor. The single crossing at (332,144) is topologically forced
// for this ring and reads as ordinary PCB routing at 0.35 opacity.
const TRACES: TraceDef[] = [
  {
    id: "i2g",
    from: "identify",
    to: "generate",
    d: "M 288 56 H 424 V 192",
    segs: [
      { x1: 296, y1: 56, x2: 416, y2: 56, dir: "h" },
      { x1: 424, y1: 64, x2: 424, y2: 184, dir: "v" },
    ],
  },
  {
    id: "g2d",
    from: "generate",
    to: "defend",
    d: "M 400 192 V 144 H 56 V 192",
    segs: [
      { x1: 400, y1: 200, x2: 400, y2: 152, dir: "v" },
      { x1: 392, y1: 144, x2: 64, y2: 144, dir: "h" },
      { x1: 56, y1: 152, x2: 56, y2: 184, dir: "v" },
    ],
  },
  {
    id: "d2i",
    from: "defend",
    to: "improve",
    d: "M 56 288 V 424 H 192",
    segs: [
      { x1: 56, y1: 296, x2: 56, y2: 416, dir: "v" },
      { x1: 64, y1: 424, x2: 184, y2: 424, dir: "h" },
    ],
  },
  {
    id: "b2t",
    from: "improve",
    to: "identify",
    // Token-sampling path starts at the point the divert token actually
    // stands on (Improve's left edge, y=424) and travels straight through
    // the node - no teleport. visibleD is the stroke: only the part
    // outside the node (the same rail language as every other trace).
    d: "M 192 424 H 332 V 88 H 288",
    visibleD: "M 288 424 H 332 V 88 H 288",
    segs: [
      { x1: 296, y1: 424, x2: 324, y2: 424, dir: "h" },
      { x1: 332, y1: 416, x2: 332, y2: 96, dir: "v" },
      { x1: 324, y1: 88, x2: 296, y2: 88, dir: "h" },
    ],
  },
];

// Virtual measurement-only paths (no visible stroke): the "caught" tail
// a majority token fades out along just past the gate, and the full
// divert route a missed token takes through Defend and down to Improve.
const CAUGHT_D = "M 56 192 V 264";
const DIVERT_D = "M 56 192 V 424 H 192";

// The Beat-3 gate (§12.5.3): a short horizontal threshold line sitting
// just above Defend's top edge that every cluster passes through on its
// way in. This is the single most important beat of the whole sequence.
const GATE = { x1: 36, y1: 178, x2: 76, y2: 178 };

// ---------------------------------------------------------------------------
// Timing (§12.5.4 ambient script: ~6s cycle + ~4.5s pause; §12.5.5 live
// travel sized so spawn -> gate -> feedback fits a 3-5s event window)
// ---------------------------------------------------------------------------

const TRAVEL_MS = 1400;
const HOLD_MS = 260; // Beat 2 materialize hold at Generate - short: a beat, not a dead stop
const DIVERT_MS = 1400; // gate -> Improve (through the node)
const INCORPORATE_PARK_MS = 420; // token pause at Improve before departing - brief
const LOOP_MS = 1250; // Improve -> Identify (longest leg: ~520px through-node)
const AMBIENT_PERIOD_MS = 10_500; // ~6s of motion + ~4.5s pause
const CLUSTER = 5; // a cluster, not a crowd (§12.9 step 4 cap)
const CLUSTER_STAGGER_MS = 110;
const POOL = 10; // hard cap on concurrent token elements
const GATE_FLASH_MS = 400;
const PULSE_MS = 300; // metric_update node pulse (<=300ms per §12.5.5)
const CYCLE_LABEL_MS = 1800;
const CAUGHT_MS = 800; // caught-tail fade: fully resolved before the token vanishes

// Real, already-trusted numbers (ADR-4). Sources:
// - 1,390 = sum of FRAUD_TYPE_TARGETS, displayed on Home's KPI row
//   (hero-kpi-row.tsx ATTACKS_GENERATED_TOTAL - reused, not reinvented).
// - recall 0.8200 -> 0.8467 and FN 34 -> 32 = the CHANGELOG deltas as
//   already written in numbers-that-hold-up.tsx ("real numbers, no
//   fabrication"). These are the ambient loop's punchline every cycle.
const ATTACKS_GENERATED_TOTAL = 1_390;
const AMBIENT_RECALL_LABEL = "recall 0.8200 \u2192 0.8467";
const AMBIENT_FN_LABEL = "FN 34 \u2192 32";
const AMBIENT_GEN_LABEL = `${ATTACKS_GENERATED_TOTAL.toLocaleString("en-US")} attacks generated`;
const AMBIENT_IMPROVE_LABEL = "misses \u2192 training set";

const LEG_META: Record<
  LegId,
  { label: string; color: string; Icon: typeof Radar }
> = {
  identify: { label: "Identify", color: "var(--loop-identify)", Icon: Radar },
  generate: { label: "Generate", color: "var(--loop-attack)", Icon: GitBranch },
  defend: { label: "Defend", color: "var(--loop-defend)", Icon: ShieldCheck },
  improve: { label: "Improve", color: "var(--loop-improve)", Icon: TrendingUp },
};

const TRACE_COLOR: Record<TraceId, string> = {
  i2g: "var(--loop-identify)",
  g2d: "var(--loop-attack)",
  d2i: "var(--loop-defend)",
  b2t: "var(--loop-improve)",
};



// ---------------------------------------------------------------------------
// Motion engine (ADR-3): one requestAnimationFrame loop samples every
// active token along its SVGPathElement via getPointAtLength and applies
// transform/opacity/fill directly to the DOM - no React re-render per
// frame, no CSS offset-path, no layout-forcing properties (§12.9 step 4).
// ---------------------------------------------------------------------------

type TokLeg = "i2g" | "g2d" | "divert" | "caught" | "b2t";
type TokState = "travel" | "hold" | "waitGate" | "incorporate" | "done";

interface Tok {
  slot: number;
  idx: number; // index within its cluster; idx 0 is the diverted one
  leg: TokLeg;
  state: TokState;
  t0: number;
  dur: number;
  holdUntil: number;
  missed: boolean;
  forceClear: boolean;
}

interface LabelSpec {
  el: SVGTextElement | null;
  t0: number;
  holdMs: number;
  visible: boolean;
}

interface EngineDeps {
  slotEls: Array<SVGGElement | null>;
  slotRects: Array<SVGRectElement | null>;
  paths: Record<string, SVGPathElement | null>;
  gateEl: SVGLineElement | null;
  pulseEls: Record<LegId, SVGRectElement | null>;
  labels: {
    gen: SVGTextElement | null;
    improve1: SVGTextElement | null;
    improve2: SVGTextElement | null;
    cycle: SVGTextElement | null;
    divert: SVGTextElement | null;
  };
  modeRef: { current: "ambient" | "live" };
  ambientLabelsRef: { current: boolean };
}

const TOKEN_COLOR: Record<TokLeg, string> = {
  i2g: "var(--loop-identify)",
  g2d: "var(--loop-attack)",
  divert: "var(--loop-improve)",
  b2t: "var(--loop-improve)",
  caught: "var(--text-muted)", // muted/desaturated - correctly handled, story over
};

function clamp01(v: number): number {
  return v < 0 ? 0 : v > 1 ? 1 : v;
}

// Travel distance curve: trapezoid velocity profile - brief ramp-up
// (12%), cruise, soft landing (25%). Continuous velocity at every
// junction: no launch burst (the ease-out-quad this replaces started
// every leg at 2x speed, which read as tokens "sprinting" out of the
// gate and out of Improve), no dead stop at arrival.
function travelEase(p: number): number {
  const q = clamp01(p);
  const A = 0.12; // ramp-up fraction
  const B = 0.25; // landing fraction
  const norm = 1 - (A + B) / 2; // trapezoid covers less distance than a unit-velocity line
  let d: number;
  if (q < A) {
    d = (q * q) / (2 * A);
  } else if (q < 1 - B) {
    d = A / 2 + (q - A);
  } else {
    const s = (q - (1 - B)) / B; // 0..1 across the landing zone
    d = A / 2 + (1 - B - A) + B * (s - (s * s) / 2);
  }
  return d / norm;
}


function pointAt(
  path: SVGPathElement,
  len: number,
  p: number,
): { x: number; y: number } {
  const pt = path.getPointAtLength(clamp01(p) * len);
  return { x: pt.x, y: pt.y };
}

function labelOpacity(l: LabelSpec, now: number): number {
  if (!l.visible || !l.el) return 0;
  const t = now - l.t0;
  if (t < 0) return 0;
  const IN = 150;
  const OUT = 300;
  if (t < IN) return t / IN;
  if (l.holdMs !== Infinity && t > l.holdMs) {
    return Math.max(0, 1 - (t - l.holdMs) / OUT);
  }
  return 1;
}

function createEngine(deps: EngineDeps) {
  const toks: Tok[] = [];
  const freeSlots: number[] = [];
  for (let i = POOL - 1; i >= 0; i--) freeSlots.push(i);
  const lens: Record<string, number> = {};
  let missPending = false;
  let divertText: string | null = null; // live: "{count} x {fraud type}"
  let nextCycleAt = Infinity;
  let prevMode = deps.modeRef.current;
  let gateFlashT0 = -1;
  let gateOp = 0; // smoothed gate visibility (proximity-driven)
  const pulses: Record<"defend" | "improve", number> = { defend: -1, improve: -1 };

  const labels: Record<"gen" | "improve1" | "improve2" | "cycle" | "divert", LabelSpec> = {
    gen: { el: deps.labels.gen, t0: 0, holdMs: 0, visible: false },
    improve1: { el: deps.labels.improve1, t0: 0, holdMs: 0, visible: false },
    improve2: { el: deps.labels.improve2, t0: 0, holdMs: 0, visible: false },
    cycle: { el: deps.labels.cycle, t0: 0, holdMs: 0, visible: false },
    divert: { el: deps.labels.divert, t0: 0, holdMs: 0, visible: false },
  };

  function setLabel(l: LabelSpec, text: string | null, now: number, holdMs: number) {
    if (text == null) {
      l.visible = false;
      return;
    }
    if (l.el && l.el.textContent !== text) l.el.textContent = text;
    l.t0 = now;
    l.holdMs = holdMs;
    l.visible = true;
  }

  function hideAllLabels(now: number) {
    for (const key of Object.keys(labels) as Array<keyof typeof labels>) {
      setLabel(labels[key], null, now, 0);
      if (labels[key].el) labels[key].el.setAttribute("opacity", "0");
    }
  }

  function applySlotStyle(slot: number, leg: TokLeg, variant: "outline" | "filled") {
    const rect = deps.slotRects[slot];
    if (!rect) return;
    const color = TOKEN_COLOR[leg];
    if (variant === "outline") {
      rect.setAttribute("fill", "var(--bg-base)");
      rect.setAttribute("stroke", color);
      rect.setAttribute("stroke-width", "1.5");
    } else {
      rect.setAttribute("fill", color);
      rect.setAttribute("stroke", "none");
    }
  }

  function startLeg(t: Tok, leg: TokLeg, now: number, dur: number) {
    t.leg = leg;
    t.state = "travel";
    t.t0 = now;
    t.dur = dur;
  }

  // Beat 3 - the gate (§12.5.3): on crossing the threshold, the cluster
  // SPLITS. The one missed token turns improve-green and takes the
  // feedback trace; the majority fade out muted just past the line.
  function split(t: Tok, now: number) {
    if (t.missed && missPending) {
      startLeg(t, "divert", now, DIVERT_MS);
      applySlotStyle(t.slot, "divert", "filled");
      if (t.idx === 0 && deps.modeRef.current === "live" && divertText) {
        setLabel(labels.divert, divertText, now, DIVERT_MS + 300);
      }
    } else {
      startLeg(t, "caught", now, CAUGHT_MS);
      applySlotStyle(t.slot, "caught", "filled");
    }
  }

  function spawnCluster(now: number) {
    missPending = deps.modeRef.current === "ambient";
    for (let i = 0; i < CLUSTER; i++) {
      const slot = freeSlots.pop();
      if (slot == null) break;
      toks.push({
        slot,
        idx: i,
        leg: "i2g",
        state: "travel",
        t0: now + i * CLUSTER_STAGGER_MS,
        dur: TRAVEL_MS,
        holdUntil: 0,
        missed: i === 0,
        forceClear: false,
      });
      applySlotStyle(slot, "i2g", "outline");
    }
  }

  function releaseAll() {
    for (const t of toks) {
      const g = deps.slotEls[t.slot];
      if (g) g.setAttribute("opacity", "0");
      freeSlots.push(t.slot);
    }
    toks.length = 0;
  }

  function advance(t: Tok, now: number) {
    switch (t.leg) {
      case "i2g": {
        // Beat 2 - MATERIALIZE: brief hold at Generate while the count
        // label updates, then continue as transactions (fill change).
        t.state = "hold";
        t.holdUntil = now + HOLD_MS;
        if (
          t.idx === 0 &&
          deps.modeRef.current === "ambient" &&
          deps.ambientLabelsRef.current
        ) {
          setLabel(labels.gen, AMBIENT_GEN_LABEL, now, HOLD_MS + 800);
        }
        break;
      }
      case "g2d": {
        gateFlashT0 = now;
        if (t.forceClear) {
          startLeg(t, "caught", now, CAUGHT_MS);
          applySlotStyle(t.slot, "caught", "filled");
        } else if (missPending) {
          split(t, now);
        } else {
          t.state = "waitGate"; // parked at the threshold until the real miss_added lands
        }
        break;
      }
      case "caught":
        t.state = "done";
        break;
      case "divert": {
        // Beat 4 - FEEDBACK: the node pulses (same treatment Defend gets
        // on metric_update - one consistent vocabulary across all four
        // boxes) and the tied numeric consequence shows (§12.5.6).
        pulses.improve = now;
        if (deps.modeRef.current === "ambient") {
          if (deps.ambientLabelsRef.current) {
            setLabel(labels.improve1, AMBIENT_RECALL_LABEL, now, 2800);
            setLabel(labels.improve2, AMBIENT_FN_LABEL, now, 2800);
          }
          t.state = "incorporate";
          t.holdUntil = now + INCORPORATE_PARK_MS;
        } else {
          setLabel(labels.improve1, AMBIENT_IMPROVE_LABEL, now, 2200);
          setLabel(labels.improve2, null, now, 0);
          t.state = "done";
        }
        break;
      }
      case "b2t":
        t.state = "done";
        break;
    }
  }


  function frame(now: number) {
    // Mode transitions (ADR-2): live preempts ambient instantly; live ->
    // ambient releases live leftovers and starts the calm loop again.
    const mode = deps.modeRef.current;
    if (mode !== prevMode) {
      if (mode === "live") {
        nextCycleAt = Infinity;
      } else {
        releaseAll();
        hideAllLabels(now);
        nextCycleAt = now + 700;
      }
      prevMode = mode;
    }

    // Ambient scheduling (§12.5.4): auto-plays, loops on a calm interval.
    // The scheduler never queues a backlog: if the tab was hidden and the
    // schedule went stale, it just waits for the next tick.
    if (mode === "ambient" && now >= nextCycleAt) {
      spawnCluster(now);
      nextCycleAt = now + AMBIENT_PERIOD_MS;
    }

    // Tokens.
    for (let i = toks.length - 1; i >= 0; i--) {
      const t = toks[i];
      const g = deps.slotEls[t.slot];
      if (!g || !deps.slotRects[t.slot]) {
        toks.splice(i, 1);
        continue;
      }
      if (t.state === "done") {
        g.setAttribute("opacity", "0");
        freeSlots.push(t.slot);
        toks.splice(i, 1);
        continue;
      }
      if (t.state === "hold") {
        if (now >= t.holdUntil) {
          startLeg(t, "g2d", now, TRAVEL_MS);
          applySlotStyle(t.slot, "g2d", "filled");
        }
        continue;
      }
      if (t.state === "incorporate") {
        if (now >= t.holdUntil) {
          startLeg(t, "b2t", now, LOOP_MS);
          applySlotStyle(t.slot, "b2t", "outline");
        }
        continue;
      }
      if (t.state === "waitGate") {
        // gentle "under review" breathe while parked at the threshold -
        // stops the instant the split resolves (state indication, not
        // ambient decoration; interrupts cleanly by construction).
        const breathe = 0.75 + 0.25 * Math.sin((now / 1600) * Math.PI * 2);
        g.setAttribute("opacity", breathe.toFixed(3));
        continue;
      }
      if (now < t.t0) {
        g.setAttribute("opacity", "0");
        continue;
      }
      const path = deps.paths[t.leg];
      if (!path) continue;
      if (lens[t.leg] == null) lens[t.leg] = path.getTotalLength();
      const len = lens[t.leg];
      const p = clamp01((now - t.t0) / t.dur);
      const d = travelEase(p);
      const pos = pointAt(path, len, d);
      g.setAttribute("transform", `translate(${pos.x.toFixed(2)} ${pos.y.toFixed(2)})`);
      let op = 1;
      if (t.leg === "i2g" && p < 0.08) op = p / 0.08; // soft spawn, no pop-in
      // Generate handoff (user-locked): no cube motion inside the node -
      // the token fades out as it lands, holds hidden (the materialize
      // beat is carried by the label), and fades in already moving on
      // the g2d rail. No direction change shown inside the block.
      if (t.leg === "i2g" && p > 0.9) op = Math.min(op, (1 - p) / 0.1);
      if (t.leg === "g2d" && p < 0.1) op = p / 0.1;
      if (t.leg === "caught") op = 1 - p; // fade out along the caught tail
      if (t.leg === "b2t" && p > 0.7) op = (1 - p) / 0.3; // fully faded by arrival
      g.setAttribute("opacity", op.toFixed(3));
      if (p >= 1) advance(t, now);
    }

    // Gate visibility (function made legible): the Beat-3 threshold line
    // exists only in the moments tokens interact with it - fading in as
    // the cluster approaches, flashing at the split, fading away after.
    // Never static furniture.
    let gateProx = 0;
    for (const t of toks) {
      if (t.leg === "g2d") {
        const p = t.state === "waitGate" ? 1 : clamp01((now - t.t0) / t.dur);
        if (p > 0.7) gateProx = Math.max(gateProx, (p - 0.7) / 0.3);
      } else if (t.leg === "divert" || t.leg === "caught") {
        const p = clamp01((now - t.t0) / t.dur);
        if (p < 0.35) gateProx = Math.max(gateProx, 1 - p / 0.35);
      }
    }
    let gateBoost = 0;
    if (gateFlashT0 >= 0) {
      const e = (now - gateFlashT0) / GATE_FLASH_MS;
      gateBoost = e >= 1 ? 0 : 1 - Math.abs(2 * e - 1);
      if (e >= 1) gateFlashT0 = -1;
    }
    if (deps.gateEl) {
      const target = Math.max(gateProx, gateBoost);
      gateOp += (target - gateOp) * (target > gateOp ? 0.3 : 0.08);
      const v = Math.min(1, gateOp * 0.7 + gateBoost * 0.6);
      deps.gateEl.setAttribute("stroke-opacity", v.toFixed(3));
    }

    // Node pulses (<=300ms, opacity only - §12.5.5): Defend on
    // metric_update, Improve on divert arrival. Same mechanic, same
    // timing - one vocabulary.
    for (const leg of ["defend", "improve"] as const) {
      const t0 = pulses[leg];
      const el = deps.pulseEls[leg];
      if (t0 < 0) continue;
      const e = (now - t0) / PULSE_MS;
      if (el) {
        el.setAttribute(
          "opacity",
          e >= 1 ? "0" : (0.9 * (1 - Math.abs(2 * e - 1))).toFixed(3),
        );
      }
      if (e >= 1) pulses[leg] = -1;
    }

    // Labels (fade in 150ms, hold, fade out 300ms).
    for (const key of Object.keys(labels) as Array<keyof typeof labels>) {
      const l = labels[key];
      if (l.el) l.el.setAttribute("opacity", labelOpacity(l, now).toFixed(3));
    }
  }


  // Live mode event-to-visual mapping (§12.5.5). Only fields present on
  // the real LoopEvent union are used (ADR-4: no fabricated identifiers,
  // no invented counts - the token label is the event's own fraud_type
  // and count, formatted with the existing convention).
  function handleEvent(e: LoopEvent) {
    const now = performance.now();
    switch (e.type) {
      case "run_start":
        releaseAll();
        hideAllLabels(now);
        missPending = false;
        nextCycleAt = Infinity;
        break;
      case "cycle_start":
        missPending = false;
        spawnCluster(now);
        setLabel(labels.cycle, `Cycle ${e.cycle}`, now, CYCLE_LABEL_MS);
        break;
      case "miss_added":
        // THE dramatic beat (§12.5.3): the real trigger for "some cases
        // were missed". Tokens parked at the gate split now; tokens still
        // in flight will split when they arrive (never more than one
        // beat behind - §12.5.5's interruptibility note).
        missPending = true;
        divertText = `${e.count} \u00d7 ${e.fraud_type.replace(/_/g, " ")}`;
        for (const t of toks) {
          if (t.state === "waitGate") split(t, now);
        }
        break;
      case "metric_update":
        // Defend node settle pulse, synced to the same event instant the
        // CycleDeltaTiles flash on (§12.5.6).
        pulses.defend = now;
        break;
      case "cycle_end":
        // In-flight tokens finish their current leg, then clear; parked
        // ones clear now. Settle point, NOT an active leg (locked map).
        for (const t of toks) {
          if (t.state === "waitGate") {
            startLeg(t, "caught", now, CAUGHT_MS);
            applySlotStyle(t.slot, "caught", "filled");
          } else if (t.state === "travel" || t.state === "hold") {
            t.forceClear = true;
          }
        }
        break;
      case "run_complete":
        setLabel(
          labels.improve1,
          `final PR-AUC ${e.final.pr_auc.toFixed(4)}`,
          now,
          Infinity,
        );
        setLabel(
          labels.improve2,
          `${e.n_cycles} cycles \u00b7 ${e.n_new_attacks} new attacks`,
          now,
          Infinity,
        );
        break;
      case "error":
        setLabel(labels.improve1, "run stopped", now, Infinity);
        setLabel(labels.improve2, null, now, 0);
        break;
    }
  }

  // First frame: ambient starts after one short beat; live waits for
  // run_start. prevMode starts equal to the current mode, so no
  // spurious transition fires on mount.
  if (deps.modeRef.current === "ambient") nextCycleAt = performance.now() + 700;

  return { frame, handleEvent };
}


// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function LoopFlowScene({
  mode,
  activeLeg = null,
  events,
  interactive = false,
  ambientLabels = true,
  className,
}: LoopFlowSceneProps) {
  const reduceMotion = useReducedMotion();
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const [sizeKnown, setSizeKnown] = useState(false);

  const pathRefs = useRef<Record<string, SVGPathElement | null>>({});
  const slotEls = useRef<Array<SVGGElement | null>>(Array(POOL).fill(null));
  const slotRects = useRef<Array<SVGRectElement | null>>(Array(POOL).fill(null));
  const gateRef = useRef<SVGLineElement | null>(null);
  const pulseRefs = useRef<Record<LegId, SVGRectElement | null>>({
    identify: null,
    generate: null,
    defend: null,
    improve: null,
  });
  const labelRefs = useRef<{
    gen: SVGTextElement | null;
    improve1: SVGTextElement | null;
    improve2: SVGTextElement | null;
    cycle: SVGTextElement | null;
    divert: SVGTextElement | null;
  }>({ gen: null, improve1: null, improve2: null, cycle: null, divert: null });
  const engineRef = useRef<ReturnType<typeof createEngine> | null>(null);
  const modeRef = useRef(mode);
  modeRef.current = mode;
  const ambientLabelsRef = useRef(ambientLabels);
  ambientLabelsRef.current = ambientLabels;
  const lastEventIdx = useRef(0);

  // §12.5.2.1 Bug A: one skeleton for the mount -> first-size gap, then a
  // single ~180ms crossfade. Never a black box, never a hard cut.
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    if (el.clientWidth > 0) {
      setSizeKnown(true);
      return;
    }
    const ro = new ResizeObserver(() => {
      if (el.clientWidth > 0) setSizeKnown(true);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Engine lifecycle (§12.9 step 4: the rAF loop is cancelled on unmount -
  // the same unsubscribe-on-cleanup discipline use-loop.ts documents).
  useEffect(() => {
    if (reduceMotion) return; // static resting state, no engine at all
    const engine = createEngine({
      slotEls: slotEls.current,
      slotRects: slotRects.current,
      paths: pathRefs.current,
      gateEl: gateRef.current,
      pulseEls: pulseRefs.current,
      labels: labelRefs.current,
      modeRef,
      ambientLabelsRef,
    });
    engineRef.current = engine;
    let raf = 0;
    const loop = (now: number) => {
      engine.frame(now);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      engineRef.current = null;
    };
  }, [reduceMotion]);

  // Live mode: feed new events to the engine as they arrive. The index
  // resets if the events array is replaced wholesale (a new run starts
  // with a fresh array per use-loop.ts's setEvents([])).
  useEffect(() => {
    const engine = engineRef.current;
    if (!engine || !events) return;
    if (events.length < lastEventIdx.current) lastEventIdx.current = 0;
    for (let i = lastEventIdx.current; i < events.length; i++) {
      engine.handleEvent(events[i]);
    }
    lastEventIdx.current = events.length;
  }, [events]);

  const legs = Object.keys(CENTERS) as LegId[];

  return (
    <div
      ref={wrapRef}
      role="img"
      aria-label="Closed loop diagram: Identify, Generate, Defend, Improve"
      className={className}
      style={{
        position: "relative",
        width: "100%",
        maxWidth: VIEW,
        aspectRatio: "1 / 1",
        margin: "0 auto",
      }}
    >
      {/* Bug A skeleton - styled with the real panel token, crossfaded out */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          background: "var(--bg-panel)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-card)",
          opacity: sizeKnown ? 0 : 1,
          transition: `opacity ${MOTION_FAST_MS}ms ${MOTION_EASE_CSS}`,
          pointerEvents: "none",
        }}
      />
      <motion.svg
        viewBox={`0 0 ${VIEW} ${VIEW}`}
        width="100%"
        height="100%"
        aria-hidden
        className={interactive ? "lfs-interactive" : undefined}
        initial={reduceMotion ? false : { opacity: 0, scale: 0.985 }}
        animate={
          reduceMotion
            ? undefined
            : { opacity: sizeKnown ? 1 : 0, scale: sizeKnown ? 1 : 0.985 }
        }
        transition={{ duration: 0.35, ease: MOTION_EASE }}
        style={{
          display: "block",
          transformOrigin: "center",
          opacity: reduceMotion ? 1 : undefined,
        }}
      >
        {/* Persistent topology (§12.5.2): all four traces fully visible
            immediately. Base stroke + tick marks via ONE dashed line per
            straight segment - the same ruled-scale tiling the spec's
            <pattern> note asks for, with zero extra DOM nodes. */}
        {TRACES.map((t) => (
          <g key={t.id}>
            <path
              ref={(el) => {
                pathRefs.current[t.id] = el;
              }}
              d={t.visibleD ?? t.d}
              fill="none"
              stroke={TRACE_COLOR[t.id]}
              strokeOpacity={0.35}
              strokeWidth={1.25}
            />
            {t.segs.map((s, i) => (
              <line
                key={i}
                x1={s.x1}
                y1={s.y1}
                x2={s.x2}
                y2={s.y2}
                stroke={TRACE_COLOR[t.id]}
                strokeOpacity={0.45}
                strokeWidth={5}
                strokeDasharray="1 9"
              />
            ))}
          </g>
        ))}

        {/* Beat-3 gate: the horizontal threshold line above Defend */}
        <line
          ref={gateRef}
          x1={GATE.x1}
          y1={GATE.y1}
          x2={GATE.x2}
          y2={GATE.y2}
          stroke="var(--loop-defend)"
          strokeOpacity={0.55}
          strokeWidth={1.5}
        />

        {/* Measurement-only virtual paths (invisible; sampled by the engine) */}
        <path ref={(el) => { pathRefs.current.caught = el; }} d={CAUGHT_D} fill="none" stroke="none" />
        <path ref={(el) => { pathRefs.current.divert = el; }} d={DIVERT_D} fill="none" stroke="none" />

        {/* Nodes - 96x96 per H.16.4, positioned with half-offset math
            (Bug B: <rect> positions from its top-left corner). */}
        {legs.map((leg) => {
          const m = LEG_META[leg];
          const c = CENTERS[leg];
          const isActive = activeLeg === leg;
          return (
            <g key={leg} data-leg={leg}>
              <rect
                x={c.x - HALF}
                y={c.y - HALF}
                width={NODE}
                height={NODE}
                fill="var(--bg-base)"
                stroke={m.color}
                strokeWidth={2}
                strokeOpacity={isActive ? 1 : 0.85}
              />
              {/* pulse / emphasis overlay (opacity-only, H.71 §C-safe) */}
              <rect
                ref={(el) => {
                  pulseRefs.current[leg] = el;
                }}
                x={c.x - HALF}
                y={c.y - HALF}
                width={NODE}
                height={NODE}
                fill="none"
                stroke={m.color}
                strokeWidth={2}
                opacity={0}
              />
              <m.Icon size="node" x={c.x - 13} y={c.y - 26} color={m.color} aria-hidden />
              <text
                x={c.x}
                y={c.y + 20}
                textAnchor="middle"
                fontSize={9}
                fontFamily="var(--font-mono)"
                letterSpacing="0.08em"
                fill="var(--text-secondary)"
              >
                {m.label.toUpperCase()}
              </text>
            </g>
          );
        })}

        {/* Real-number labels (ADR-4: nothing invented) */}
        <text
          ref={(el) => { labelRefs.current.gen = el; }}
          x={368}
          y={236}
          textAnchor="end"
          fontSize={9}
          fontFamily="var(--font-mono)"
          fill="var(--text-secondary)"
          opacity={0}
        >
          {AMBIENT_GEN_LABEL}
        </text>
        <text
          ref={(el) => { labelRefs.current.improve1 = el; }}
          x={296}
          y={412}
          fontSize={9}
          fontFamily="var(--font-mono)"
          fill="var(--text-primary)"
          opacity={0}
        >
          {AMBIENT_RECALL_LABEL}
        </text>
        <text
          ref={(el) => { labelRefs.current.improve2 = el; }}
          x={296}
          y={426}
          fontSize={9}
          fontFamily="var(--font-mono)"
          fill="var(--text-secondary)"
          opacity={0}
        >
          {AMBIENT_FN_LABEL}
        </text>
        <text
          ref={(el) => { labelRefs.current.cycle = el; }}
          x={296}
          y={60}
          fontSize={9}
          fontFamily="var(--font-mono)"
          letterSpacing="0.08em"
          fill="var(--text-secondary)"
          opacity={0}
        />
        <text
          ref={(el) => { labelRefs.current.divert = el; }}
          x={84}
          y={172}
          fontSize={9}
          fontFamily="var(--font-mono)"
          fill="var(--loop-improve)"
          opacity={0}
        />

        {/* Token pool - fixed max (§12.9 step 4 cap); the engine drives
            transform/opacity/fill directly, React never re-renders. */}
        {Array.from({ length: POOL }, (_, i) => (
          <g
            key={i}
            ref={(el) => {
              slotEls.current[i] = el;
            }}
            opacity={0}
            aria-hidden
          >
            <rect
              ref={(el) => {
                slotRects.current[i] = el;
              }}
              x={-4.5}
              y={-4.5}
              width={9}
              height={9}
              rx={1}
              fill="var(--bg-base)"
              stroke="var(--loop-identify)"
              strokeWidth={1.5}
            />
          </g>
        ))}
      </motion.svg>
    </div>
  );
}

