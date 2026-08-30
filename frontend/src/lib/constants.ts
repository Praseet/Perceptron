// Phase 4 - lib/constants.ts
// Small, shared constants used across pages.
//
// - FEATURE_COLS mirrors src/config.py (Appendix B). The Defend page's
//   transaction builder form (Phase 8) uses this list.
// - LOOP_LEGS maps leg id to its token variable, so a component
//   that needs to resolve "identify" -> var(--loop-identify) does so
//   programmatically.
// - ROUTES gives every page path a named constant rather than a
//   string literal scattered across the app.

import type { FraudType } from "./api/types";

// Shared TanStack Query key for the getAttacks() call. Hoisted here
// (Phase 7) so every consumer dedupes to the same cache entry. The
// key is intentionally NOT dataSource-scoped: both clients return
// the same data shape, and keying on dataSource would just create
// duplicate cache entries that race each other on invalidation.
// Phase 6's features/identify/use-attacks.ts used to own a copy of
// this key as ["attacks", "identify"]; that local copy is now
// re-exported from here for back-compat with the Phase 6 import.
export const ATTACKS_QUERY_KEY = ["attacks"] as const;
export const ATTACKS_QUERY_KEY_IDENTIFY = ["attacks", "identify"] as const;

// Mirrors src/config.py FEATURE_COLS exactly.
export const FEATURE_COLS = [
  "amount",
  "account_age_days",
  "tx_last_1min",
  "tx_last_1hr",
  "tx_last_24hr",
  "count_30d",
  "amount_zscore_30d",
  "new_device",
  "new_merchant",
  "merchant_cat_freq_user",
  "time_since_last_s",
  "dist_from_prev_km",
  "geo_velocity_kmh",
  "hour_of_day",
  "three_ds_failures_before_result",
  "three_ds_failures_last_30d",
  "device_trust_age_days",
  "burst_count_10m",
  "is_high_amount_burst",
  "inter_transaction_time_s",
] as const;

// Mirrors src/config.py CAT_COLS.
export const CAT_COLS = ["merchant_category", "channel", "three_ds_result"] as const;

export type LegId = "identify" | "generate" | "defend" | "improve";

export const LOOP_LEGS: Record<LegId, { label: string; tokenVar: string }> = {
  identify: { label: "Identify", tokenVar: "var(--loop-identify)" },
  generate: { label: "Generate", tokenVar: "var(--loop-attack)" },
  defend: { label: "Defend", tokenVar: "var(--loop-defend)" },
  improve: { label: "Improve", tokenVar: "var(--loop-improve)" },
};

export const FRAUD_TYPES: readonly FraudType[] = [
  "account_takeover",
  "ai_impersonation",
  "auth_bypass",
  "bustout_identity",
  "card_testing",
  "synthetic_identity",
  "bnpl_abuse",
] as const;

export const ROUTES = {
  home: "/",
  identify: "/identify",
  generate: "/generate",
  defend: "/defend",
  loop: "/loop",
} as const;

export type RoutePath = (typeof ROUTES)[keyof typeof ROUTES];