// Phase 7 - features/generate/transaction-materialize.tsx
// Shows the generated transaction: 23 fields (20 numeric + 3
// categorical), the run_id, the acceptance flag, the drop stats,
// and a "materialize" status row that explains what the
// generator did with the proposed transaction.
//
// The 23 fields are split into two columns (numeric vs categorical)
// so the panel reads as a property sheet, not a flat dump.

import { CheckCircle2, AlertCircle, FileText } from "../../design-system/icons";
import { Badge } from "../../design-system/primitives";
import { formatUsd, formatInt } from "../../lib/format";
import { FEATURE_COLS, CAT_COLS } from "../../lib/constants";
import type { GenerateResult } from "../../lib/api/types";

interface TransactionMaterializeProps {
  result: GenerateResult;
}

function fmt(value: number | string): string {
  if (typeof value === "number") {
    if (Number.isInteger(value)) return formatInt(value);
    return value.toFixed(2);
  }
  return String(value);
}

export function TransactionMaterialize({ result }: TransactionMaterializeProps) {
  const tx = result.transaction;
  const accepted = result.accepted;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText aria-hidden size="inline" style={{ color: "var(--accent-cyan)" }} />
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
            Materialized transaction
          </h3>
        </div>
        <div className="flex items-center gap-2">
          {accepted ? (
            <Badge variant="loop-defend" label="Accepted" />
          ) : (
            <Badge variant="risk-critical" label="Rejected" />
          )}
          {tx.transaction_id && (
            <span className="text-[0.6875rem] font-mono text-[var(--text-muted)]">
              id: {tx.transaction_id}
            </span>
          )}
        </div>
      </div>

      {result.rejection_reason && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-[var(--radius-input)] border border-[var(--risk-critical)] bg-[var(--bg-base)] p-3"
        >
          <AlertCircle
            aria-hidden
            className="mt-0.5 flex-shrink-0"
            style={{ color: "var(--risk-critical)" }}
          />
          <p className="text-[0.75rem] text-[var(--risk-critical)]">
            {result.rejection_reason}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-2 text-[0.75rem]">
        <div>
          <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] mb-2">
            Numeric features ({FEATURE_COLS.length})
          </p>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5">
            {FEATURE_COLS.map((col) => {
              const v = (tx as unknown as Record<string, unknown>)[col];
              const display =
                col === "amount" && typeof v === "number"
                  ? formatUsd(v)
                  : fmt(v as number);
              return (
                <div key={col} className="flex items-baseline justify-between gap-2">
                  <dt className="text-[var(--text-muted)] font-mono text-[0.6875rem]">
                    {col}
                  </dt>
                  <dd className="text-[var(--text-primary)] font-mono tabular-nums">
                    {display}
                  </dd>
                </div>
              );
            })}
          </dl>
        </div>
        <div>
          <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] mb-2">
            Categorical features ({CAT_COLS.length})
          </p>
          <dl className="space-y-1.5">
            {CAT_COLS.map((col) => {
              const v = (tx as unknown as Record<string, unknown>)[col];
              return (
                <div key={col} className="flex items-baseline justify-between gap-2">
                  <dt className="text-[var(--text-muted)] font-mono text-[0.6875rem]">
                    {col}
                  </dt>
                  <dd className="text-[var(--text-primary)] font-mono">
                    {String(v)}
                  </dd>
                </div>
              );
            })}
          </dl>
        </div>
      </div>

      <div className="rounded-[var(--radius-input)] border border-[var(--border-subtle)] bg-[var(--bg-base)] p-3">
        <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] mb-2">
          Drop statistics
        </p>
        <div className="flex items-center gap-4 text-[0.75rem]">
          {Object.entries(result.drop_stats).map(([k, v]) => (
            <div key={k} className="flex items-baseline gap-1.5">
              <span className="text-[var(--text-muted)] font-mono">{k}</span>
              <span className="text-[var(--text-primary)] font-mono tabular-nums">
                {formatInt(v)}
              </span>
            </div>
          ))}
        </div>
        {accepted && (
          <div className="flex items-center gap-1.5 mt-2 text-[0.6875rem] text-[var(--status-safe)]">
            <CheckCircle2 aria-hidden size="inline" />
            <span>Transaction passed the leakage + schema gates.</span>
          </div>
        )}
      </div>

      <p className="text-[0.625rem] font-mono text-[var(--text-muted)]">
        run_id: {result.run_id}
      </p>
    </div>
  );
}
