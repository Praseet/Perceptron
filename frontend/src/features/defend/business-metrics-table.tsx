// Phase 8 - features/defend/business-metrics-table.tsx
// Per H.34 and the Phase 8 spec, the business-threshold table:
//
//   Threshold rows: 0.30, 0.50, 0.70, 0.90
//   Columns: Threshold, Precision, Recall, F1, FP, FN, Alert rate
//   Optionally: TP, TN
//
// Per H.34: "Do not highlight only the highest metric. The
// point is that threshold choice is a business decision."
// Every row gets equal treatment; the operating threshold
// (the row whose threshold matches the live operating point)
// gets a small marker.

import { Skeleton } from "../../design-system/primitives";
import { AlertCircle } from "../../design-system/icons";
import type { BusinessMetricsResponse } from "../../lib/api/types";

interface BusinessMetricsTableProps {
  data: BusinessMetricsResponse | undefined;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string;
}

function fmtPct(n: number): string {
  return `${(n * 100).toFixed(2)}%`;
}

export function BusinessMetricsTable({ data, isLoading, isError, errorMessage }: BusinessMetricsTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-1" aria-busy="true" aria-label="Loading business metrics">
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-7 w-full" />)}
      </div>
    );
  }
  if (isError) {
    return (
      <div role="alert" className="flex items-start gap-2 rounded-[var(--radius-input)] border border-[var(--risk-critical)] bg-[var(--bg-base)] p-3">
        <AlertCircle aria-hidden className="mt-0.5 flex-shrink-0" style={{ color: "var(--risk-critical)" }} />
        <p className="text-[0.75rem] text-[var(--risk-critical)]">{errorMessage ?? "Could not load business metrics."}</p>
      </div>
    );
  }
  if (!data || data.length === 0) {
    return (
      <div className="text-center text-[0.75rem] text-[var(--text-muted)] py-6">
        No business metrics.
      </div>
    );
  }
  // The spec operating threshold is 0.5; we mark that row.
  const operatingThreshold = 0.5;
  return (
    <div
      className="overflow-x-auto"
      tabIndex={0}
      role="region"
      aria-label="Business-threshold tradeoff table (scrollable horizontally)"
    >
      <table className="w-full text-[0.75rem] border-collapse">
        <thead>
          <tr>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">Threshold</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">Precision</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">Recall</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">F1</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">TP</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">FP</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">FN</th>
            <th scope="col" className="text-right text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] px-2 py-1">Alert rate</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row) => {
            const isOp = Math.abs(row.threshold - operatingThreshold) < 1e-6;
            return (
              <tr
                key={row.threshold}
                className="border-t border-[var(--border-subtle)]"
                style={isOp ? { backgroundColor: "var(--bg-elevated)" } : undefined}
              >
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-primary)]">
                  {row.threshold.toFixed(2)}
                  {isOp && <span className="ml-1 text-[var(--accent-cyan)] text-[0.625rem]">op</span>}
                </td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-primary)]">{fmtPct(row.precision)}</td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-primary)]">{fmtPct(row.recall)}</td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-primary)]">{fmtPct(row.f1)}</td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-secondary)]">{row.true_positives}</td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-secondary)]">{row.false_positives}</td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-secondary)]">{row.false_negatives}</td>
                <td className="px-2 py-1.5 text-right font-mono tabular-nums text-[var(--text-secondary)]">{fmtPct(row.alert_rate)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
