// Phase 6 - features/identify/attack-feasibility-dots.tsx
// The feasibility column visual. Renders `feasibility` filled dots
// out of the actual scale's max (5) with the numeric rating always
// available as a title tooltip - the "never dots alone" rule.
//
// Per the Phase 6 spec the page prompt says "1-3 filled dots" in
// its prose but resolves the discrepancy by saying "render that
// many filled dots out of that scale's max" using whatever the
// data actually contains. The attacks.json scale is 1-5
// (consistent with Appendix A and the source taxonomy doc), so
// the dots render 0-5 filled out of 5. The PROGRESS.md entry
// documents the 1-3 vs 1-5 discrepancy and the chosen reading.

interface AttackFeasibilityDotsProps {
  feasibility: 1 | 2 | 3 | 4 | 5;
  max?: number;
}

export function AttackFeasibilityDots({
  feasibility,
  max = 5,
}: AttackFeasibilityDotsProps) {
  // tabular-nums per H.68 so the number in the tooltip does not
  // shift the surrounding layout when a different attack's row is
  // hovered and the title text changes.
  return (
    <span
      className="inline-flex items-center gap-1.5 tabular-nums"
      title={`Feasibility ${feasibility} / ${max}`}
      aria-label={`Feasibility ${feasibility} out of ${max}`}
    >
      <span className="inline-flex gap-0.5" aria-hidden="true">
        {Array.from({ length: max }, (_, i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full border"
            style={{
              backgroundColor:
                i < feasibility ? "var(--accent-cyan)" : "transparent",
              borderColor:
                i < feasibility
                  ? "var(--accent-cyan)"
                  : "var(--border-strong)",
            }}
          />
        ))}
      </span>
      <span className="text-[0.6875rem] text-[var(--text-muted)] font-mono">
        {feasibility}/{max}
      </span>
    </span>
  );
}
