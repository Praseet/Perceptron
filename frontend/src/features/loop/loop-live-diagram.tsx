// Phase 9 - features/loop/loop-live-diagram.tsx
// Per the Phase 9 spec step 3: a thin wrapper around the shared
// LoopDiagram (Phase 3), rendered with mode="live" and
// interactive={true}, mapping incoming events to activeLeg.
//
// This file owns the LOCKED 7-event mapping (see PROGRESS.md):
//   run_start     -> "identify"
//   cycle_start   -> "generate"
//   miss_added    -> "improve"
//   metric_update -> "defend"
//   cycle_end     -> null
//   run_complete  -> null
//   error         -> null
//
// Implementation note: the wrapper is React.memo'd so that
// passing the same `activeLeg` string on re-renders does NOT
// trigger ReactFlow's internal setState. In Phase 9's first
// build, the diagram was passed the full events array on
// every tick, which caused ReactFlow's viewport store to
// loop and emit "Maximum update depth exceeded" errors. The
// fix: the page computes activeLeg via useMemo([run.events])
// and passes the STRING to this component, so shallow-equal
// comparison short-circuits re-renders when the leg hasn't
// changed.

import { memo, useEffect, useRef, useState } from "react";
import { LoopDiagram, type LegId } from "../../design-system/patterns/loop-diagram";

interface LoopLiveDiagramProps {
  activeLeg: LegId | null;
  className?: string;
}

/**
 * Maps the most recent event to the activeLeg value. Returns
 * `null` when the run is in a between-cycles or done state
 * (per the locked table), in which case the LoopDiagram's
 * settled-state pulse takes over. Exported so the page can use
 * it inside a useMemo.
 */
export function activeLegForEvents(
  events: ReadonlyArray<{ type: string }>,
): LegId | null {
  for (let i = events.length - 1; i >= 0; i--) {
    const e = events[i];
    switch (e.type) {
      case "run_start":
        return "identify";
      case "cycle_start":
        return "generate";
      case "miss_added":
        return "improve";
      case "metric_update":
        return "defend";
      case "cycle_end":
      case "run_complete":
      case "error":
        return null;
      default:
        return null;
    }
  }
  return null;
}

function LoopLiveDiagramInner({ activeLeg, className }: LoopLiveDiagramProps) {
  // The LoopDiagram component renders at a fixed 480x480 internally
  // (Phase 3 lock). On narrow viewports (< 480px) this overflows
  // its parent grid column. We wrap it in a CSS-transform scale
  // that re-measures its container via ResizeObserver, so the
  // diagram fits whatever width the parent gives it. The internal
  // ReactFlow viewport still receives the full 480x480 coordinate
  // space - the outer scale just shrinks the rendered box.
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const el = wrapperRef.current;
    if (!el) return;
    const compute = () => {
      const w = el.clientWidth || 480;
      setScale(Math.min(1, w / 480));
    };
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // The outer wrapper clips (overflow: hidden) so ReactFlow's
  // internal 480x480 coordinate pane cannot push the document's
  // scrollWidth out beyond the viewport - the spec calls out
  // "no horizontal scrollbar appears" at any viewport, and the
  // unscaled-pane bleed is the only remaining offender.
  return (
    <div
      ref={wrapperRef}
      className={className}
      style={{
        width: "100%",
        maxWidth: 480,
        aspectRatio: "1 / 1",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div
        style={{
          width: 480,
          height: 480,
          transform: `scale(${scale})`,
          transformOrigin: "top left",
        }}
      >
        <LoopDiagram mode="live" activeLeg={activeLeg} interactive={true} />
      </div>
    </div>
  );
}

export const LoopLiveDiagram = memo(LoopLiveDiagramInner);
