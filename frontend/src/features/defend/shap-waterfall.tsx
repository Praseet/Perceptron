// Phase 8 - features/defend/shap-waterfall.tsx
// SHAP waterfall. Per the spec: horizontal bar chart via Recharts,
// signed contributions from the predict() response's shap array,
// colored by SIGN not by feature identity (positive-toward-fraud
// in --color-risk-high, negative in --color-risk-low - re-read
// the spec's explicit instruction on this; a chart that colors
// each bar by which feature it is, rather than which direction it
// pushes the prediction, would be a legible-but-wrong reading
// of "signed contributions").
// Top 10 features by |value|, descending. tabular-nums on the
// value labels (H.68.1). Empty/Loading/Error states.

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LabelList,
} from "recharts";
import { Skeleton } from "../../design-system/primitives";
import { AlertCircle } from "../../design-system/icons";
import type { PredictResult } from "../../lib/api/types";

interface ShapWaterfallProps {
  prediction: PredictResult | null;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
}

interface ShapRow {
  feature: string;
  magnitude: number;
  sign: "positive" | "negative";
  value: number;
}

function buildRows(shap: PredictResult["shap"]): ShapRow[] {
  return [...shap]
    .map((f) => ({
      feature: f.feature,
      magnitude: Math.abs(f.value),
      sign: f.impact,
      value: f.value,
    }))
    .sort((a, b) => b.magnitude - a.magnitude)
    .slice(0, 10);
}

export function ShapWaterfall({ prediction, isLoading, isError, errorMessage }: ShapWaterfallProps) {
  if (isLoading) {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Loading SHAP values">
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-6 w-1/2" />
      </div>
    );
  }
  if (isError) {
    return (
      <div role="alert" className="flex items-start gap-2 rounded-[var(--radius-input)] border border-[var(--risk-critical)] bg-[var(--bg-base)] p-3">
        <AlertCircle aria-hidden className="mt-0.5 flex-shrink-0" style={{ color: "var(--risk-critical)" }} />
        <p className="text-[0.75rem] text-[var(--risk-critical)]">{errorMessage ?? "Predict failed."}</p>
      </div>
    );
  }
  if (!prediction || prediction.shap.length === 0) {
    return (
      <div className="text-center text-[0.75rem] text-[var(--text-muted)] py-6">
        Submit a transaction to see its top SHAP features.
      </div>
    );
  }
  const rows = buildRows(prediction.shap);
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          Top SHAP features (signed, by |value|)
        </p>
        <div className="flex items-center gap-3 text-[0.625rem] font-mono">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: "var(--risk-high)" }} aria-hidden />
            <span className="text-[var(--text-muted)]">toward fraud</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: "var(--risk-low)" }} aria-hidden />
            <span className="text-[var(--text-muted)]">toward legit</span>
          </span>
        </div>
      </div>
      <div style={{ width: "100%", height: 240 }}>
        <ResponsiveContainer>
          <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 32, left: 4, bottom: 4 }}>
            <XAxis
              type="number"
              tick={{ fontSize: 10, fill: "var(--text-muted)" }}
              stroke="var(--border-subtle)"
              className="font-mono tabular-nums"
            />
            <YAxis
              type="category"
              dataKey="feature"
              tick={{ fontSize: 10, fill: "var(--text-secondary)" }}
              stroke="var(--border-subtle)"
              width={120}
              className="font-mono"
            />
            <Tooltip
              cursor={{ fill: "var(--bg-elevated)" }}
              contentStyle={{
                backgroundColor: "var(--bg-elevated)",
                border: "1px solid var(--border-strong)",
                fontSize: 11,
                fontFamily: "var(--font-mono)",
                color: "var(--text-primary)",
              }}
              formatter={(_value, _name, item) => {
                const sign = (item.payload as ShapRow).sign;
                const signed = (item.payload as ShapRow).value;
                return [
                  sign === "negative" ? `−${Math.abs(signed).toFixed(3)}` : `+${Math.abs(signed).toFixed(3)}`,
                  "SHAP",
                ];
              }}
            />
            <Bar dataKey="magnitude" radius={[0, 3, 3, 0]}>
              {rows.map((r, i) => (
                <Cell
                  key={i}
                  fill={r.sign === "negative" ? "var(--risk-low)" : "var(--risk-high)"}
                />
              ))}
              <LabelList
                dataKey="value"
                position="right"
                className="font-mono tabular-nums"
                style={{ fontSize: 10, fill: "var(--text-secondary)" }}
                formatter={(v) => `${Number(v) >= 0 ? "+" : "−"}${Math.abs(Number(v)).toFixed(3)}`}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
