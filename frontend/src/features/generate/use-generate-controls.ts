// Phase 7 - features/generate/use-generate-controls.ts
// The ONE shared hook for all Generate-control surfaces on the app.
//
// Both the full-page Generate page (features/generate/generate-page.tsx)
// and the Home page Generate mini (features/home/pillar-preview-cards.tsx)
// render the same attack/urgency/Generate trio. Per the spec
// share-the-hook rule, every byte of state and mutation logic lives
// here. The two surfaces differ ONLY in layout (40/60 grid vs.
// compact panel) and which derived result-state they choose to
// render - the hook is the single source of truth for both.
//
// Why a custom hook (not just useMutation) - because live mode can
// stream progress messages from the backend over SSE (H.2.17), and
// the Generate page needs to surface them. The hook hides the
// streaming concern from the call site.
//
// This is the ONLY file in features/generate/ that imports from
// lib/api/. The full-page and the GenerateControls component each
// import this hook, keeping the feature folder API surface small.

import { useCallback, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import type {
  Attack,
  GenerateRequest,
  GenerateResult,
} from "../../lib/api/types";
import { ATTACKS_QUERY_KEY } from "../../lib/constants";
import { useAppStore } from "../../lib/store";

export type Urgency = "low" | "medium" | "high";
export type UserId = number | string;

export interface UseGenerateControlsOptions {
  initialAttackId?: string;
  initialUrgency?: Urgency;
  initialUserId?: UserId;
  /** When true (home mini variant), auto-pick the first implemented
   * attack and never let the caller change it. */
  lockAttackId?: boolean;
}

export interface UseGenerateControlsResult {
  attacks: Attack[];
  attacksLoading: boolean;
  attacksError: Error | null;
  attackId: string;
  urgency: Urgency;
  userId: UserId;
  setAttackId: (id: string) => void;
  setUrgency: (u: Urgency) => void;
  setUserId: (u: UserId) => void;
  isStreaming: boolean;
  progress: string[];
  result: GenerateResult | null;
  error: Error | null;
  generate: () => void;
  reset: () => void;
}

// Pick the first "implemented" attack. Falls back to the first
// attack of any status if none are implemented (defensive - the
// real fixture has 13 implemented, but in a degraded backend the
// page should still render).
function firstImplemented(list: Attack[]): string {
  const found = list.find((a) => a.status === "implemented");
  return (found ?? list[0])?.id ?? "";
}

export function useGenerateControls(
  opts: UseGenerateControlsOptions = {},
): UseGenerateControlsResult {
  const {
    initialAttackId,
    initialUrgency = "medium",
    initialUserId = "random",
    lockAttackId = false,
  } = opts;

  const attacksQuery = useQuery<Attack[]>({
    queryKey: [...ATTACKS_QUERY_KEY],
    queryFn: () => getApiClient().getAttacks(),
  });

  // Local state for the three controls. Kept here (not in Zustand)
  // because they are tied to this UI surface, not the global app.
  // The "last generated transaction id" is the one field that
  // belongs in Zustand (Phase 8 Defend page reads it).
  const [attackId, setAttackIdInner] = useState<string>(
    initialAttackId ?? "",
  );
  const [urgency, setUrgency] = useState<Urgency>(initialUrgency);
  const [userId, setUserId] = useState<UserId>(initialUserId);

  // Hand-rolled mutation: forwards progress messages to local
  // state, supports cancellation via a token. useMutation would
  // also work but the cancellation semantics are cleaner with a
  // manual ref + state.
  const [isStreaming, setIsStreaming] = useState(false);
  const [progress, setProgress] = useState<string[]>([]);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const cancelRef = useRef<{ cancelled: boolean }>({ cancelled: false });

  // When the attack list arrives and the caller has not pre-set
  // an attack id, default to the first implemented one. This
  // matches the spec non-empty-default rule for the Generate page.
  // Gated by whether attackId is "" - a real selection is never
  // overwritten.
  if (
    !lockAttackId &&
    attackId === "" &&
    attacksQuery.data &&
    attacksQuery.data.length > 0
  ) {
    setAttackIdInner(initialAttackId ?? firstImplemented(attacksQuery.data));
  }

  // When lockAttackId is on (home mini), always force the selection
  // to the first implemented - the home mini never shows a select
  // so this is the only way to keep the in-flight generate call
  // pointed at a real attack.
  if (lockAttackId && attacksQuery.data && attacksQuery.data.length > 0) {
    const want = firstImplemented(attacksQuery.data);
    if (want && want !== attackId) setAttackIdInner(want);
  }

  const setAttackId = useCallback(
    (id: string) => {
      if (lockAttackId) return; // no-op
      setAttackIdInner(id);
    },
    [lockAttackId],
  );

  const generate = useCallback(() => {
    if (!attackId) return; // can't fire without an attack
    cancelRef.current.cancelled = true; // cancel any in-flight
    const myToken = { cancelled: false };
    cancelRef.current = myToken;

    setIsStreaming(true);
    setProgress([]);
    setError(null);
    setResult(null);

    const req: GenerateRequest = {
      attack_id: attackId,
      user_id: userId,
      urgency,
    };

    getApiClient()
      .generate(req, (msg) => {
        if (myToken.cancelled) return;
        setProgress((p) => [...p, msg]);
      })
      .then((res) => {
        if (myToken.cancelled) return;
        setResult(res);
        setIsStreaming(false);
        // Phase 8: write the full transaction to the store
        // SYNCHRONOUSLY (in the .then callback, not in a
        // useEffect on the result) so the store is committed
        // before the next paint. This closes a race where the
        // user could click Score in Defend before the React
        // effect that writes to the store had a chance to run.
        const tx = res.transaction;
        if (tx.transaction_id) {
          useAppStore.getState().setLastGeneratedTransactionId(tx.transaction_id);
          useAppStore.getState().setLastGeneratedTransaction(tx);
        }
        // Phase 10.5 §5.3: persist the full GenerateResult so the Home
        // Generate mini's "See all" lands on the full Generate
        // page showing the same result rather than an empty state.
        // Synchronous-write pattern, same as the Generate->Defend
        // handoff above, so the store is committed before the
        // next paint (otherwise clicking See all could race it).
        useAppStore.getState().setLastHomeGenerateResult(res);
      })
      .catch((e: unknown) => {
        if (myToken.cancelled) return;
        setError(e instanceof Error ? e : new Error(String(e)));
        setIsStreaming(false);
      });
  }, [attackId, userId, urgency]);

  const reset = useCallback(() => {
    cancelRef.current.cancelled = true;
    setIsStreaming(false);
    setProgress([]);
    setResult(null);
    setError(null);
  }, []);

  return {
    attacks: attacksQuery.data ?? [],
    attacksLoading: attacksQuery.isLoading,
    attacksError:
      attacksQuery.error instanceof Error
        ? attacksQuery.error
        : attacksQuery.error
          ? new Error(String(attacksQuery.error))
          : null,

    attackId,
    urgency,
    userId,

    setAttackId,
    setUrgency,
    setUserId,

    isStreaming,
    progress,
    result,
    error,
    generate,
    reset,
  };
}
