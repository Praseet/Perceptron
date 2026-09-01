// Phase 12 (§12.17.3 + project-owner request) - features/identify/fraud-type-strip.tsx
// A compact fraud-type strip above the attack table: the seven fraud
// types the taxonomy is organized around, each with its real per-type
// case count (from getEvalPerClass(), the same data the per-fraud-type
// table below already shows) and a one-line description.
//
// ADR-4 note: the counts are real, already-flowing data. The one-line
// descriptions are definitional (what the type IS), sourced from the
// project's own attack taxonomy (docs/ATTACK_TAXONOMY.md + the
// generator semantics in src/generator/) - they are definitions, not
// runtime metrics, so a constant is the honest form. No fabricated
// numbers anywhere.
//
// Visual register: mono uppercase labels, tabular-nums counts, one
// accent-cyan selected state, no new color tokens (§12.10).

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import { MOTION_EASE } from "../../design-system/motion";
import type { FraudType } from "../../lib/api/types";

interface FraudTypeInfo {
  label: string;
  blurb: string;
}

// One line per type, each grounded in the taxonomy doc:
//   account_takeover  - legitimate credential seized, drained from inside
//   ai_impersonation  - Category A: LLM voice/chat personas (SE-00x)
//   auth_bypass       - AUT-00x: "Fingerprint/face auth bypass"
//   bustout_identity  - nurtured account maxed out and abandoned
//   card_testing      - Category C: rapid probes of stolen card numbers
//   synthetic_identity- Category B: fabricated person grown past KYC
//   bnpl_abuse        - PR-003: "Synthetic identity for BNPL max-out"
const FRAUD_TYPE_INFO: Record<FraudType, FraudTypeInfo> = {
  account_takeover: {
    label: "Account takeover",
    blurb: "A legitimate customer's credential is seized and the account is drained from the inside.",
  },
  ai_impersonation: {
    label: "AI impersonation",
    blurb: "LLM-generated voice and chat personas - cloned executives, romance bots, fake support desks - social-engineer the payment.",
  },
  auth_bypass: {
    label: "Auth bypass",
    blurb: "Fingerprint, face, or 3-D Secure verification is circumvented at the authentication step itself.",
  },
  bustout_identity: {
    label: "Bustout identity",
    blurb: "A nurtured account builds clean history for weeks, then is maxed out and abandoned in one sweep.",
  },
  card_testing: {
    label: "Card testing",
    blurb: "Rapid micro-authorizations probe which stolen card numbers are still live before resale.",
  },
  synthetic_identity: {
    label: "Synthetic identity",
    blurb: "A fabricated person assembled from real and invented attributes is grown past KYC into full creditworthiness.",
  },
  bnpl_abuse: {
    label: "BNPL abuse",
    blurb: "Synthetic identities open buy-now-pay-later lines at onboarding and max them out immediately.",
  },
};

const TYPE_ORDER: FraudType[] = [
  "account_takeover",
  "ai_impersonation",
  "auth_bypass",
  "bustout_identity",
  "card_testing",
  "synthetic_identity",
  "bnpl_abuse",
];

export function FraudTypeStrip() {
  const reduceMotion = useReducedMotion();
  const [selected, setSelected] = useState<FraudType>(TYPE_ORDER[0]);
  const evalPerClass = useQuery({
    queryKey: ["eval-per-class", "identify"],
    queryFn: () => getApiClient().getEvalPerClass(),
    staleTime: 30_000,
  });

  const counts = new Map<string, number>();
  if (evalPerClass.data) {
    for (const row of evalPerClass.data) counts.set(row.fraud_type, row.count);
  }

  const info = FRAUD_TYPE_INFO[selected];

  return (
    <section
      aria-label="Fraud types in this dataset"
      className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] p-4"
    >
      <div className="flex flex-wrap items-center gap-x-1 gap-y-1">
        {TYPE_ORDER.map((t, i) => {
          const isSel = t === selected;
          const count = counts.get(t);
          return (
            <span key={t} className="inline-flex items-center">
              {i > 0 && (
                <span
                  aria-hidden
                  className="mx-1 text-[var(--border-strong)]"
                >
                  /
                </span>
              )}
              <button
                onClick={() => setSelected(t)}
                aria-pressed={isSel}
                className={
                  "px-2 h-7 inline-flex items-center gap-1.5 rounded-[var(--radius-input)] font-mono uppercase tracking-[0.06em] text-[0.6875rem] transition-colors duration-150 " +
                  (isSel
                    ? "text-[var(--accent-cyan)] bg-[var(--bg-elevated)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]")
                }
                style={
                  isSel
                    ? { boxShadow: "inset 0 0 0 1px var(--accent-cyan-dim)" }
                    : undefined
                }
              >
                <span>{FRAUD_TYPE_INFO[t].label}</span>
                {count != null && (
                  <span className="tabular-nums text-[var(--text-muted)]">
                    {count.toLocaleString("en-US")}
                  </span>
                )}
              </button>
            </span>
          );
        })}
      </div>
      <motion.p
        key={selected}
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2, ease: MOTION_EASE }}
        className="mt-3 text-[0.8125rem] leading-[1.55] text-[var(--text-secondary)]"
      >
        {info.blurb}
      </motion.p>
      <p className="mt-2 text-[0.625rem] font-mono text-[var(--text-muted)]">
        Counts: per-fraud-type eval rows. Definitions: docs/ATTACK_TAXONOMY.md.
      </p>
    </section>
  );
}
