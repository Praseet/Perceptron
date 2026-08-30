import { useEffect, useMemo, useRef, useState } from "react";
import { ReactFlow, Handle, Position, type Node, type Edge } from "reactflow";
import "reactflow/dist/style.css";
import { motion, useReducedMotion } from "framer-motion";
import {
  Radar,
  GitBranch,
  ShieldCheck,
  TrendingUp,
} from "../icons";

// H.2.6 final implementation decision:
// Semantic order: Identify -> Generate -> Defend -> Improve -> Identify
// Fixed positions: top / right / bottom / left
// Identify = top, Generate = right, Defend = left, Improve = bottom
// Edges routed around the perimeter (smooth-step / orthogonal)
// Animation order: Identify -> Generate -> Defend -> Improve (NOT
// Generate -> Improve -> Defend as the older draft said).

export type LegId = "identify" | "generate" | "defend" | "improve";

interface LoopDiagramProps {
  mode?: "static" | "live"; // default "static"
  activeLeg?: LegId | null; // default null
  interactive?: boolean; // default false
  className?: string;
}

const LEG_META: Record<
  LegId,
  { label: string; tokenColor: string; Icon: typeof Radar; position: { x: number; y: number } }
> = {
  identify: {
    label: "Identify",
    tokenColor: "var(--loop-identify)",
    Icon: Radar,
    position: { x: 240, y: 56 },
  },
  generate: {
    label: "Generate",
    tokenColor: "var(--loop-attack)", // Appendix D name (semantically = "generate attacks")
    Icon: GitBranch,
    position: { x: 424, y: 240 },
  },
  defend: {
    label: "Defend",
    tokenColor: "var(--loop-defend)",
    Icon: ShieldCheck,
    position: { x: 56, y: 240 },
  },
  improve: {
    label: "Improve",
    tokenColor: "var(--loop-improve)",
    Icon: TrendingUp,
    position: { x: 240, y: 424 },
  },
};

// Animation timing (H.2.6 + Phase 3 prompt). 2.4s total, 4 nodes +
// 4 edges. Per H.2.6, the order is Identify -> Generate -> Defend ->
// Improve (Improve lands last, not Defend as the older draft said).
const ANIM_TOTAL_MS = 2400;
const STEP_MS = ANIM_TOTAL_MS / 8; // 0..7: 4 node-appears + 4 edge-appears
const NODE_START: Record<LegId, number> = {
  identify: 0 * STEP_MS,
  generate: 2 * STEP_MS,
  defend: 4 * STEP_MS,
  improve: 6 * STEP_MS,
};
const EDGE_STARTS: Array<{ from: LegId; to: LegId; ms: number }> = [
  { from: "identify", to: "generate", ms: 1 * STEP_MS },
  { from: "generate", to: "defend", ms: 3 * STEP_MS },
  { from: "defend", to: "improve", ms: 5 * STEP_MS },
  { from: "improve", to: "identify", ms: 7 * STEP_MS },
];
const PULSE_MS = 4000;

// ---- Custom node ----
// 88x88 square, 2px leg-color border, --bg-base fill, centered icon
// in the same color, label below in --text-caption. No glow, no blur,
// no transform on hover, no shadow (H.2.4).

function LegNode({ data }: { data: { legId: LegId; active: boolean } }) {
  const meta = LEG_META[data.legId];
  const Icon = meta.Icon;
  const reduceMotion = useReducedMotion();
  // Phase 9.5 step 6 - LoopLiveDiagram: when `active` toggles,
  // animate the inset boxShadow (the active-state indicator)
  // over a short duration. Node dimensions and graph geometry
  // are preserved exactly - only the inset shadow fades in or
  // out. No glow, no particles, no scale. Use case mapping:
  // H.71 §C ("Loop - animate the active-leg state change
  // subtly (opacity/border/fill only), preserving node
  // dimensions and graph geometry exactly, with zero glow/
  // particles/edge-beam effects"). Reduced motion snaps
  // immediately.
  return (
    <motion.div
      style={{
        width: 88,
        height: 88,
        background: "var(--bg-base)",
        border: `2px solid ${meta.tokenColor}`,
        borderRadius: "var(--radius-node)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
      }}
      animate={{
        boxShadow: data.active ? `inset 0 0 0 1px ${meta.tokenColor}` : "inset 0 0 0 0px transparent",
      }}
      transition={
        reduceMotion
          ? { duration: 0 }
          : { duration: 0.22, ease: "easeOut" }
      }
      data-leg={data.legId}
    >
      <Handle type="target" position={Position.Top} style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="target" position={Position.Left} style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0, pointerEvents: "none" }} />
      <Icon size="node" color={meta.tokenColor} aria-hidden />
      <span
        style={{
          fontFamily: "var(--font-sans)",
          fontSize: "0.6875rem",
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          color: "var(--text-muted)",
        }}
      >
        {meta.label}
      </span>
    </motion.div>
  );
}

const nodeTypes = { leg: LegNode };

// ---- Edge style ----
// Leg color in the leg''s own color, smooth-step routing around the
// perimeter. Active edge is thicker. No animated dashes (would read
// as decorative motion).
function makeEdge(
  e: { from: LegId; to: LegId; ms: number },
  legColor: (leg: LegId) => string,
  isActive: (from: LegId, to: LegId) => boolean,
  isVisible: boolean,
): Edge {
  const color = legColor(e.from);
  return {
    id: `${e.from}-${e.to}`,
    source: e.from,
    target: e.to,
    type: "smoothstep",
    animated: false,
    style: {
      stroke: color,
      strokeWidth: isActive(e.from, e.to) ? 2.5 : 1.5,
      opacity: isVisible ? 1 : 0,
      transition: "opacity 200ms ease-out",
    },
  };
}

export function LoopDiagram({
  mode = "static",
  activeLeg = null,
  interactive = false,
  className,
}: LoopDiagramProps) {
  const reduceMotion = useReducedMotion();
  // Animation phase tracking. We start the intro on mount; once the
  // intro completes, the settled pulse takes over per leg.
  const [phase, setPhase] = useState<"intro" | "settled">("intro");
  const [progressMs, setProgressMs] = useState(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  // One-shot intro animation. Skipped entirely under reduced motion.
  useEffect(() => {
    if (reduceMotion) {
      setPhase("settled");
      setProgressMs(ANIM_TOTAL_MS);
      return;
    }
    startRef.current = null;
    const tick = (now: number) => {
      if (startRef.current == null) startRef.current = now;
      const elapsed = now - startRef.current;
      if (elapsed >= ANIM_TOTAL_MS) {
        setProgressMs(ANIM_TOTAL_MS);
        setPhase("settled");
        return;
      }
      setProgressMs(elapsed);
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [reduceMotion]);

  const isNodeVisible = (leg: LegId) => {
    if (reduceMotion) return true;
    return progressMs >= NODE_START[leg];
  };

  const isEdgeVisible = (e: { ms: number }) => {
    if (reduceMotion) return true;
    return progressMs >= e.ms;
  };

  const legColor = (leg: LegId) => LEG_META[leg].tokenColor;
  const isActiveEdge = (from: LegId, to: LegId) =>
    activeLeg != null && (from === activeLeg || to === activeLeg);

  const nodes: Node[] = useMemo(
    () =>
      (Object.keys(LEG_META) as LegId[]).map((legId) => ({
        id: legId,
        type: "leg",
        position: LEG_META[legId].position,
        data: { legId, active: activeLeg === legId },
        // Hide by zero-size + no events until the intro has reached
        // this node. We do not remove the node from the graph so the
        // edge endpoints stay valid; the wrapper handles opacity.
        style: {
          opacity: isNodeVisible(legId) ? 1 : 0,
          pointerEvents: isNodeVisible(legId) ? "auto" : "none",
        },
      })),
    // progressMs / activeLeg intentionally drive re-render
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activeLeg, progressMs, reduceMotion],
  );

  const edges: Edge[] = useMemo(
    () =>
      EDGE_STARTS.map((e) => makeEdge(e, legColor, isActiveEdge, isEdgeVisible(e))),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activeLeg, progressMs, reduceMotion],
  );

  // The component root applies .console only in mode="live" (H.2.5).
  // In mode="static", the component renders directly on the page''s
  // normal background; no .console, no override.
  return (
    <div
      className={(mode === "live" ? "console " : "") + (className ?? "")}
      style={{
        width: 480,
        height: 480,
        position: "relative",
      }}
      role="img"
      aria-label="Closed loop diagram: Identify, Generate, Defend, Improve"
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={interactive}
        nodesConnectable={false}
        elementsSelectable={interactive}
        // Phase 10 a11y: the wrapping div has role="img" with a
        // single aria-label. ReactFlow's default `tabindex="0"`
        // on every node makes them focusable descendants, which
        // triggers axe rule "Element has focusable descendants"
        // (wcag412 / serious). The diagram is decorative - the
        // meaningful accessible name is on the wrapper. Disable
        // per-node focusability globally; pan/zoom in interactive
        // mode is still available via the ReactFlow viewport
        // container, which is the parent the user already tabs
        // through.
        nodesFocusable={false}
        edgesFocusable={false}
        panOnDrag={interactive}
        panOnScroll={false}
        zoomOnScroll={interactive}
        zoomOnPinch={interactive}
        zoomOnDoubleClick={false}
        minZoom={1}
        maxZoom={1}
        proOptions={{ hideAttribution: true }}
        // The pulse overlay renders the 4s opacity cycle per node in
        // the settled state. Reduced-motion skips it entirely.
      >
        {/* No Background, no Controls - we want a clean static composition. */}
      </ReactFlow>
      {/* Per-leg opacity pulse overlay. Re-renders each leg on its
          own 4s cycle, in its own leg color. Reduced motion renders
          nothing here (the elements below are opacity 1 with no
          animation, which is what the settled state should look like
          in static anyway). */}
      {!reduceMotion &&
        phase === "settled" &&
        (Object.keys(LEG_META) as LegId[]).map((legId) => (
          <motion.div
            key={legId + "-pulse"}
            aria-hidden="true"
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.25, 0] }}
            transition={{
              duration: PULSE_MS / 1000,
              repeat: Infinity,
              ease: "easeInOut",
            }}
            style={{
              position: "absolute",
              left: LEG_META[legId].position.x + 44 - 60,
              top: LEG_META[legId].position.y + 44 - 60,
              width: 120,
              height: 120,
              borderRadius: "var(--radius-node)",
              border: `2px solid ${LEG_META[legId].tokenColor}`,
              pointerEvents: "none",
            }}
          />
        ))}
    </div>
  );
}