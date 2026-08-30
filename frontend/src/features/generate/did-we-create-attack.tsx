// Phase 7 - features/generate/did-we-create-attack.tsx
// The post-generate confirmation dialog. Per the spec, after a
// successful generate the page shows a Dialog asking "Did we
// just create an attack?" with three actions:
//
//   1. "Yes, add to training set" - sends a request to add the
//      newly-generated transaction to the model's training set.
//      (This is a placeholder in the demo - the demo client
//      simply closes the dialog. The action is wired but the
//      backend behavior is out of scope for Phase 7.)
//   2. "Score in Defend" - navigates to /defend with the
//      generated transaction pre-loaded.
//   3. "Discard" - closes the dialog. The transaction remains
//      available in "Recent generates" for the session.
//
// Uses the existing Dialog primitive (chrome/, not in this
// folder). Open state is fully controlled by the parent.

import { useNavigate } from "react-router-dom";
import { Dialog, Button } from "../../design-system/primitives";
import { Sparkles, ShieldCheck, X } from "../../design-system/icons";
import { ROUTES } from "../../lib/constants";
import type { GenerateResult } from "../../lib/api/types";

interface DidWeCreateAttackProps {
  open: boolean;
  onClose: () => void;
  /** Called when the user picks "Yes, add to training set". */
  onAddToTraining: (result: GenerateResult) => void;
  result: GenerateResult | null;
}

export function DidWeCreateAttack({
  open,
  onClose,
  onAddToTraining,
  result,
}: DidWeCreateAttackProps) {
  const navigate = useNavigate();
  if (!result) return null;

  function goDefend() {
    onClose();
    // The Defend page (Phase 8) will read the tx_id from Zustand
    // (we already wrote it in GenerateControls.onSuccessTxId).
    navigate(ROUTES.defend);
  }

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={
        <span className="flex items-center gap-2">
          <Sparkles aria-hidden size="inline" style={{ color: "var(--loop-attack)" }} />
          Did we just create an attack?
        </span>
      }
    >
      <div className="space-y-3">
        <p className="text-[0.8125rem] text-[var(--text-secondary)]">
          The generator just produced a transaction that passed the
          leakage and schema gates. What would you like to do with
          it?
        </p>
        <dl className="text-[0.75rem] space-y-1.5">
          <div className="flex items-baseline justify-between">
            <dt className="text-[var(--text-muted)] font-mono">attack_id</dt>
            <dd className="text-[var(--text-primary)] font-mono">
              {result.transaction.transaction_id ?? "(no id)"}
            </dd>
          </div>
          <div className="flex items-baseline justify-between">
            <dt className="text-[var(--text-muted)] font-mono">run_id</dt>
            <dd className="text-[var(--text-primary)] font-mono">{result.run_id}</dd>
          </div>
        </dl>
        <div className="flex flex-col gap-2 pt-2">
          <Button
            variant="primary"
            onClick={() => {
              onAddToTraining(result);
              onClose();
            }}
          >
            <Sparkles aria-hidden />
            Yes, add to training set
          </Button>
          <Button variant="secondary" onClick={goDefend}>
            <ShieldCheck aria-hidden />
            Score in Defend
          </Button>
          <Button variant="ghost" onClick={onClose}>
            <X aria-hidden />
            Discard
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
