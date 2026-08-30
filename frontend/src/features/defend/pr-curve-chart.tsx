// Phase 8 - features/defend/pr-curve-chart.tsx
// Per the spec: "PrCurveChart - Recharts, 400x300, from
// getPrCurve(), with the real operating point marked with a dot
// and a label showing its precision/recall/threshold values."
// No client-side re-computation (per Phase 8 DO-NOT #2). Every
// value shown is read verbatim from the API response.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  CartesianGrid,
} from "recharts";
import { Skeleton } from "../../design-system/primitives";
import { AlertCircle } from "../../design-system/icons";
import type { PrCurveResponse } from "../../lib/api/types";

interface PrCurveChartProps {
  data: PrCurveResponse | undefined;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
}

function buildPoints(data: PrCurveResponse): Array<{ recall: number; precision: number; threshold: number }> {
  return data.precision.map((p, i) => ({
    recall: data.recall[i] ?? 0,
    precision: p,
    threshold: data.thresholds[i] ?? 0,
  }));
}

export function PrCurveChart({ data, isLoading, isError, errorMessage }: PrCurveChartProps) {
  if (isLoading) {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Loading PR curve">
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }
  if (isError) {
    return (
      <div role="alert" className="flex items-start gap-2 rounded-[var(--radius-input)] border border-[var(--risk-critical)] bg-[var(--bg-base)] p-3">
        <AlertCircle aria-hidden className="mt-0.5 flex-shrink-0" style={{ color: "var(--risk-critical)" }} />
        <p className="text-[0.75rem] text-[var(--risk-critical)]">{errorMessage ?? "Could not load PR curve."}</p>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="text-center text-[0.75rem] text-[var(--text-muted)] py-6">
        No PR curve data.
      </div>
    );
  }
  const points = buildPoints(data);
  const op = data.operating_point;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          Precision-Recall curve
        </p>
        <p className="text-[0.625rem] font-mono text-[var(--text-muted)] tabular-nums">
          operating point: <span className="text-[var(--accent-cyan)] tabular-nums">P={(op.precision * 100).toFixed(2)}%</span>
          {" / "}
          <span className="text-[var(--accent-cyan)] tabular-nums">R={(op.recall * 100).toFixed(2)}%</span>
          {" / "}
          <span className="text-[var(--accent-cyan)] tabular-nums">t={op.threshold.toFixed(2)}</span>
        </p>
      </div>
      <div style={{ width: "100%", height: 300 }}>
        <ResponsiveContainer>
          <LineChart data={points} margin={{ top: 12, right: 24, left: 4, bottom: 12 }}>
            <CartesianGrid stroke="var(--border-subtle)" strokeDasharray="2 4" />
            <XAxis
              type="number"
              dataKey="recall"
              domain={[0, 1]}
              tick={{ fontSize: 10, fill: "var(--text-muted)" }}
              stroke="var(--border-subtle)"
              tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
              className="font-mono tabular-nums"
              label={{
                value: "recall",
                position: "insideBottom",
                offset: -4,
                style: { fontSize: 10, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" },
              }}
            />
            <YAxis
              type="number"
              dataKey="precision"
              domain={[0, 1]}
              tick={{ fontSize: 10, fill: "var(--text-muted)" }}
              stroke="var(--border-subtle)"
              tickFormatter={(v: number) => `${Math.round(v * 100)}%`}
              className="font-mono tabular-nums"
              label={{
                value: "precision",
                angle: -90,
                position: "insideLeft",
                style: { fontSize: 10, fill: "var(--text-muted)", fontFamily: "var(--font-mono)" },
              }}
            />
            <Tooltip
              cursor={{ stroke: "var(--accent-cyan)", strokeDasharray: "2 4" }}
              contentStyle={{
                backgroundColor: "var(--bg-elevated)",
                border: "1px solid var(--border-strong)",
                fontSize: 11,
                fontFamily: "var(--font-mono)",
                color: "var(--text-primary)",
              }}
            />
            <Line
              type="monotone"
              dataKey="precision"
              stroke="var(--accent-cyan)"
              dot={false}
              isAnimationActive={false}
            />
            <ReferenceDot
              x={op.recall}
              y={op.precision}
              r={5}
              fill="var(--loop-defend)"
              stroke="var(--bg-base)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="text-[0.6875rem] font-mono text-[var(--text-muted)] tabular-nums">
        Operating point: P={(op.precision * 100).toFixed(2)}%, R={(op.recall * 100).toFixed(2)}%, threshold={op.threshold.toFixed(2)}
      </p>
    </div>
  );
}
