// Phase 8 - features/defend/use-defend.ts
// The ONE shared TanStack Query hook file for the Defend page.
// (Plus a small read-from-store helper for the "Load a transaction
// I just generated" link.)
//
// Per the Phase 8 spec:
//   "use-defend.ts - TanStack Query hooks: a mutation for
//    getApiClient().predict(tx), and queries for
//    getEvalPerClass() and getPrCurve()."
//
// Phase 8 also adds the two new eval endpoints per H.2.14 / H.2.15
// (business metrics + confusion), so this file owns all five
// remote reads plus the predict mutation.
//
// This is the ONLY file in features/defend/ that imports from
// lib/api/. Every other file in this folder reads data through
// these hooks (mirroring the Phase 6 identify/use-attacks.ts rule).

import { useMutation, useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import { useAppStore } from "../../lib/store";
import type { TransactionRowWithId } from "../../lib/api/types";

/**
 * usePredict() - the predict mutation. The form supplies the
 * transaction on submit; we forward to getApiClient().predict().
 */
export function usePredict() {
  return useMutation({
    mutationFn: (tx: TransactionRowWithId) =>
      getApiClient().predict({ transaction: tx }),
  });
}

/**
 * useEvalPerClass() - per-fraud-type eval table. Same shape the
 * Home page already uses (Phase 5 + Phase 3 PerFraudTypeTable
 * pattern), so the numbers on Defend match the Home page exactly
 * (consistency requirement: spec).
 */
export function useEvalPerClass() {
  return useQuery({
    queryKey: ["eval", "per-class"],
    queryFn: () => getApiClient().getEvalPerClass(),
    staleTime: 30_000,
  });
}

/**
 * useEvalPrCurve() - precision/recall curve. Drives the
 * PrCurveChart and the ProbabilityGauge's threshold tick.
 */
export function useEvalPrCurve() {
  return useQuery({
    queryKey: ["eval", "pr-curve"],
    queryFn: () => getApiClient().getEvalPrCurve(),
    staleTime: 30_000,
  });
}

/**
 * useEvalBusiness() - H.2.14 business metrics at the four spec
 * thresholds. 5s stale time because these are eval-time
 * numbers that won't change during a session.
 */
export function useEvalBusiness() {
  return useQuery({
    queryKey: ["eval", "business"],
    queryFn: () => getApiClient().getEvalBusiness(),
    staleTime: 30_000,
  });
}

/**
 * useEvalConfusion() - H.2.15 per-fraud-type confusion data.
 */
export function useEvalConfusion() {
  return useQuery({
    queryKey: ["eval", "confusion"],
    queryFn: () => getApiClient().getEvalConfusion(),
    staleTime: 30_000,
  });
}

/**
 * useLastGeneratedTransaction() - returns the full transaction
 * row from the store when the Generate -> Defend cross-link is
 * available. Returns null otherwise. The Defend page uses this
 * to decide whether to show the "Load a transaction I just
 * generated" link.
 *
 * Per the spec, this is feature-local state ownership: the
 * store is the cross-page contract, and this hook is the
 * page's read window into it.
 */
export function useLastGeneratedTransaction(): TransactionRowWithId | null {
  return useAppStore((s) => s.lastGeneratedTransaction);
}
