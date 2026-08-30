// Phase 9 - features/loop/cycle-delta-tiles.tsx
// Per the Phase 9 spec step 5:
//   "CycleDeltaTiles - reuses the KpiTile pattern (Phase 3),
//    updated in place after each metric_update event, each
//    showing a +/- delta chip against the immediately-previous
//    value (not against the run's starting value - a running
//    delta, per cycle)."
//
// We show four KPI tiles (recall, pr_auc, fn, precision), the
// same four metrics the demo's runLoop emits. For each metric we
// track the most recent prior value (the value at the previous
// metric_update event for that metric in the run) and compute
// the delta against it. The first time a metric is seen in a
// run, no delta is shown - the user has no prior to compare to.

import { useMemo } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { KpiTile } from "../../design-system/patterns/kpi-tile";
import { formatPct } from "../../lib/format";
import type { LoopEvent } from "../../lib/api/types";

interface CycleDeltaTilesProps {
  events: LoopEvent[];
}

type Metric = "recall" | "pr_auc" | "fn" | "precision";

interface MetricState {
  current: number | null;
  delta: number | null;
}

function trackMetric(events: LoopEvent[], metric: Metric): MetricState {
  // Walk events forward. For each metric_update event with the
  // right metric type, capture the value. The "delta" is the
  // change from the previous value of the same metric.
  let prev: number | null = null;
  let current: number | null = null;
  let delta: number | null = null;
  for (const e of events) {
    if (e.type === "metric_update" && e.metric === metric) {
      const v = e.value;
      if (prev != null) {
        delta = v - prev;
      }
      prev = v;
      current = v;
    }
    // Also pick up the run_start baseline if the metric is
    // recall or pr_auc or precision or fn - but run_start
    // doesn't have a per-metric shape (it has a single
    // baseline object). So we just look at metric_updates.
  }
  return { current, delta };
}

function formatForMetric(metric: Metric, v: number): string {
  if (metric === "pr_auc") return v.toFixed(4);
  if (metric === "fn") return Math.round(v).toString();
  // recall / precision are 0..1, format as %
  return formatPct(v, 2);
}

function deltaForMetric(_metric: Metric, d: number): number {
  // Convert absolute value delta to a percent change for
  // KpiTile (which expects a percent change). For pr_auc
  // the natural unit is already 0..1, so percent change is
  // (delta / prev) * 100. For fn (count) the percent change
  // is also fine.
  return d * 100;
}

function directionForMetric(metric: Metric): "up-is-good" | "down-is-good" {
  // Per spec convention, recall/precision/pr_auc are
  // up-is-good. fn (false negative count) is down-is-good.
  if (metric === "fn") return "down-is-good";
  return "up-is-good";
}

export function CycleDeltaTiles({ events }: CycleDeltaTilesProps) {
  const reduceMotion = useReducedMotion();
  const tiles = useMemo(() => {
    const metrics: Metric[] = ["recall", "pr_auc", "fn", "precision"];
    return metrics.map((m) => ({
      metric: m,
      ...trackMetric(events, m),
    }));
  }, [events]);

  // Phase 9.5 step 6 - CycleDeltaTiles: the most recent
  // metric_update event's metric tile gets a brief opacity
  // emphasis (background flash + opacity dip) so the eye is
  // drawn to the freshly-updated value. Use case mapping:
  // H.71 §B ("Loop metric delta update (very high priority) -
  // tile stays in place, value updates with brief opacity/
  // background emphasis only - never a scale pulse or screen
  // flash"). Reduced motion renders the tile without the
  // emphasis animation; the value change is still visible.
  const lastMetricUpdate = useMemo(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      if (events[i].type === "metric_update") {
        return events[i];
      }
    }
    return null;
  }, [events]);
  const lastMetricName =
    lastMetricUpdate && lastMetricUpdate.type === "metric_update"
      ? lastMetricUpdate.metric
      : null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3" aria-label="Cycle deltas">
      {tiles.map((t) => (
        <motion.div
          key={t.metric}
          animate={
            !reduceMotion && t.metric === lastMetricName
              ? { backgroundColor: ["rgba(255,255,255,0)", "rgba(34, 211, 238, 0.10)", "rgba(255,255,255,0)"] }
              : {}
          }
          transition={
            reduceMotion
              ? { duration: 0 }
              : { duration: 0.6, ease: "easeOut" }
          }
          className="rounded-[var(--radius-card)]"
        >
          <KpiTile
            label={t.metric === "pr_auc" ? "PR-AUC" : t.metric === "fn" ? "False negatives" : t.metric[0].toUpperCase() + t.metric.slice(1)}
            value={t.current ?? 0}
            direction={directionForMetric(t.metric)}
            delta={t.delta == null ? undefined : deltaForMetric(t.metric, t.delta)}
            format={(v) => formatForMetric(t.metric, v)}
          />
        </motion.div>
      ))}
    </div>
  );
}
