// Phase 4 - lib/use-event-stream.ts
// Shared hook for consuming an event stream. Both Generate (Phase 7)
// and Loop (Phase 9) use this. The shape: take a subscribe function
// that returns an unsubscribe, expose { events, isStreaming } state.

import { useEffect, useRef, useState } from "react";

export interface UseEventStreamResult<T> {
  events: T[];
  isStreaming: boolean;
  reset: () => void;
}

export function useEventStream<T>(
  subscribe: (onEvent: (e: T) => void) => () => void,
  active: boolean = true,
): UseEventStreamResult<T> {
  const [events, setEvents] = useState<T[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventsRef = useRef<T[]>([]);
  // Hold the latest subscribe in a ref so the effect can read the
  // current one without depending on its identity. This avoids the
  // Phase 9 "loop subscription restarts every render" bug: callers
  // (notably useRunLoop) pass an inline arrow function as `subscribe`,
  // which is a new reference on every render. Depending on its
  // identity in the effect deps would cause the effect to clean up
  // and re-mount on every render, which calls the previous
  // subscription's `unsub` (clearing all pending setTimeout timers
  // for events that haven't fired yet) and starts a new
  // subscription - so events scheduled at +50ms, +200ms, etc. are
  // cleared before they fire and the timeline never fills.
  const subscribeRef = useRef(subscribe);
  subscribeRef.current = subscribe;

  useEffect(() => {
    if (!active) return;
    eventsRef.current = [];
    setEvents([]);
    setIsStreaming(true);
    const unsub = subscribeRef.current((e) => {
      eventsRef.current = [...eventsRef.current, e];
      setEvents(eventsRef.current);
    });
    // The cleanup calls the subscriber's unsubscribe function but
    // does NOT call setIsStreaming(false) here - that would cause
    // an infinite setState loop if the caller re-creates the
    // active flag on every render. The flag is set to true at the
    // top of this effect; when the page unmounts entirely the hook
    // is garbage-collected and the state disappears with it.
    return () => {
      unsub();
    };
  }, [active]);

  const reset = () => {
    eventsRef.current = [];
    setEvents([]);
  };

  return { events, isStreaming, reset };
}