// Phase 4 - lib/index.ts
// Barrel for the lib layer. Per H.3.1, lib/ does not import up toward
// features, chrome, or design-system. Features consume lib/ through
// getApiClient() (api/client.ts) and named exports here.

export { getApiClient } from "./api/client";
export type { AflApiClient } from "./api/client";
export * from "./api/types";

export { useAppStore } from "./store";
export type { DataSource } from "./store";

export { useEventStream } from "./use-event-stream";
export type { UseEventStreamResult } from "./use-event-stream";

export {
  formatUsd,
  formatPct,
  formatInt,
  formatScore,
  formatShort,
  formatRelative,
  formatDuration,
} from "./format";

export {
  FEATURE_COLS,
  CAT_COLS,
  LOOP_LEGS,
  FRAUD_TYPES,
  ROUTES,
} from "./constants";
export type { LegId, RoutePath } from "./constants";