// Phase 9 - features/loop/use-loop.ts
// The ONE shared TanStack Query hook file for the Loop page. Per
// the Phase 9 spec step 1:
//   "a query hook for `getApiClient().getLoopHistory()`, and a
//    hook wrapping `getApiClient().runLoop(req, onEvent)` via
//    `lib/use-event-stream.ts` (Phase 4) - remember `runLoop`'s
//    signature returns an unsubscribe function directly, not a
//    Promise, per 'The API client interface' above; make sure
//    this hook's cleanup (on unmount, or on starting a new run
//    while one is active) actually calls that unsubscribe function,
//    or you will leak an open SSE connection or a dangling
//    `setInterval` (in demo mode) every time this page re-renders."
//
// Critical detail: the unsubscribe-on-cleanup requirement is not
// optional polish. Per spec DO-NOT list:
//   "Let an unmounted or superseded SSE/demo-interval subscription
//    keep running in the background - the unsubscribe-on-cleanup
//    requirement in step 1 is not optional polish."
//
// This is the only file in features/loop/ that imports from
// lib/api/. Everything else reads through these hooks (mirrors the
// Phase 6 identify/use-attacks.ts rule).

import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getApiClient } from "../../lib/api/client";
import { useEventStream } from "../../lib/use-event-stream";
import type { LoopEvent, LoopHistoryEntry, LoopRunRequest } from "../../lib/api/types";

/**
 * useLoopHistory() - query for the run-history table. The
 * local-state "this session" list is kept separately (in the
 * page) and prepended on run_complete; this query is the
 * server-side history fixture.
 */
export function useLoopHistory() {
  return useQuery<LoopHistoryEntry[]>({
    queryKey: ["loop", "history"],
    queryFn: () => getApiClient().getLoopHistory(),
    staleTime: 30_000,
  });
}

export interface UseRunLoopResult {
  events: LoopEvent[];
  isStreaming: boolean;
  error: Error | null;
  /** True when the last received event was a `run_complete` (or
   *  `error`) - the run is finished. */
  isComplete: boolean;
  /** Start a new run. Cancels any in-progress run first. */
  start: (req: LoopRunRequest) => void;
  /** Clear the event list and any error. Does not cancel an
   *  in-progress run; the run continues to call onEvent and
   *  silently drops those events. */
  reset: () => void;
}

/**
 * useRunLoop() - wraps the API client's `runLoop` via
 * `useEventStream`. The cleanup is non-negotiable per spec: when
 * the hook unmounts OR a new run starts while one is active, the
 * previous subscribe's unsubscribe function MUST be called to
 * tear down the open SSE/interval.
 *
 * Implementation note: `useEventStream` is given a single
 * `subscribe` function; we make it re-create the subscription by
 * mutating the `active` flag (which useEventStream keys on) via
 * `version`, an incrementing counter. Each `start` bumps the
 * version, which causes useEventStream's effect to clean up the
 * old subscribe (calling its returned unsubscribe) and call the
 * new one. This is the simplest way to honor the "no overlapping
 * streams" acceptance criterion.
 */
export function useRunLoop(): UseRunLoopResult {
  const [events, setEvents] = useState<LoopEvent[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  // The active request, or null when no run is in progress.
  const reqRef = useRef<LoopRunRequest | null>(null);
  // Increments each time start() is called or reset() is called.
  // useEventStream keys on this so its effect re-runs (cleaning
  // up the old subscription).
  const [version, setVersion] = useState(0);

  const start = useCallback((req: LoopRunRequest) => {
    reqRef.current = req;
    setEvents([]);
    setIsComplete(false);
    setError(null);
    setVersion((v) => v + 1);
  }, []);

  const reset = useCallback(() => {
    reqRef.current = null;
    setEvents([]);
    setIsComplete(false);
    setError(null);
    setVersion((v) => v + 1);
  }, []);

  const stream = useEventStream<LoopEvent>(
    (onEvent) => {
      const req = reqRef.current;
      if (!req) {
        return () => {};
      }
      const unsub = getApiClient().runLoop(req, (e) => {
        onEvent(e);
        if (e.type === "run_complete" || e.type === "error") {
          setIsComplete(true);
        }
        if (e.type === "error") {
          setError(new Error(e.message));
        }
      });
      return unsub;
    },
    version > 0, // active only after the first start()
  );

  // Sync the inner stream's events to our outer state.
  useEffect(() => {
    setEvents(stream.events);
  }, [stream.events]);

  // Derived: a run is "streaming" while events are arriving. Once
  // the last received event is `run_complete` or `error`, the
  // stream is done even though its effect is still mounted.
  // `stream.isStreaming` is the raw hook flag, which stays true
  // for the lifetime of the active=true effect; we narrow it to
  // "actually streaming right now" by AND-ing with "no terminal
  // event received yet." We read from `stream.events` directly
  // (not from the local `events` state, which lags by one render
  // because of the sync effect below) so the button re-enables
  // on the same render that delivers `run_complete`.
  const streamEvents = stream.events;
  const lastEventType =
    streamEvents.length > 0 ? streamEvents[streamEvents.length - 1]?.type : null;
  const isTerminal = lastEventType === "run_complete" || lastEventType === "error";
  const isStreaming = stream.isStreaming && !isTerminal;

  return {
    events,
    isStreaming,
    error,
    isComplete,
    start,
    reset,
  };
}
