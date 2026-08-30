// Phase 4 - lib/format.ts
// Number/currency/date formatting helpers used throughout.
//
// Per spec:
// - Currency: USD-style "$" for transaction amounts (dataset is
//   unlabeled; the hackathon prize amounts are INR but the
//   transaction amounts in the CSV are not explicitly INR-denominated
//   per the spec - default to USD and note the assumption).
// - Percentage: one convention site-wide. We use the "0.9072 -> 90.72%"
//   convention (2-decimal percentage) everywhere.
// - Date: relative/short via date-fns.

import { formatDistanceToNow, format } from "date-fns";

/** Format a number as USD currency, e.g. 1234.5 -> "$1,234.50". */
export function formatUsd(n: number, opts: { fractionDigits?: number } = {}): string {
  const fd = opts.fractionDigits ?? 2;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: fd,
    maximumFractionDigits: fd,
  }).format(n);
}

/** Format a probability/rate (0..1) as a percentage, e.g. 0.9072 -> "90.72%". */
export function formatPct(n: number, fractionDigits: number = 2): string {
  return (n * 100).toFixed(fractionDigits) + "%";
}

/** Format an integer with thousands separators, e.g. 1064963 -> "1,064,963". */
export function formatInt(n: number): string {
  return new Intl.NumberFormat("en-US").format(Math.round(n));
}

/** Format a 0-100 risk score as just the number, no padding. */
export function formatScore(n: number): string {
  return Math.round(n).toString();
}

/** Short absolute date-time, e.g. "Aug 29, 2026 14:30". */
export function formatShort(iso: string): string {
  try {
    return format(new Date(iso), "MMM d, yyyy HH:mm");
  } catch {
    return iso;
  }
}

/** Relative time, e.g. "5 minutes ago". */
export function formatRelative(iso: string): string {
  try {
    return formatDistanceToNow(new Date(iso), { addSuffix: true });
  } catch {
    return iso;
  }
}

/** Format a duration in seconds as "1m 23s" or "47s". */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return Math.round(seconds) + "s";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds - m * 60);
  return m + "m " + s + "s";
}