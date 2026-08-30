// Phase 9 - features/loop/loop-page.tsx
// The real Loop page. Replaces the Phase 5 placeholder.
//
// Per the Phase 9 spec step 7:
//   "loop-page.tsx - composes the header (exact copy),
//    LoopControls, the left-60%/right-40% split
//    (LoopLiveDiagram + CycleTimeline on the left,
//    CycleDeltaTiles on the right), and RunHistoryTable
//    full-width below. Ensure a run's completion appends a
//    new row to the visible run history immediately (whether
//    that's via TanStack Query cache invalidation
//    triggering a refetch of getLoopHistory(), or an
//    optimistic local append - either is fine, pick one and
//    be consistent)."

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { LoopControls } from "./loop-controls";
import {
  LoopLiveDiagram,
  activeLegForEvents,
} from "./loop-live-diagram";
import { CycleTimeline } from "./cycle-timeline";
import { CycleDeltaTiles } from "./cycle-delta-tiles";
import { RunHistoryTable } from "./run-history-table";
import { useLoopHistory, useRunLoop } from "./use-loop";

import type { LoopHistoryEntry, LoopRunRequest } from "../../lib/api/types";

const HEADER_TITLE = "Loop";
const HEADER_SUBTITLE =
  "Generate adversarial examples from the current model's misses, add them to the training set, retrain, measure the delta. Each cycle takes ~30-60s on the dataset's current scale.";
const HEADER_STEP = "Step 4 of 4";

export function LoopPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  // ?prefill=1cycle is set by the global nav's "Run the loop"
  // button (Phase 5). When present, default max-cycles to 1
  // and strip the param so a back-button doesn't re-prefill.
  // ?prefill=1cycle is set by the global nav's "Run the loop"
  // button (Phase 5). Capture the value ONCE at first mount via
  // useRef. Reading it on every render triggers React 19 +
  // strict-mode re-init when our setSearchParams effect fires
  // and changes the URL from /loop?prefill=1cycle back to
  // /loop. With useRef, the captured value is stable for the
  // lifetime of the LoopPage instance; subsequent renders see
  // the same 1 even after prefill becomes null in the URL.
  const initialMaxCyclesRef = useRef<1 | 3 | 5>(
    searchParams.get("prefill") === "1cycle" ? 1 : 3,
  );
  const initialMaxCycles = initialMaxCyclesRef.current;
  useEffect(() => {
    if (searchParams.get("prefill")) {
      const next = new URLSearchParams(searchParams);
      next.delete("prefill");
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const historyQuery = useLoopHistory();
  const run = useRunLoop();
  // Local "this session" history. Prepended on run_complete so
  // the new row appears immediately (per the spec's "either
  // refetch or optimistic local append" choice - I picked the
  // latter to keep the test deterministic).
  const [recentRuns, setRecentRuns] = useState<LoopHistoryEntry[]>([]);

  // On run_complete, append a new entry.
  useEffect(() => {
    if (!run.isComplete) return;
    const lastEvent = run.events[run.events.length - 1];
    if (!lastEvent || lastEvent.type !== "run_complete") return;
    const entry: LoopHistoryEntry = {
      run_id: lastEvent.run_id,
      started_at: new Date(Date.now() - lastEvent.duration_s * 1000).toISOString(),
      duration_s: lastEvent.duration_s,
      final_pr_auc: lastEvent.final.pr_auc,
      n_cycles: lastEvent.n_cycles,
      n_new_attacks: lastEvent.n_new_attacks,
      // artifact_url omitted in demo (no real artifacts dir).
    };
    setRecentRuns((prev) => {
      // Dedup: don't double-add the same run_id (the effect
      // can re-fire if isComplete changes).
      if (prev.some((r) => r.run_id === entry.run_id)) return prev;
      return [entry, ...prev];
    });
  }, [run.isComplete, run.events]);

  // Combined list: local "this session" first, then the
  // server-side history fixture.
  const allRows = useMemo<LoopHistoryEntry[]>(() => {
    const serverRows = historyQuery.data ?? [];
    // Deduplicate (in case the same run_id appears in both).
    const seen = new Set(recentRuns.map((r) => r.run_id));
    return [...recentRuns, ...serverRows.filter((r) => !seen.has(r.run_id))];
  }, [recentRuns, historyQuery.data]);

  // Phase 9 fix: derive the active leg as a stable primitive value
  // from the events array. This is the single change that closes
  // the "Maximum update depth exceeded" ReactFlow bug - the
  // events array gets a new reference on every SSE/demo tick,
  // but the active-leg STRING usually doesn't change. Passing the
  // primitive into a memo(LoopLiveDiagram) means the diagram
  // short-circuits re-renders on ticks where the active leg
  // hasn't actually changed. See loop-live-diagram.tsx for the
  // locked event-type-to-leg mapping; see PROGRESS.md for the
  // full diagnosis.
  const liveLeg = useMemo(
    () => activeLegForEvents(run.events),
    [run.events],
  );

  function handleRun(req: LoopRunRequest) {
    run.start(req);
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-caption font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          {HEADER_STEP}
        </p>
        <h1 className="text-section-title text-[var(--text-primary)] mt-1">
          {HEADER_TITLE}
        </h1>
        <p className="text-body text-[var(--text-secondary)] mt-2 max-w-full md:max-w-2xl break-words">
          {HEADER_SUBTITLE}
        </p>
      </header>

      <LoopControls
        initialMaxCycles={initialMaxCycles}
        onRun={handleRun}
        isRunning={run.isStreaming}
      />

      {/* Phase 10 layout fix: the previous 3fr/2fr split squeezed the
         four KPI tiles into a 2x2 grid in the narrower right column.
         Each tile's number was cramped and overlapped the delta chip.
         The new layout keeps the live diagram on the left, the cycle
         timeline on the right, and the four delta tiles in their own
         full-width 4-column row below. Each tile now reads cleanly
         with plenty of room and no number collision. */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <LoopLiveDiagram activeLeg={liveLeg} />
        <CycleTimeline
          events={run.events}
          streamError={run.error}
          isRunning={run.isStreaming}
        />
      </div>

      <div className="space-y-4">
        <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Cycle deltas
        </h2>
        <CycleDeltaTiles events={run.events} />
      </div>

      <RunHistoryTable rows={allRows} />
    </div>
  );
}
