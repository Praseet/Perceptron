// Phase 7 - features/generate/diff-against-normal.tsx
// "Diff Against Normal" panel. Renders a small table that compares
// the generated transaction to the per-user median values the
// backend returns in `user_medians` (per H.2.13). The four
// comparison fields are exactly the ones the type definition
// commits to: amount, channel, hour_of_day, device_trust_age_days.
//
// The comparison is value-only - the panel is a one-shot read of
// "how does this transaction deviate from the user's normal
// behavior", with no chart. Spec choice: this is a "narrative"
// panel, not a metrics panel.

import { Scale } from "../../design-system/icons";
import type { GenerateResult } from "../../lib/api/types";
import { formatUsd, formatInt } from "../../lib/format";

interface DiffAgainstNormalProps {
  result: GenerateResult;
}

interface DiffRow {
  field: string;
  generated: number | string;
  normal: number | string;
  /** A short plain-English verdict shown to the right of each row. */
  verdict: string;
}

function buildRows(
  tx: GenerateResult["transaction"],
  medians: NonNullable<GenerateResult["user_medians"]>,
): DiffRow[] {
  // amount: flag if generated > 2x the user median.
  const amtVerdict =
    tx.amount > medians.amount * 2
      ? `${(tx.amount / medians.amount).toFixed(1)}x user median`
      : "Within range";

  // channel: if different, flag. The spec data is mostly card-not-present
  // so this is rare in practice.
  const chVerdict =
    tx.channel === medians.channel ? "Same channel" : `Different from "${medians.channel}"`;

  // hour_of_day: convert to 0-23 wall clock and flag if off-peak (00-05).
  const hourVerdict =
    tx.hour_of_day >= 0 && tx.hour_of_day <= 5
      ? "Off-hours"
      : "Normal hours";

  // device_trust_age_days: a new device (low value) is a known fraud
  // signal. Flag if < 7 days.
  const dvtVerdict =
    tx.device_trust_age_days < 7
      ? `New device (${formatInt(tx.device_trust_age_days)}d)`
      : `${formatInt(tx.device_trust_age_days)}d trusted`;

  return [
    { field: "amount", generated: tx.amount, normal: medians.amount, verdict: amtVerdict },
    { field: "channel", generated: tx.channel, normal: medians.channel, verdict: chVerdict },
    { field: "hour_of_day", generated: tx.hour_of_day, normal: medians.hour_of_day, verdict: hourVerdict },
    {
      field: "device_trust_age_days",
      generated: tx.device_trust_age_days,
      normal: medians.device_trust_age_days,
      verdict: dvtVerdict,
    },
  ];
}

function fmt(v: number | string): string {
  if (typeof v === "number") {
    if (v === Math.floor(v)) return formatInt(v);
    return v.toFixed(2);
  }
  return String(v);
}

export function DiffAgainstNormal({ result }: DiffAgainstNormalProps) {
  const medians = result.user_medians;
  if (!medians) {
    return (
      <div className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4">
        <div className="flex items-center gap-2 mb-2">
          <Scale aria-hidden size="inline" style={{ color: "var(--accent-cyan)" }} />
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
            Diff against normal
          </h3>
        </div>
        <p className="text-[0.75rem] text-[var(--text-muted)]">
          No user medians returned with this run.
        </p>
      </div>
    );
  }

  const rows = buildRows(result.transaction, medians);

  return (
    <div className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Scale aria-hidden size="inline" style={{ color: "var(--accent-cyan)" }} />
        <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Diff against normal
        </h3>
      </div>
      <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
        Per-user medians, this run
      </p>
      <table className="w-full text-[0.75rem]">
        <thead>
          <tr className="border-b border-[var(--border-subtle)]">
            <th className="text-left py-1.5 text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
              Field
            </th>
            <th className="text-right py-1.5 text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
              This run
            </th>
            <th className="text-right py-1.5 text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
              User median
            </th>
            <th className="text-left py-1.5 pl-3 text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
              Verdict
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const isAmount = r.field === "amount";
            return (
              <tr key={r.field} className="border-b border-[var(--border-subtle)] last:border-b-0">
                <td className="py-1.5 text-[var(--text-primary)] font-mono">{r.field}</td>
                <td className="py-1.5 text-right text-[var(--text-primary)] font-mono tabular-nums">
                  {isAmount && typeof r.generated === "number"
                    ? formatUsd(r.generated)
                    : fmt(r.generated)}
                </td>
                <td className="py-1.5 text-right text-[var(--text-secondary)] font-mono tabular-nums">
                  {isAmount && typeof r.normal === "number"
                    ? formatUsd(r.normal)
                    : fmt(r.normal)}
                </td>
                <td className="py-1.5 pl-3 text-[var(--text-secondary)]">{r.verdict}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
