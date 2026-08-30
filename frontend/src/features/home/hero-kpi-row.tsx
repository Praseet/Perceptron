// Phase 5 - features/home/hero-kpi-row.tsx
// Four KPI tiles directly under the hero. Per the Phase 5 spec:
//
//   1. Transactions     - getSystemStatus().n_transactions (1,064,963)
//   2. Attacks generated - sum of FRAUD_TYPE_TARGETS = 1,390 (a static
//                          aggregate from src/config.py, NOT a query -
//                          the value doesn't change at runtime)
//   3. Fraud rate       - getSystemStatus().fraud_rate (0.0004 -> 0.04%)
//   4. PR-AUC           - getSystemStatus().pr_auc_test (0.9072)
//
// The first, third, and fourth read from getSystemStatus() (one query,
// four derived values). The second is a compile-time constant from
// the project's own config - the locked value is 1,390 per the
// Phase 5 spec.

import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import { KpiTile } from "../../design-system/patterns/kpi-tile";
import { formatPct } from "../../lib/format";

// Static aggregate. Computed once at module load; the spec is explicit
// that this is "a static aggregate per the spec" and not a runtime
// value, so the constant is hardcoded and the calculation is
// documented for the reviewer who diffs this against src/config.py:
//   120 + 80 + 220 + 450 + 340 + 100 + 80 = 1,390
const ATTACKS_GENERATED_TOTAL = 1_390;

export function HeroKpiRow() {
  const status = useQuery({
    queryKey: ["system-status", "hero-kpi"],
    queryFn: () => getApiClient().getSystemStatus(),
    staleTime: 30_000,
  });

  // Loading skeleton: 4 empty tiles. KpiTile accepts no loading
  // state natively, so we render our own simple placeholders that
  // match the KpiTile's dimensions and color tokens.
  if (status.isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" aria-busy="true">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-[var(--radius-card)] bg-[var(--bg-panel)] border border-[var(--border-subtle)] p-4 h-[88px] animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (status.isError || !status.data) {
    // On error, render zero-state tiles rather than blanking the
    // hero. The user still sees the chrome, the layout, and the
    // message "data unavailable" - which is the right honest
    // response to a backend failure.
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" role="status">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-[var(--radius-card)] bg-[var(--bg-panel)] border border-[var(--border-subtle)] p-4"
          >
            <p className="text-caption">Data unavailable</p>
            <p className="text-data-lg mt-1 text-[var(--text-muted)]">-</p>
          </div>
        ))}
      </div>
    );
  }

  const { n_transactions, fraud_rate, pr_auc_test } = status.data;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" aria-label="Key performance indicators">
      <KpiTile
        label="Transactions"
        value={n_transactions}
        direction="up-is-good"
        format={(n) => n.toLocaleString("en-US")}
      />
      <KpiTile
        label="Attacks generated"
        value={ATTACKS_GENERATED_TOTAL}
        direction="up-is-good"
        format={(n) => n.toLocaleString("en-US")}
      />
      <KpiTile
        label="Fraud rate"
        value={fraud_rate}
        direction="down-is-good"
        format={(n) => formatPct(n, 3)}
      />
      <KpiTile
        label="PR-AUC"
        value={pr_auc_test}
        direction="up-is-good"
        format={(n) => n.toFixed(4)}
      />
    </div>
  );
}