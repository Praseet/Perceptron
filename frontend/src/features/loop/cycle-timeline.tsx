// Phase 9 - features/loop/cycle-timeline.tsx
// Per the Phase 9 spec step 4:
//   "CycleTimeline - a vertical list, one row per SSE event
//    (not one row per cycle - every individual event), each
//    with a timestamp (via lib/format.ts), a one-line
//    description derived from the event's type and payload,
//    and a delta chip where the event type is metric_update.
//    On stream disconnection mid-run, render a final row:
//    'Connection lost - showing results through the last
//    received cycle,' per 'Empty, Loading, and Error States'
//    above - never hang on a spinner (there are no spinners in
//    this codebase) or leave the timeline silently frozen with
//    no explanation."
//
// Empty state: the timeline renders an EmptyState before any
// events. After the first event, the list renders.

import { Card } from "../../design-system/primitives";
import { EmptyState } from "../../design-system/patterns/empty-state";
import { Inbox, AlertTriangle } from "../../design-system/icons";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { formatRelative } from "../../lib/format";
import type { LoopEvent } from "../../lib/api/types";

interface CycleTimelineProps {
  events: LoopEvent[];
  /** True when the stream has disconnected or errored. Renders
   *  the final "Connection lost..." row. */
  streamError?: Error | null;
  /** True when the user has triggered a run but events haven't
   *  started arriving yet. The list is empty but we don't show
   *  the "no cycles yet" empty state. */
  isRunning?: boolean;
}

function formatTime(d: Date): string {
  // HH:MM:SS.mmm - precise enough to be useful, not so long
  // that the row overflows. Mono-friendly.
  const pad = (n: number, w = 2) => n.toString().padStart(w, "0");
  return (
    pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" +
    pad(d.getSeconds()) + "." + pad(d.getMilliseconds(), 3)
  );
}

function eventTimestamp(e: LoopEvent): Date {
  if (e.type === "run_start") {
    return new Date(e.started_at);
  }
  return new Date();
}


function eventDescription(e: LoopEvent): string {
  switch (e.type) {
    case "run_start":
      return `Run started (baseline recall ${e.baseline.recall.toFixed(2)}, PR-AUC ${e.baseline.pr_auc.toFixed(4)})`;
    case "cycle_start":
      return `Cycle ${e.cycle} started`;
    case "miss_added":
      return `Cycle ${e.cycle}: ${e.count} new ${e.fraud_type.replace(/_/g, " ")} miss${e.count === 1 ? "" : "es"} synthesized`;
    case "metric_update": {
      // Phase 10 layout fix: previously the description repeated the
      // value (e.g. "Cycle 1: recall 0.83%") AND the right column
      // showed the same number with a sign ("+0.83%"). Two copies of
      // the same value side-by-side was visually noisy and looked
      // like overlapping numbers. The right column already carries
      // the signed value, so the description just labels the metric
      // for context.
      return `Cycle ${e.cycle}: ${e.metric}`;
    }
    case "cycle_end":
      return `Cycle ${e.cycle} ended`;
    case "run_complete":
      return `Run complete (final PR-AUC ${e.final.pr_auc.toFixed(4)}, ${e.n_cycles} cycle${e.n_cycles === 1 ? "" : "s"}, ${e.n_new_attacks} new attacks)`;
    case "error":
      return `Error: ${e.message}`;
    default: {
      const _exhaustive: never = e;
      void _exhaustive;
      return "Unknown event";
    }
  }
}

function eventDelta(e: LoopEvent): string | null {
  if (e.type !== "metric_update") return null;
  const sign = e.value > 0 ? "+" : e.value < 0 ? "−" : "±";
  const unit = e.metric === "fn" ? "" : "%";
  return `${sign}${Math.abs(e.value).toFixed(e.metric === "pr_auc" ? 4 : 2)}${unit}`;
}

export function CycleTimeline({ events, streamError, isRunning }: CycleTimelineProps) {
  const reduceMotion = useReducedMotion();
  if (events.length === 0 && !streamError && !isRunning) {
    return (
      <EmptyState
        icon={<Inbox size="empty" />}
        message="No cycle events yet. Click Run to start a closed-loop pass."
      />
    );
  }


  return (
    <Card className="p-4 space-y-2">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Cycle timeline
        </h3>
        <span className="text-[0.625rem] font-mono text-[var(--text-muted)] tabular-nums">
          {events.length} event{events.length === 1 ? "" : "s"}
        </span>
      </div>
      <ol className="space-y-1.5 max-h-[480px] overflow-y-auto" aria-live="polite">
        {/* Phase 9.5 step 6 - CycleTimeline: each event row enters
            with a restrained fade + small slide. Use case mapping:
            H.71 §A ("Loop timeline event arrival (very high priority)
            - real event -> row fades/short-slides in -> settles, no
            loop, no bounce"). The key uses the event's index in the
            append-only array (events are only appended, never
            reordered or removed in this phase's stream), so
            AnimatePresence can correctly track enter. Reduced
            motion skips the enter animation entirely so the row
            appears already settled. */}
        <AnimatePresence initial={false}>
          {events.map((e, i) => {
            const ts = eventTimestamp(e);
            return (
              <motion.li
                key={i}
                initial={
                  reduceMotion ? false : { opacity: 0, x: -8, height: 0 }
                }
                animate={
                  reduceMotion
                    ? { opacity: 1, x: 0, height: "auto" }
                    : { opacity: 1, x: 0, height: "auto" }
                }
                exit={
                  reduceMotion
                    ? { opacity: 1, x: 0 }
                    : { opacity: 0, x: -8, height: 0 }
                }
                transition={
                  reduceMotion
                    ? { duration: 0 }
                    : { duration: 0.18, ease: "easeOut" }
                }
                className="grid grid-cols-[80px_1fr_auto] items-center gap-2 text-[0.75rem] font-mono overflow-hidden"
              >
                <span className="text-[0.6875rem] text-[var(--text-muted)] tabular-nums">
                  {formatTime(ts)}
                </span>
                <span className="text-[var(--text-secondary)]">{eventDescription(e)}</span>
                {eventDelta(e) ? (
                  <span className="text-[0.625rem] font-mono text-[var(--accent-cyan)] tabular-nums">
                    {eventDelta(e)}
                  </span>
                ) : (
                  <span />
                )}
              </motion.li>
            );
          })}
        </AnimatePresence>
        {streamError && (
          <li
            className="grid grid-cols-[80px_1fr_auto] items-center gap-2 text-[0.75rem] font-mono border-t border-[var(--risk-critical)] pt-2 mt-2"
            role="alert"
          >
            <span className="text-[0.6875rem] text-[var(--risk-critical)] tabular-nums">
              {formatTime(new Date())}
            </span>
            <span className="text-[var(--risk-critical)] flex items-center gap-1">
              <AlertTriangle aria-hidden size="inline" />
              Connection lost - showing results through the last received cycle
            </span>
            <span />
          </li>
        )}
      </ol>
      {events.length > 0 && (
        <p className="text-[0.625rem] font-mono text-[var(--text-muted)] pt-2 border-t border-[var(--border-subtle)] tabular-nums">
          last event: {formatRelative(eventTimestamp(events[events.length - 1]).toISOString())}
        </p>
      )}
    </Card>
  );
}
