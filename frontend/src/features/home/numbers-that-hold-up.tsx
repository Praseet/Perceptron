// Phase 5 - features/home/numbers-that-hold-up.tsx
// The "Numbers that hold up" section. Per the Phase 5 spec:
//   - id="numbers-that-hold-up" so the footer's "Methodology" link
//     can scroll here.
//   - A small "loop in motion" prose block with the real CHANGELOG
//     before/after numbers (val recall 0.8200 -> 0.8467, FN 34 -> 32)
//     presented as static historical fact.
//   - A per-fraud-type PR-AUC table fed from getEvalPerClass() via
//     TanStack Query, using the PerFraudTypeTable pattern.

import { useQuery } from "@tanstack/react-query";
import { motion, useReducedMotion } from "framer-motion";
import { getApiClient } from "../../lib/api/client";
import { PerFraudTypeTable } from "../../design-system/patterns/per-fraud-type-table";
import { TrendingUp, Repeat } from "../../design-system/icons";
import { LOOP_LEGS } from "../../lib/constants";

export function NumbersThatHoldUp() {
  const reduceMotion = useReducedMotion();
  const evalPerClass = useQuery({
    queryKey: ["eval-per-class", "home"],
    queryFn: () => getApiClient().getEvalPerClass(),
    staleTime: 30_000,
  });

  // Phase 9.5 step 2: a single useInView reveal per section,
  // per H.71 §I. The whole <section> fades in + slides a tiny
  // amount when scrolled into view. Reduced motion skips the
  // animation entirely.

  return (
    <motion.section
      id="numbers-that-hold-up"
      aria-labelledby="numbers-heading"
      className="space-y-5 scroll-mt-20"
      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-15% 0px -15% 0px" }}
      transition={reduceMotion ? { duration: 0 } : { duration: 0.35, ease: "easeOut" }}
    >
      <h2
        id="numbers-heading"
        className="text-section-title text-[var(--text-primary)]"
      >
        Numbers that hold up
      </h2>

      {/* "Loop in motion" prose block. Static historical fact from
          the CHANGELOG - val recall 0.8200 -> 0.8467 across cycles,
          FN 34 -> 32. Presented with the improve-leg green as the
          small accent because this section is the evidence that the
          loop actually improves the model. */}
      <div
        className="bg-[var(--bg-panel)] border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-5"
        style={{ borderLeft: `4px solid ${LOOP_LEGS.improve.tokenVar}` }}
      >
        <div className="flex items-center gap-2 mb-2">
          <Repeat aria-hidden style={{ color: LOOP_LEGS.improve.tokenVar }} />
          <span
            className="text-[0.6875rem] font-mono uppercase tracking-[0.12em]"
            style={{ color: LOOP_LEGS.improve.tokenVar }}
          >
            Loop in motion
          </span>
        </div>
        <p className="text-[0.875rem] text-[var(--text-primary)] leading-[1.6]">
          After a single 1-cycle closed-loop run on the 1,064,963-row
          holdout, validation recall improved from{" "}
          <span className="font-mono">0.8200</span> to{" "}
          <span className="font-mono">0.8467</span> and false negatives
          dropped from <span className="font-mono">34</span> to{" "}
          <span className="font-mono">32</span>. Every miss becomes a
          new training row.
        </p>
        <p className="text-[0.6875rem] font-mono text-[var(--text-muted)] mt-3">
          Source: CHANGELOG.md - validation recall / FN deltas.
        </p>
      </div>

      {/* Per-fraud-type PR-AUC table. Real numbers, no fabrication.
          The table pattern handles the micro-bars; this component
          only supplies the data. */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
            Per-fraud-type PR-AUC
          </h3>
          <span className="text-[0.6875rem] text-[var(--text-muted)] font-mono inline-flex items-center gap-1">
            <TrendingUp aria-hidden />
            Tier 1 XGBoost, test set
          </span>
        </div>
        {evalPerClass.isLoading ? (
          <div className="h-40 rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] animate-pulse" />
        ) : evalPerClass.isError || !evalPerClass.data ? (
          <div className="h-40 rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] flex items-center justify-center text-[var(--text-muted)] text-[0.8125rem]">
            Data unavailable
          </div>
        ) : (
          <PerFraudTypeTable rows={evalPerClass.data} />
        )}
      </div>
    </motion.section>
  );
}