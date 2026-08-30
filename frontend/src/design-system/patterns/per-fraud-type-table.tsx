// Per-fraud-type eval table. Lives in design-system/patterns/ (not
// features/defend/ or features/home/) because both pages need it
// identically. See Phase 3 prompt for the rationale.

// H.2.6: --chart-1 is not in Appendix D. The spec''s micro-bar uses
// the closest equivalent semantic token, --accent-cyan.
//
// The EvalPerClassRow type is defined inline here per the prompt''s
// note that Phase 4 will replace it with the shared
// lib/api/types.ts import. Both the inline shape and the import
// will be the same once Phase 4 lands.
export interface EvalPerClassRow {
  fraud_type: string;
  count: number;
  precision: number;
  recall: number;
  pr_auc: number;
  fpr: number;
}

interface PerFraudTypeTableProps {
  rows: EvalPerClassRow[];
  className?: string;
}

// Helper: format a number as percentage with 2 decimals.
const fmtPct = (n: number) => (n * 100).toFixed(2) + "%";

// Find column max for a given key (for micro-bar widths).
function colMax(rows: EvalPerClassRow[], key: keyof EvalPerClassRow): number {
  return rows.reduce(
    (m, r) => Math.max(m, r[key] as number),
    0,
  );
}

export function PerFraudTypeTable({ rows, className }: PerFraudTypeTableProps) {
  const countMax = Math.max(1, colMax(rows, "count"));
  const precMax = Math.max(1e-9, colMax(rows, "precision"));
  const recMax = Math.max(1e-9, colMax(rows, "recall"));
  const prMax = Math.max(1e-9, colMax(rows, "pr_auc"));
  const fprMax = Math.max(1e-9, colMax(rows, "fpr"));

  return (
    <div
      className={
        "rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-hidden " +
        (className ?? "")
      }
    >
      {/* Phase 10 a11y: tabIndex={0} + role="region" + aria-label
          make this scrollable container keyboard-accessible. WCAG
          2.1.1 / axe `scrollable-region-focusable` requires that
          a scrollable region be either focusable itself or
          contain focusable content. The original `<div>` was a
          plain container - keyboard-only users could not scroll
          it on Safari / Firefox. */}
      <div
        className="overflow-x-auto"
        tabIndex={0}
        role="region"
        aria-label="Per-fraud-type eval table (scrollable horizontally)"
      >
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-[var(--border-subtle)]">
              <th className="text-left text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-4 py-2">
                Fraud type
              </th>
              <th className="text-right text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-4 py-2">
                Count
              </th>
              <th className="text-right text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-4 py-2">
                Precision
              </th>
              <th className="text-right text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-4 py-2">
                Recall
              </th>
              <th className="text-right text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-4 py-2">
                PR-AUC
              </th>
              <th className="text-right text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] px-4 py-2">
                FPR
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.fraud_type}
                className="border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-elevated)] transition-colors duration-150"
              >
                <td className="px-4 py-2 text-data text-[var(--text-primary)]">
                  {r.fraud_type}
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="micro-bar" style={{ width: `${(r.count / countMax) * 60}px` }} />
                    <span className="text-data">{r.count}</span>
                  </div>
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="micro-bar" style={{ width: `${(r.precision / precMax) * 60}px` }} />
                    <span className="text-data">{fmtPct(r.precision)}</span>
                  </div>
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="micro-bar" style={{ width: `${(r.recall / recMax) * 60}px` }} />
                    <span className="text-data">{fmtPct(r.recall)}</span>
                  </div>
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="micro-bar" style={{ width: `${(r.pr_auc / prMax) * 60}px` }} />
                    <span className="text-data">{fmtPct(r.pr_auc)}</span>
                  </div>
                </td>
                <td className="px-4 py-2 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="micro-bar" style={{ width: `${(r.fpr / fprMax) * 60}px` }} />
                    <span className="text-data">{fmtPct(r.fpr)}</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}