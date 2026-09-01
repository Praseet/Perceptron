// Phase 12 (§12.17.6) - features/defend/threshold-line.tsx
// A single horizontal number line from 0 to 1: a fixed tick at the
// operating threshold and the transaction's actual probability plotted
// as a dot, colored by which side of the threshold it lands on. This
// connects probability + threshold + decision into one glanceable
// object instead of three separate facts the user has to recombine.
//
// It is the same "decision gate" concept LoopFlowScene's Beat 3
// establishes (§12.17.6: a threshold something either clears or
// doesn't), expressed at page scale - coherent visual vocabulary, not
// repetition.
//
// Motion: the dot's position animates via transform: translateX (GPU-
// only), 250ms MOTION_EASE - retargets smoothly when a new score
// lands. No layout properties animate.

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MOTION_EASE } from "../../design-system/motion";

interface ThresholdLineProps {
  probability: number | null;
  threshold: number;
}

const TRACK_H = 2;

export function ThresholdLine({ probability, threshold }: ThresholdLineProps) {
  const trackRef = useRef<HTMLDivElement | null>(null);
  const [width, setWidth] = useState(0);
  const reduceMotion = useReducedMotion();

  // Track width measurement - same ResizeObserver pattern the
  // LoopFlowScene skeleton uses (§12.5.2.1's established technique).
  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    const compute = () => setWidth(el.clientWidth);
    compute();
    const ro = new ResizeObserver(compute);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const flagged = probability != null && probability >= threshold;
  const dotColor = flagged ? "var(--risk-critical)" : "var(--status-safe)";
  // 4px inset each side so the 0 and 1 dots aren't clipped.
  const usable = Math.max(0, width - 8);
  const dotX = probability == null ? 0 : 4 + probability * usable;

  return (
    <div className="pt-1">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[0.625rem] font-mono text-[var(--text-muted)] tabular-nums">
          0
        </span>
        <span className="text-[0.625rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          decision boundary
        </span>
        <span className="text-[0.625rem] font-mono text-[var(--text-muted)] tabular-nums">
          1
        </span>
      </div>
      <div
        ref={trackRef}
        className="relative h-10"
        role="img"
        aria-label={
          probability == null
            ? "Probability decision line, no transaction scored yet"
            : `Probability ${probability.toFixed(3)} versus threshold ${threshold.toFixed(2)}: ${
                flagged ? "flagged" : "legitimate"
              }`
        }
      >
        {/* the track */}
        <div
          className="absolute left-0 right-0 bg-[var(--border-strong)]"
          style={{ top: 19, height: TRACK_H }}
        />
        {/* quartile ticks */}
        {[0.25, 0.5, 0.75].map((q) => (
          <div
            key={q}
            aria-hidden
            className="absolute w-px h-2 bg-[var(--border-subtle)]"
            style={{ left: 4 + q * usable, top: 14 }}
          />
        ))}
        {/* the threshold tick - fixed, accent, labeled */}
        <div
          aria-hidden
          className="absolute w-[2px] h-5 bg-[var(--accent-cyan)]"
          style={{ left: 4 + threshold * usable, top: 10 }}
        />
        <span
          className="absolute text-[0.625rem] font-mono text-[var(--accent-cyan)] tabular-nums whitespace-nowrap"
          style={{
            left: Math.min(Math.max(0, 4 + threshold * usable - 14), Math.max(0, width - 40)),
            top: 26,
          }}
        >
          thr {threshold.toFixed(2)}
        </span>
        {/* the probability dot */}
        {probability != null && (
          <motion.div
            aria-hidden
            className="absolute rounded-full"
            style={{
              width: 10,
              height: 10,
              top: 15,
              left: 0,
              backgroundColor: dotColor,
            }}
            initial={reduceMotion ? false : { opacity: 0, x: dotX - 5 }}
            animate={
              reduceMotion
                ? { opacity: 1 }
                : { opacity: 1, x: dotX - 5 }
            }
            transition={{ duration: 0.25, ease: MOTION_EASE }}
          />
        )}
        {probability == null && (
          <p className="absolute left-0 top-[26px] text-[0.625rem] font-mono text-[var(--text-muted)]">
            score a transaction to plot its probability
          </p>
        )}
      </div>
    </div>
  );
}
