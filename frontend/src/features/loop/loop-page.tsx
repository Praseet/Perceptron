// Phase 9 - features/loop/loop-page.tsx
// The real Loop page. Replaces the Phase 5 placeholder.
//
// Phase 12 (§12.7) - the page's own state machine drives the diagram:
//   IDLE     -> LoopFlowScene mode="ambient" (auto-playing on mount)
//   RUNNING  -> mode="live" events={run.events}
//   SETTLING -> live showing the final state, ~1.75s hold
//   IDLE     -> back to ambient (the loop closes)
// Everything else (LoopControls, CycleTimeline, CycleDeltaTiles,
// RunHistoryTable, use-loop) is unchanged. H.18.5's acceptance
// criteria are preserved exactly: the Run button still disables while
// a run is active, two simultaneous streams are still impossible, the
// aria-live status summary and CycleTimeline rows are unchanged, and
// RunHistoryTable still gets a new row on run_complete.

import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { LoopControls } from "./loop-controls";
import { CycleTimeline } from "./cycle-timeline";
import { CycleDeltaTiles } from "./cycle-delta-tiles";
import { RunHistoryTable } from "./run-history-table";
import { useLoopHistory, useRunLoop } from "./use-loop";

import type { LoopHistoryEntry, LoopRunRequest } from "../../lib/api/types";

// Phase 12 (§12.6 + §12.9 step 2): LoopFlowScene is its own React.lazy
// boundary, independent of KpiTile and of the page route chunks.
const LoopFlowScene = lazy(() =>
  import("../../design-system/patterns/loop-flow-scene").then((m) => ({
    default: m.LoopFlowScene,
  })),
);

// §12.5.5: after run_complete, hold the final state long enough to read
// it, then hand the page back to the ambient loop.
const SETTLE_MS = 1750;

const HEADER_TITLE = "Loop";
const HEADER_SUBTITLE =
  "Generate adversarial examples from the current model's misses, add them to the training set, retrain, measure the delta. Each cycle takes ~30-60s on the dataset's current scale.";
const HEADER_STEP = "Step 4 of 4";

export function LoopPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  // ?prefill=1cycle is set by the global nav's "Run the loop"
  // button (Phase 5). Capture the value ONCE at first mount via
  // useRef (see PROGRESS.md - reading it on every render triggered
  // a React 19 + strict-mode re-init loop).
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

  // Phase 12 §12.7 state machine. `run.isStreaming` is RUNNING;
  // once a terminal event lands, SETTLING holds the live scene for
  // SETTLE_MS so the final state is readable, then back to IDLE
  // (ambient). The settle timer is cancelled by a new run starting.
  const [settled, setSettled] = useState(false);
  const phase: "idle" | "running" | "settling" = run.isStreaming
    ? "running"
    : run.isComplete
      ? "settling"
      : "idle";
  useEffect(() => {
    if (phase !== "settling") {
      setSettled(false);
      return;
    }
    const t = setTimeout(() => setSettled(true), SETTLE_MS);
    return () => clearTimeout(t);
  }, [phase]);
  const sceneMode: "ambient" | "live" =
    phase === "running" || (phase === "settling" && !settled) ? "live" : "ambient";

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

      {/* Phase 10 layout fix: the live diagram on the left, the cycle
          timeline on the right, and the four delta tiles in their own
          full-width 4-column row below. Phase 12: the diagram is now
          LoopFlowScene, wrapped in the same .console instrument surface
          the Home hero uses (one consistent frame for the signature
          scene), with an honest mode caption beneath it. */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        <div>
          <div className="console border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[0.625rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
                closed loop
              </span>
              <span className="text-[0.625rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
                {sceneMode === "live" ? "live run" : "ambient preview"}
              </span>
            </div>
            <Suspense
              fallback={
                <div
                  style={{
                    aspectRatio: "1 / 1",
                    background: "var(--bg-panel)",
                    border: "1px solid var(--border-subtle)",
                  }}
                />
              }
            >
              <LoopFlowScene
                mode={sceneMode}
                events={run.events}
                ambientLabels={false}
              />
            </Suspense>
          </div>
          <p className="mt-2 text-[0.625rem] font-mono text-[var(--text-muted)] text-center">
            {sceneMode === "live"
              ? "Reacting to the real run in progress."
              : "Illustrative preview - press Run for a live cycle."}
          </p>
        </div>
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
