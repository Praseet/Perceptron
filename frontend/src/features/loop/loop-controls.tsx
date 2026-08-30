// Phase 9 - features/loop/loop-controls.tsx
// Per the Phase 9 spec step 2:
//   "LoopControls - fraud-type focus (Select: All or one of the
//    seven FRAUD_TYPE_TARGETS keys - cross-check spelling
//    against Appendix B), number of new attacks per cycle
//    (Select: 50 / 100 / 200), max cycles (Select: 1 / 3 / 5),
//    'Run ->' Button. Read the global nav's ?prefill=1cycle
//    search param (set by the 'Run the loop' button, per Phase
//    5) and pre-fill max-cycles to 1 when present."
//
// The parent (loop-page.tsx) reads ?prefill=1cycle and passes
// `initialMaxCycles` as a prop. This keeps LoopControls testable
// in isolation (per the round-1 design decision).

import { useEffect, useState } from "react";
import { Button, Select } from "../../design-system/primitives";
import { Loader2, Play } from "../../design-system/icons";
import { FRAUD_TYPES } from "../../lib/constants";
import type { FraudType } from "../../lib/api/types";

interface LoopControlsProps {
  initialMaxCycles?: 1 | 3 | 5;
  onRun: (req: { fraud_type: FraudType | "all"; n_new_attacks: 50 | 100 | 200; max_cycles: 1 | 3 | 5 }) => void;
  disabled?: boolean;
  isRunning?: boolean;
}

const MAX_CYCLES_OPTIONS = [1, 3, 5] as const;
const N_NEW_PER_OPTION = [50, 100, 200] as const;

export function LoopControls({
  initialMaxCycles = 3,
  onRun,
  disabled,
  isRunning,
}: LoopControlsProps) {
  // All four Selects are controlled, since the spec gives fixed
  // option lists. This makes the form's state recoverable and
  // the Playwright test can assert on current values directly.
  const [fraudType, setFraudType] = useState<FraudType | "all">("all");
  const [nNewAttacks, setNNewAttacks] = useState<50 | 100 | 200>(100);
  const [maxCycles, setMaxCycles] = useState<1 | 3 | 5>(initialMaxCycles);

  // If the parent later changes initialMaxCycles (e.g. the user
  // re-navigates to /loop?prefill=1cycle after the page already
  // mounted), respect it. (Edge case; the normal flow is the
  // initial mount.)
  useEffect(() => {
    setMaxCycles(initialMaxCycles);
  }, [initialMaxCycles]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onRun({ fraud_type: fraudType, n_new_attacks: nNewAttacks, max_cycles: maxCycles });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3" aria-label="Loop controls">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="space-y-1.5">
          <label
            htmlFor="loop-fraud-type"
            className="block text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]"
          >
            Fraud-type focus
          </label>
          <Select
            id="loop-fraud-type"
            value={fraudType}
            onChange={(e) => setFraudType(e.target.value as FraudType | "all")}
            disabled={disabled || isRunning}
            aria-label="Fraud-type focus"
          >
            <option value="all">All</option>
            {FRAUD_TYPES.map((ft) => (
              <option key={ft} value={ft}>
                {ft.replace(/_/g, " ")}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor="loop-n-new"
            className="block text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]"
          >
            New attacks / cycle
          </label>
          <Select
            id="loop-n-new"
            value={String(nNewAttacks)}
            onChange={(e) => {
              const v = Number(e.target.value);
              if (v === 50 || v === 100 || v === 200) {
                setNNewAttacks(v as 50 | 100 | 200);
              }
            }}
            disabled={disabled || isRunning}
            aria-label="New attacks per cycle"
          >
            {N_NEW_PER_OPTION.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor="loop-max-cycles"
            className="block text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]"
          >
            Max cycles
          </label>
          <Select
            id="loop-max-cycles"
            value={String(maxCycles)}
            onChange={(e) => {
              const v = Number(e.target.value);
              if (v === 1 || v === 3 || v === 5) {
                setMaxCycles(v as 1 | 3 | 5);
              }
            }}
            disabled={disabled || isRunning}
            aria-label="Max cycles"
          >
            {MAX_CYCLES_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="flex items-center gap-2 pt-1">
        <Button
          type="submit"
          variant="primary"
          size="md"
          disabled={disabled || isRunning}
          aria-label="Run the closed loop"
        >
          {isRunning ? <Loader2 aria-hidden /> : <Play aria-hidden />}
          {isRunning ? "Running" : "Run →"}
        </Button>
        {disabled && !isRunning && (
          <span className="text-[0.6875rem] text-[var(--text-muted)] font-mono">
            connecting...
          </span>
        )}
      </div>
    </form>
  );
}
