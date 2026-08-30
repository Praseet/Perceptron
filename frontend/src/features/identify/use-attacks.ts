// Phase 6 - features/identify/use-attacks.ts
// The ONLY file in src/features/identify/ that imports from lib/api/.
// Every other file in this folder reads attacks through this hook.
// Per the spec: "this is the ONLY file in this feature folder that
// imports from `lib/api/`."

import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import type { Attack } from "../../lib/api/types";

// Cache key is module-scoped (not dataSource-scoped) because the
// same data is returned by both clients; keying on dataSource
// would just duplicate cache entries. The 30s staleTime comes from
// the global default in main.tsx.
// Re-export the hoisted key under its old name so any future
// internal caller of `ATTACKS_QUERY_KEY` from this module keeps
import { ATTACKS_QUERY_KEY } from "../../lib/constants";
export { ATTACKS_QUERY_KEY };

/**
 * useAttacks() � returns the full list of attacks from the active
 * API client. Wraps the data so the rest of the feature folder
 * never sees a loading/error state directly: instead the hook
 * returns a discriminated result the page can switch on.
 */
export function useAttacks() {
  const q = useQuery<Attack[]>({
    queryKey: [...ATTACKS_QUERY_KEY],
    queryFn: () => getApiClient().getAttacks(),
  });
  return q;
}
