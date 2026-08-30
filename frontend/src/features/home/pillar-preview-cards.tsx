// Phase 5+7+8+10.5 - features/home/pillar-preview-cards.tsx
// The "See it work" section. Three live miniatures + one static
// Improve card, all in one row, replacing the previous two-section
// pair of ClosedLoopStages + PillarPreviewCards. Per Phase 10.5
// refactor §5.1, this is one deliberate section that introduces the
// four pillars once (Identify/Generate/Defend as live previews,
// Improve as the fourth card pointing to /loop).
//
// Per H.3.1 this file does NOT import from features/generate/ for
// the Generate mini - the shared hook + component are imported
// from features/generate/. The Defend mini imports only the
// TransactionBuilderForm component (no hook). This is the
// legitimate feature-crossing per H.3.2 (shared UI components
// from the same shared layer's siblings are allowed when
// alternative is duplication).

import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import { useAppStore } from "../../lib/store";
import { ROUTES, LOOP_LEGS, ATTACKS_QUERY_KEY } from "../../lib/constants";
import { Layers, Sparkles, Activity, TrendingUp, ArrowRight } from "../../design-system/icons";
import { useGenerateControls } from "../generate/use-generate-controls";
import { GenerateControls } from "../generate/generate-controls";
import { TransactionBuilderForm } from "../defend/transaction-builder-form";
import type { TransactionRowWithId } from "../../lib/api/types";

const TOP5 = 5;

export function PillarPreviewCards() {
  return (
    <section aria-labelledby="see-it-work-heading" className="space-y-4">
      <h2
        id="see-it-work-heading"
        className="text-section-title text-[var(--text-primary)]"
      >
        See it work
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <IdentifyMini />
        <GenerateMini />
        <DefendMini />
        <ImproveMini />
      </div>
    </section>
  );
}

function IdentifyMini() {
  const navigate = useNavigate();
  const attacks = useQuery({
    queryKey: [...ATTACKS_QUERY_KEY],
    queryFn: () => getApiClient().getAttacks(),
    staleTime: 30_000,
  });

  const top5 = (attacks.data ?? [])
    .slice()
    .sort((a, b) => {
      if (b.feasibility !== a.feasibility) return b.feasibility - a.feasibility;
      const rank = (s: string) => (s === "implemented" ? 0 : s === "partial" ? 1 : 2);
      return rank(a.status) - rank(b.status);
    })
    .slice(0, TOP5);

  return (
    <article className="bg-[var(--bg-panel)] border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4 flex flex-col">
      <header className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers aria-hidden style={{ color: LOOP_LEGS.identify.tokenVar }} />
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">Identify</h3>
        </div>
        <button
          onClick={() => navigate(ROUTES.identify)}
          className="text-[0.6875rem] text-[var(--accent-cyan)] hover:text-[var(--accent-cyan-dim)] transition-colors"
        >
          See all
        </button>
      </header>
      {attacks.isLoading ? (
        <div className="space-y-2 animate-pulse" aria-busy>
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="h-6 bg-[var(--bg-elevated)] rounded" />
          ))}
        </div>
      ) : (
        <ul className="space-y-1.5">
          {top5.map((a) => (
            <li key={a.id}>
              <button
                onClick={() => navigate(`${ROUTES.identify}?attack_id=${encodeURIComponent(a.id)}`)}
                className="w-full text-left flex items-center justify-between gap-2 px-2 py-1 rounded text-[0.75rem] text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-colors"
              >
                <span className="truncate">{a.name}</span>
                <span className="text-[0.625rem] font-mono text-[var(--text-muted)] shrink-0">
                  {a.id} - {a.feasibility}/5
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

// Phase 7: this is a thin wrapper. The hook + UI live in
// features/generate/ and are shared with the full Generate page.
function GenerateMini() {
  const navigate = useNavigate();
  const controls = useGenerateControls({ lockAttackId: true });

  return (
    <article className="bg-[var(--bg-panel)] border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4 flex flex-col">
      <header className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles aria-hidden style={{ color: LOOP_LEGS.generate.tokenVar }} />
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">Generate</h3>
        </div>
        <button
          onClick={() => navigate(ROUTES.generate)}
          className="text-[0.6875rem] text-[var(--accent-cyan)] hover:text-[var(--accent-cyan-dim)] transition-colors"
        >
          See all
        </button>
      </header>
      <div className="flex-1">
        <GenerateControls controls={controls} variant="compact" />
      </div>
      {controls.result && (
        <p className="mt-2 text-[0.625rem] font-mono text-[var(--text-muted)] truncate">
          {controls.result.transaction.transaction_id}
        </p>
      )}
    </article>
  );
}

// Phase 8: replaced the Phase 5 DefendPredictive helper (which
// re-ran generate() to recover a transaction) with a real
// compact <TransactionBuilderForm>. The mini is a "preview":
// 3 fields, a Predict button, and on submit it navigates to
// /defend where the real predict-and-show-result experience
// lives. The mini reads the same store, uses the same
// ATTACKS_QUERY_KEY, and shares the form with the full page.
function DefendMini() {
  const navigate = useNavigate();
  const lastTx = useAppStore((s) => s.lastGeneratedTransaction);

  function handleSubmit(tx: TransactionRowWithId) {
    // The home mini doesn't render a result panel - that's the
    // /defend page's job. Navigate there with the form values
    // pre-loaded via the same store path the Generate page uses.
    // The Defend page reads lastGeneratedTransaction at mount via
    // its useGenerateControls hook (the same one we already use
    // in the compact form here, which auto-defaults to the store
    // value when present). We don't need a URL search param.
    void tx;
    navigate(ROUTES.defend);
  }

  return (
    <article className="bg-[var(--bg-panel)] border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4 flex flex-col">
      <header className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity aria-hidden style={{ color: LOOP_LEGS.defend.tokenVar }} />
          <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">Defend</h3>
        </div>
        <button
          onClick={() => navigate(ROUTES.defend)}
          className="text-[0.6875rem] text-[var(--accent-cyan)] hover:text-[var(--accent-cyan-dim)] transition-colors"
        >
          See all
        </button>
      </header>
      {lastTx ? (
        <p className="text-[0.625rem] font-mono text-[var(--text-muted)] mb-2">
          last generated: <span className="text-[var(--text-primary)]">{lastTx.transaction_id ?? "?"}</span>
        </p>
      ) : (
        <div className="flex items-center gap-2 text-[0.625rem] font-mono text-[var(--text-muted)] mb-2">
          <Activity aria-hidden size="inline" className="opacity-60" />
          <span>defaults: dataset medians</span>
        </div>
      )}
      <div className="flex-1">
        <TransactionBuilderForm onSubmit={handleSubmit} variant="compact" />
      </div>
    </article>
  );
}

// Phase 10.5 §5.1 step 3: the Improve card moves here from the
// former ClosedLoopStages section. Its content is unchanged - icon,
// one-sentence tagline, "Try it ->" link to /loop - but the card
// shell keeps the leg-color border-top accent the original
// StageCard used, preserving H.67#10's asymmetry principle within
// the merged 4-card row.
function ImproveMini() {
  return (
    <article
      className="bg-[var(--bg-panel)] border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4 flex flex-col"
      style={{ borderTop: `4px solid ${LOOP_LEGS.improve.tokenVar}` }}
    >
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp aria-hidden style={{ color: LOOP_LEGS.improve.tokenVar }} />
        <span
          className="text-[0.6875rem] font-mono uppercase tracking-[0.12em]"
          style={{ color: LOOP_LEGS.improve.tokenVar }}
        >
          {LOOP_LEGS.improve.label}
        </span>
      </div>
      <h3 className="font-display text-[1.5rem] font-semibold text-[var(--text-primary)] tracking-[-0.01em]">
        Improve
      </h3>
      <p className="text-[0.8125rem] text-[var(--text-secondary)] leading-[1.55] mt-2 flex-1">
        Extract evasion patterns from the model's misses, synthesize new adversarial rows, and measure the delta.
      </p>
      <Link
        to={ROUTES.loop}
        className="inline-flex items-center gap-1 mt-4 text-[0.8125rem] text-[var(--accent-cyan)] hover:text-[var(--accent-cyan-dim)] transition-colors"
      >
        Try it <ArrowRight aria-hidden />
      </Link>
    </article>
  );
}
