// Phase 7 - features/generate/recent-generates.tsx
// "Recent generates this session" - a small list of the last N
// generates the user did on this page. NOT in Zustand: per the
// spec, this is feature-local UI state (it represents "what just
// happened in the last few minutes on this page", not "what the
// app knows"). When the user navigates away, the list clears.
//
// Each row shows: attack id + name, urgency, transaction_id, time.
// Clicking a row re-opens the result in the main panel by passing
// the GenerateResult back to the parent via onSelect.

import { RotateCcw } from "../../design-system/icons";
import type { GenerateResult } from "../../lib/api/types";
import { formatUsd } from "../../lib/format";

interface RecentGeneratesProps {
  results: GenerateResult[];
  onSelect: (result: GenerateResult) => void;
}

function timeOf(d: Date): string {
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function RecentGenerates({
  results,
  onSelect,
}: RecentGeneratesProps) {
  if (results.length === 0) {
    return (
      <div className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4">
        <div className="flex items-center gap-2 mb-2">
          <RotateCcw aria-hidden size="inline" style={{ color: "var(--accent-cyan)" }} />
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
            Recent generates
          </h3>
        </div>
        <p className="text-[0.75rem] text-[var(--text-muted)]">
          No generates this session yet. Each successful generation will appear here.
        </p>
      </div>
    );
  }

  // Newest first.
  const ordered = [...results].reverse();

  return (
    <div className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4 space-y-3">
      <div className="flex items-center gap-2">
        <RotateCcw aria-hidden size="inline" style={{ color: "var(--accent-cyan)" }} />
        <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Recent generates
        </h3>
        <span className="text-[0.625rem] font-mono text-[var(--text-muted)] ml-auto">
          {results.length} this session
        </span>
      </div>
      <ul className="space-y-1.5">
        {ordered.slice(0, 8).map((r) => {
          return (
            <li key={r.run_id}>
              <button
                onClick={() => onSelect(r)}
                className="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded text-[0.75rem] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors"
              >
                <span className="font-mono text-[0.6875rem] text-[var(--text-muted)]">
                  {timeOf(new Date())}
                </span>
                <span className="font-mono text-[0.6875rem] tabular-nums">
                  {formatUsd(r.transaction.amount)}
                </span>
                <span className="font-mono text-[0.6875rem] text-[var(--text-muted)] truncate flex-1">
                  {r.transaction.transaction_id ?? r.run_id}
                </span>
                {!r.accepted && (
                  <span className="text-[0.625rem] font-mono text-[var(--risk-critical)]">
                    rejected
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ul>
      <p className="text-[0.625rem] font-mono text-[var(--text-muted)]">
        Click a row to re-open that result in the main panel.
      </p>
    </div>
  );
}
