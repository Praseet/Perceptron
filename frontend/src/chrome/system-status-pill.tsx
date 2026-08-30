// Phase 5 - chrome/system-status-pill.tsx
// The right-side status indicator in the top nav. Shows:
//   - a colored dot (green = online, amber = degraded, red = offline)
//   - the "Online · N.NNN M tx" line
//
// Reads from getSystemStatus() via TanStack Query. Falls back to a
// "loading" pill while the query is in flight and to a "stale" pill on
// error. Never throws and never blanks the nav.

import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../lib/api/client";
import { useAppStore } from "../lib/store";
import { formatInt, formatRelative } from "../lib/format";
import { StatusPill } from "../design-system/patterns/status-pill";

const TOKENS = {
  online: "var(--status-safe)",
  degraded: "var(--status-warn)",
  offline: "var(--status-threat)",
} as const;

function statusToColor(s: string | undefined): string {
  if (s === "ok") return TOKENS.online;
  if (s === "degraded") return TOKENS.degraded;
  return TOKENS.offline;
}

function statusToText(s: string | undefined, nTx: number | undefined): string {
  if (s == null) return "Connecting";
  if (s === "ok") {
    if (nTx == null) return "Online";
    // "1.06M tx" - compact millions formatting. The spec shows this
    // exact label in §3.0 Global Chrome, so we hardcode the format.
    if (nTx >= 1_000_000) return `Online · ${(nTx / 1_000_000).toFixed(2)}M tx`;
    if (nTx >= 1_000) return `Online · ${(nTx / 1_000).toFixed(1)}k tx`;
    return `Online · ${nTx} tx`;
  }
  if (s === "degraded") return "Degraded";
  return "Offline";
}

export function SystemStatusPill() {
  const dataSource = useAppStore((s) => s.dataSource);

  // getHealth() is the source of truth for the dot color (it has
  // status: "ok" | "degraded"), and getSystemStatus() is the source
  // of truth for the n_transactions shown in the label. Two queries
  // because two sources - kept separate so each can refresh on its
  // own cadence without invalidating the other.
  const health = useQuery({
    queryKey: ["health", dataSource],
    queryFn: () => getApiClient().getHealth(),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const status = useQuery({
    queryKey: ["system-status", dataSource],
    queryFn: () => getApiClient().getSystemStatus(),
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  // While loading, the dot is muted (text-muted) and the label says
  // "Connecting". We deliberately don't show a Skeleton here - a
  // nav bar is too small for a Skeleton to read as anything other
  // than a flicker, and a muted dot is the right "I don't know yet"
  // signal for a status indicator.
  if (health.isLoading || status.isLoading) {
    return (
      <StatusPill
        color="var(--text-muted)"
        text="Connecting"
        aria-label="System status: connecting"
      />
    );
  }

  // On error, treat as offline. The label "Last seen N min ago" tells
  // the user this is a stale reading, not a live one. The
  // last_retrain_at timestamp from getSystemStatus() is the closest
  // proxy we have for "last seen alive."
  if (health.isError || status.isError) {
    const lastSeen = status.data?.last_retrain_at;
    const text = lastSeen
      ? `Stale · last seen ${formatRelative(lastSeen)}`
      : "Stale";
    return (
      <StatusPill
        color={TOKENS.offline}
        text={text}
        aria-label={`System status: ${text}`}
      />
    );
  }

  const s = health.data?.status;
  const nTx = status.data?.n_transactions;
  const text = statusToText(s, nTx);
  const color = statusToColor(s);

  return (
    <span
      className="inline-flex items-center gap-3"
      aria-label={`System status: ${text}`}
    >
      <StatusPill color={color} text={text} />
      {status.data && (
        <span className="hidden md:inline text-[0.6875rem] text-[var(--text-muted)] font-mono tabular-nums">
          {formatInt(status.data.n_users)} users
        </span>
      )}
    </span>
  );
}