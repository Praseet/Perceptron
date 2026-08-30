// Phase 7 - features/generate/generate-page.tsx
// The real Generate page. Replaces the Phase 5 placeholder.
//
// Layout: 40/60 grid - left column is the GenerateControls
// (attack/urgency/user/Generate button) and the streaming
// progress; right column is the results panel (conversation log,
// materialized transaction, diff against normal, recent
// generates). The page also opens a post-generate "Did we just
// create an attack?" Dialog with three actions.
//
// Deep-link: ?attack_id=<id> in the URL pre-selects the attack.

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Skeleton, Card } from "../../design-system/primitives";
import { EmptyState } from "../../design-system/patterns/empty-state";
import { Sparkles, Inbox } from "../../design-system/icons";
import { pushToast } from "../../design-system/primitives/Toast";
import { useGenerateControls } from "./use-generate-controls";
import { GenerateControls } from "./generate-controls";
import { ConversationLog } from "./conversation-log";
import { TransactionMaterialize } from "./transaction-materialize";
import { DiffAgainstNormal } from "./diff-against-normal";
import { RecentGenerates } from "./recent-generates";
import { DidWeCreateAttack } from "./did-we-create-attack";
import { useAppStore } from "../../lib/store";
import type { GenerateResult } from "../../lib/api/types";

const HEADER_TITLE = "Generate";
const HEADER_SUBTITLE =
  "Produce a synthetic attack transaction from a chosen attack vector.";



export function GeneratePage() {
  const reduceMotion = useReducedMotion();
  const [searchParams, setSearchParams] = useSearchParams();

  // Capture ?attack_id= on first mount only.
  const initialAttackIdRef = useRef<string | null>(
    searchParams.get("attack_id"),
  );
  useEffect(() => {
    if (initialAttackIdRef.current && searchParams.get("attack_id")) {
      const next = new URLSearchParams(searchParams);
      next.delete("attack_id");
      setSearchParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const controls = useGenerateControls({
    initialAttackId: initialAttackIdRef.current ?? undefined,
  });

  // Currently displayed result. selected overrides controls.result
  // when the user clicks a row in RecentGenerates. Phase 10.5 §5.3:
  // if the user generated on the Home page's Generate mini and then
  // clicked "See all", `useAppStore().lastHomeGenerateResult` holds
  // the result they already saw, and we seed `selected` with it so
  // the full page shows the carried-forward result rather than
  // resetting to its empty state. The lazy initializer reads the
  // store exactly once on first mount; if the user navigates
  // directly to /generate without going through the Home mini,
  // the store is empty and `selected` is null (no behavior change).
  const [selected, setSelected] = useState<GenerateResult | null>(
    () => useAppStore.getState().lastHomeGenerateResult,
  );
  const displayed: GenerateResult | null = selected ?? controls.result;

  // Session-local list of all successful results.
  const [history, setHistory] = useState<GenerateResult[]>([]);
  useEffect(() => {
    if (!controls.result) return;
    setHistory((h) => {
      if (h.some((r) => r.run_id === controls.result!.run_id)) return h;
      return [...h, controls.result!];
    });
  }, [controls.result]);

  // Post-generate dialog. Auto-opens on a new result run_id.
  // `lastSeenRunId` is the last run_id the user has acknowledged
  // (by clicking Discard, Score in Defend, etc.). The dialog is
  // open when the currently-displayed result's run_id differs
  // from lastSeenRunId - i.e. there is a new result to acknowledge.
  const [lastSeenRunId, setLastSeenRunId] = useState<string | null>(null);
  const dialogOpen =
    displayed !== null && displayed.run_id !== lastSeenRunId;

  useEffect(() => {
    if (controls.result && controls.result.run_id !== lastSeenRunId) {
      // New result: clear any selected override so the new result
      // is the one displayed, and the dialog auto-opens.
      setSelected(null);
    }
  }, [controls.result, lastSeenRunId]);

  function closeDialog() {
    if (displayed) setLastSeenRunId(displayed.run_id);
  }

  function onSelectResult(r: GenerateResult) {
    setSelected(r);
    setLastSeenRunId(r.run_id);
  }

  function onAddToTraining(r: GenerateResult) {
    pushToast({
      severity: "info",
      message: "Add-to-training pipeline is wired in Phase 9 (Loop).",
    });
    void r;
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-caption font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          Step 2 of 4
        </p>
        <h1 className="text-section-title text-[var(--text-primary)] mt-1">
          {HEADER_TITLE}
        </h1>
        <p className="text-body text-[var(--text-secondary)] mt-2 max-w-2xl">
          {HEADER_SUBTITLE}
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] gap-6 items-start">
        <Card className="p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles aria-hidden size="inline" style={{ color: "var(--loop-attack)" }} />
            <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
              Generate controls
            </h2>
          </div>
          <GenerateControls controls={controls} />
        </Card>

        <div className="space-y-4">
          <AnimatePresence mode="wait">
            {controls.attacksLoading ? (
              <motion.div
                key="gen-loading"
                initial={reduceMotion ? false : { opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={reduceMotion ? { opacity: 1 } : { opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.12 }}
              >
                <Card className="p-4 space-y-3" aria-busy="true">
                  <Skeleton className="h-5 w-1/3" />
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-4 w-3/4" />
                </Card>
              </motion.div>
            ) : controls.attacksError ? (
              <motion.div
                key="gen-error"
                initial={reduceMotion ? false : { opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={reduceMotion ? { opacity: 1 } : { opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.12 }}
              >
                <EmptyState
                  icon={<Inbox size="empty" />}
                  message="Could not load the attack taxonomy. Check that the API is reachable."
                />
              </motion.div>
            ) : !displayed ? (
              <motion.div
                key="gen-empty"
                initial={reduceMotion ? false : { opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={reduceMotion ? { opacity: 1 } : { opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.12 }}
              >
                <EmptyState
                  icon={<Sparkles size="empty" />}
                  message="Pick an attack vector and press Generate. The full transcript and the materialized transaction will land here."
                />
              </motion.div>
            ) : (
              <motion.div
                key="gen-result"
                className="space-y-4"
                initial={reduceMotion ? false : { opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduceMotion ? { opacity: 1, y: 0 } : { opacity: 0, y: -6 }}
                transition={
                  reduceMotion
                    ? { duration: 0 }
                    : { duration: 0.22, ease: "easeOut" }
                }
              >
                <Card className="p-4 space-y-4">
                  <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
                    Conversation
                  </h2>
                  <ConversationLog conversation={displayed.conversation} />
                </Card>
                <Card className="p-4 space-y-4">
                  <TransactionMaterialize result={displayed} />
                </Card>
                {displayed.user_medians && (
                  <DiffAgainstNormal result={displayed} />
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {history.length > 0 && (
            <RecentGenerates
              results={history}
              onSelect={onSelectResult}
            />
          )}
        </div>
      </div>

      <DidWeCreateAttack
        open={dialogOpen}
        onClose={closeDialog}
        onAddToTraining={onAddToTraining}
        result={displayed}
      />
    </div>
  );
}
