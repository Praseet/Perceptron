// Phase 8 - features/defend/confusion-heatmap.tsx
// Per the spec:
//   "ConfusionHeatmap - small (240px), rows = fraud_type, columns
//    = predicted label, cells colored on a scale from
//    --color-bg-muted to --color-risk-critical, normalized per
//    row, with the numeric count always printed in the cell text
//    (never color alone, per Accessibility Standards)."
//
// Driven by getEvalConfusion() data. Empty/Loading/Error states.

import { Skeleton } from "../../design-system/primitives";
import { AlertCircle } from "../../design-system/icons";
import type { ConfusionResponse } from "../../lib/api/types";

interface ConfusionHeatmapProps {
  data: ConfusionResponse | undefined;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
}

// Map a normalized row-percentage (0-1) to a color. The lower
// the percentage, the closer to the muted background; the
// higher, the closer to --color-risk-critical.
function colorForRowPct(pct: number): string {
  // Use a small inline interpolation. We can't use oklch() or any
  // CSS color-mix() in the spec (H.5.4 forbids gradients, and
  // color-mix is a separate utility) so we step through the 3-tier
  // risk spectrum defined in index.css.
  if (pct >= 0.7) return "var(--risk-critical)";
  if (pct >= 0.4) return "var(--risk-medium)";
  if (pct >= 0.15) return "var(--risk-low)";
  return "var(--bg-elevated)";
}

function textColorForBg(bgVar: string): string {
  if (bgVar === "var(--risk-critical)" || bgVar === "var(--risk-medium)") {
    return "var(--text-primary)";
  }
  return "var(--text-secondary)";
}

// Display label for a fraud type. Strip the underscores and
// keep it mono.
function labelFor(fraudType: string): string {
  return fraudType.replace(/_/g, " ");
}

export function ConfusionHeatmap({ data, isLoading, isError, errorMessage }: ConfusionHeatmapProps) {
  if (isLoading) {
    return (
      <div className="space-y-1" aria-busy="true" aria-label="Loading confusion heatmap">
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <Skeleton key={i} className="h-7 w-full" />
        ))}
      </div>
    );
  }
  if (isError) {
    return (
      <div role="alert" className="flex items-start gap-2 rounded-[var(--radius-input)] border border-[var(--risk-critical)] bg-[var(--bg-base)] p-3">
        <AlertCircle aria-hidden className="mt-0.5 flex-shrink-0" style={{ color: "var(--risk-critical)" }} />
        <p className="text-[0.75rem] text-[var(--risk-critical)]">{errorMessage ?? "Could not load confusion data."}</p>
      </div>
    );
  }
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-[0.75rem] text-[var(--text-muted)] py-6">
        No confusion data.
      </div>
    );
  }
  // Per-row max for normalization. The H.2.15 endpoint returns
  // total per row; the spec says "normalized per row", so the
  // largest single value in the row is 100% on the color scale.
  return (
    <div className="space-y-2">
      <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
        Confusion by fraud type (rows normalized; counts in every cell)
      </p>
      <table className="w-full text-[0.75rem] border-collapse">
        <thead>
          <tr>
            <th
              scope="col"
              className="text-left text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1 w-[42%]"
            >
              Fraud type
            </th>
            <th
              scope="col"
              className="text-center text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1 w-[29%]"
            >
              predicted legit
            </th>
            <th
              scope="col"
              className="text-center text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1 w-[29%]"
            >
              predicted fraud
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const rowMax = Math.max(row.predicted_legit, row.predicted_fraud, 1);
            const legitPct = row.predicted_legit / rowMax;
            const fraudPct = row.predicted_fraud / rowMax;
            const legitBg = colorForRowPct(legitPct);
            const fraudBg = colorForRowPct(fraudPct);
            return (
              <tr key={row.fraud_type} className="border-t border-[var(--border-subtle)]">
                <td className="px-2 py-1.5 text-[var(--text-primary)] font-mono">
                  {labelFor(row.fraud_type)}
                </td>
                <td className="p-1">
                  <div
                    className="rounded-[var(--radius-input)] px-2 py-1.5 text-center font-mono tabular-nums"
                    style={{
                      backgroundColor: legitBg,
                      color: textColorForBg(legitBg),
                    }}
                    aria-label={`predicted legit: ${row.predicted_legit} of ${row.total}`}
                  >
                    {row.predicted_legit}
                  </div>
                </td>
                <td className="p-1">
                  <div
                    className="rounded-[var(--radius-input)] px-2 py-1.5 text-center font-mono tabular-nums"
                    style={{
                      backgroundColor: fraudBg,
                      color: textColorForBg(fraudBg),
                    }}
                    aria-label={`predicted fraud: ${row.predicted_fraud} of ${row.total}`}
                  >
                    {row.predicted_fraud}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
