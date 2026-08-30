// Phase 5 - features/home/hero.tsx
// The hero section: wordmark + headline + sub-headline + loop diagram
// on a slightly darker inset panel + a "static - v1" label + the
// "Run the loop ->" CTA. The loop is in mode="static" (no live
// pulsing) so the hero doesn't compete with the page's own motion;
// the live mode is reserved for the actual /loop page when a run
// is in progress.
//
// The lock decision from Phase 5: "LoopDiagram on a slightly darker
// inset panel (console-like instrument surface), 1px border, small
// 'static - v1' label. Diagram dominates; copy supports."

import { useNavigate } from "react-router-dom";
import { LoopDiagram } from "../../design-system/patterns/loop-diagram";
import { Button } from "../../design-system/primitives";
import { Play, ArrowRight } from "../../design-system/icons";
import { ROUTES } from "../../lib/constants";

export function Hero() {
  const navigate = useNavigate();
  return (
    <section
      className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-8 items-center"
      aria-label="Hero"
    >
      {/* Copy column. On wide screens this is left, diagram is right.
          On narrow screens it stacks (the LoopDiagram is 480x480
          which would overflow a phone, so we hide it below lg). */}
      <div className="space-y-5">
        <p className="text-caption text-[var(--text-muted)] font-mono uppercase tracking-[0.12em]">
          Adversarial Fraud Lab
        </p>
        <h1 className="font-display text-[2.5rem] sm:text-[3.25rem] leading-[1.05] font-semibold tracking-[-0.02em] text-[var(--text-primary)]">
          The AI that learns fraud by{" "}
          <span className="text-[var(--accent-cyan)]">becoming</span> a
          fraudster.
        </h1>
        <p className="text-[0.9375rem] text-[var(--text-secondary)] max-w-[640px] leading-[1.6]">
          Closed-loop red team / blue team for GenAI-powered payment
          fraud. We identify emerging attacks, generate them at scale,
          defend against them, and feed every miss back into the next
          generation.
        </p>
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            onClick={() => navigate(`${ROUTES.loop}?prefill=1cycle`)}
            className="h-10 px-5"
          >
            <Play aria-hidden />
            <span>Run the loop</span>
            <ArrowRight aria-hidden />
          </Button>
          <Button
            variant="ghost"
            onClick={() => navigate(ROUTES.identify)}
            className="h-10 px-5"
          >
            Browse 25 attacks
          </Button>
        </div>
      </div>

      {/* Diagram column. The .console class wraps the diagram in a
          slightly darker instrument surface with 1px border, exactly
          per the locked decision. The "static - v1" label sits in the
          top-right corner to signal this is a presentation, not a
          live node graph. Phase 10.5 §5.4: a one-line caption under
          the panel connects this snapshot to the live diagram on
          /loop so a judge who sees both doesn't wonder if they're
          looking at the same screen twice.
          Phase 10: gate the diagram behind `xl` instead of `lg` so
          the 480px + 32px gap + copy doesn't cause horizontal
          overflow between 1024 and 1280px viewport widths. */}
      <div className="hidden xl:block relative">
        <div className="console border border-[var(--border-subtle)] rounded-[var(--radius-card)] p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[0.625rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
              closed loop
            </span>
            <span className="text-[0.625rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
              static - v1
            </span>
          </div>
          <LoopDiagram mode="static" />
        </div>
        <p className="mt-2 text-[0.625rem] font-mono text-[var(--text-muted)] text-center">
          This is what the system looks like idle. Run a real cycle to watch it move.
        </p>
      </div>
    </section>
  );
}