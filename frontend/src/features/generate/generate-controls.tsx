// Phase 7 - features/generate/generate-controls.tsx
// The shared Generate controls (attack select, urgency select, user-id
// input, Generate button, streaming progress, error message). Used by:
//   1. The full-page Generate page (variant="full", default)
//   2. The Home page Generate mini (variant="compact")
//
// The hook is `useGenerateControls` (this same folder). This component
// is purely presentational - it reads from the hook and renders the
// controls + the streaming progress panel + the error banner. The
// caller decides what to do with the resulting GenerateResult
// (the full page shows the whole result panel; the home mini just
// writes the tx_id to Zustand via the caller-provided onSuccess).

import { useEffect } from "react";
import { useAppStore } from "../../lib/store";
import { Button, Select } from "../../design-system/primitives";
import { Loader2, Sparkles, AlertCircle } from "../../design-system/icons";
import { Skeleton } from "../../design-system/primitives/Skeleton";
import {
// (useGenerateControls removed - was unused)
  type Urgency,
  type UseGenerateControlsResult,
} from "./use-generate-controls";

type Variant = "full" | "compact";

interface GenerateControlsProps {
  controls: UseGenerateControlsResult;
  /** When provided, called with the result's transaction_id after a
   *  successful generate. Used by the home mini to write to Zustand. */
  onSuccessTxId?: (txId: string) => void;
  variant?: Variant;
}

// Group a label + a child control, used for both variants. Keeps
// the layout consistent between the full page and the home mini.
function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={htmlFor}
        className="block text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]"
      >
        {label}
      </label>
      {children}
    </div>
  );
}

export function GenerateControls({
  controls,
  onSuccessTxId,
  variant = "full",
}: GenerateControlsProps) {
  const setLastTx = useAppStore((s) => s.setLastGeneratedTransactionId);
  const setLastTxRow = useAppStore((s) => s.setLastGeneratedTransaction);

  // Fire onSuccess when a new result lands. The hook resets `result`
  // to null on every generate() call, so this only fires once per
  // successful call. The compact home mini relies on this side-effect
  // to populate the Zustand store so Defend mini can read it.
  // Phase 8 update: also write the full transaction row to the
  // store so the Defend page's "Load a transaction I just generated"
  // link can pre-fill all 23 fields. The id field stays as a
  // convenience for callers that just want the id.
  useEffect(() => {
    if (!controls.result) return;
    const tx = controls.result.transaction;
    const txId = tx.transaction_id;
    if (!txId) return;
    setLastTx(txId);
    setLastTxRow(tx);
    onSuccessTxId?.(txId);
  }, [controls.result, setLastTx, setLastTxRow, onSuccessTxId]);

  const showFull = variant === "full";

  return (
    <div className={showFull ? "space-y-4" : "space-y-3"}>
      <Field label="Attack vector" htmlFor="generate-attack">
        {controls.attacksLoading ? (
          <Skeleton className="h-9 w-full" />
        ) : controls.attacksError ? (
          <p className="text-[0.75rem] text-[var(--risk-critical)]">
            Couldn’t load attacks.
          </p>
        ) : (
          <Select
            id="generate-attack"
            value={controls.attackId}
            onChange={(e) => controls.setAttackId(e.target.value)}
            disabled={variant === "compact"}
            aria-label="Attack vector"
          >
            {controls.attacks.length === 0 ? (
              <option value="">No attacks available</option>
            ) : (
              controls.attacks.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.id} - {a.name}
                </option>
              ))
            )}
          </Select>
        )}
      </Field>

      <Field label="Urgency" htmlFor="generate-urgency">
        <Select
          id="generate-urgency"
          value={controls.urgency}
          onChange={(e) => controls.setUrgency(e.target.value as Urgency)}
          aria-label="Urgency"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </Select>
      </Field>

      {showFull && (
        <Field label="User" htmlFor="generate-user">
          <input
            id="generate-user"
            type="text"
            value={String(controls.userId ?? "random")}
            onChange={(e) => {
              // Phase 10 user-input fix: accept any text the user
              // types (usernames, emails, ids, "random", or a numeric
              // user id). Forward the raw string to the API; the
              // demo client coerces numeric-looking strings to a
              // number for downstream calls. Empty input falls back
              // to "random" so the placeholder behaviour still
              // works.
              const v = e.target.value;
              if (v === "") {
                controls.setUserId("random");
              } else {
                controls.setUserId(v);
              }
            }}
            className="h-9 px-3 w-full bg-[var(--bg-base)] text-[var(--text-primary)] font-sans text-[0.875rem] rounded-[var(--radius-input)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] focus:border-[var(--accent-cyan)] focus:outline-none transition-colors duration-150"
            aria-label="User (or random)"
            placeholder="random"
          />
        </Field>
      )}

      <div className="flex items-center gap-2 pt-1">
        <Button
          variant="primary"
          size={showFull ? "md" : "sm"}
          onClick={controls.generate}
          disabled={
            controls.isStreaming ||
            !controls.attackId ||
            controls.attacksLoading
          }
          aria-label={showFull ? "Generate attack" : "Generate"}
        >
          {controls.isStreaming ? (
            <Loader2 aria-hidden />
          ) : (
            <Sparkles aria-hidden />
          )}
          {showFull ? "Generate attack" : "Generate"}
        </Button>
        {(controls.result || controls.error) && (
          <Button
            variant="ghost"
            size={showFull ? "md" : "sm"}
            onClick={controls.reset}
          >
            Reset
          </Button>
        )}
      </div>

      {/* Streaming progress. In demo mode, this never appears (the
          demo client has no onProgress events to emit). In live mode
          with SSE, the user sees the backend narrator logging each
          step. */}
      {controls.isStreaming && controls.progress.length > 0 && (
        <div
          className="rounded-[var(--radius-input)] border border-[var(--border-subtle)] bg-[var(--bg-base)] p-3 space-y-1"
          aria-live="polite"
        >
          <p className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
            Streaming progress
          </p>
          <ul className="space-y-0.5 text-[0.75rem] text-[var(--text-secondary)] font-mono">
            {controls.progress.slice(-4).map((msg, i) => (
              <li key={`${i}-${msg.slice(0, 12)}`}>{"> "}{msg}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Error banner. Per the spec: a single failed request that a
          retry might fix gets a transient error pattern. We use an
          inline banner here (not a Toast) because the controls are
          still on screen and the user can hit Generate again. */}
      {controls.error && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-[var(--radius-input)] border border-[var(--risk-critical)] bg-[var(--bg-base)] p-3"
        >
          <AlertCircle
            aria-hidden
            className="mt-0.5 flex-shrink-0"
            style={{ color: "var(--risk-critical)" }}
          />
          <p className="text-[0.75rem] text-[var(--risk-critical)]">
            {controls.error.message}
          </p>
        </div>
      )}
    </div>
  );
}
