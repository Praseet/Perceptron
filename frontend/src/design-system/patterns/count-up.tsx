import { useEffect, useRef, useState } from "react";

interface CountUpProps {
  value: number;
  durationMs?: number;
  format?: (n: number) => string;
  className?: string;
  ariaLabel?: string;
}

// Animates a number from 0 to `value` over `durationMs` (default 1200),
// but only when the element first enters the viewport (IntersectionObserver,
// not a scroll listener). Respects prefers-reduced-motion by rendering
// the final value immediately with no animation.
export function CountUp({
  value,
  durationMs = 1200,
  format,
  className,
  ariaLabel,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const [display, setDisplay] = useState(0);
  const [started, setStarted] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const el = ref.current;
    if (!el) return;

    // Reduced motion: render the final value, no observer needed.
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduceMotion) {
      setStarted(true);
      setDisplay(value);
      return;
    }

    // Phase 10 fix: if the element is already in the viewport on
    // first mount, start immediately. The IntersectionObserver
    // below is a fallback for below-the-fold elements - but
    // Playwright's headless rendering and a lot of common
    // scroll-while-loading patterns can leave the observer
    // unfired if the element never re-enters the viewport, which
    // makes the tile look stuck at 0. We also fall through to
    // "started" after a short delay as a last resort so a
    // numbers-only tile never reads "0" forever.
    const rect = el.getBoundingClientRect();
    const inViewportNow =
      rect.top < window.innerHeight && rect.bottom > 0;
    if (inViewportNow) {
      setStarted(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting && !started) {
          setStarted(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [value, started]);

  useEffect(() => {
    if (!started) return;
    if (typeof window === "undefined") return;
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    if (reduceMotion) {
      setDisplay(value);
      return;
    }
    // Phase 10 fix: when the value updates after the first reveal,
    // animate from the CURRENT displayed value (not from 0) so the
    // tile doesn't "snap back to zero" every time a new event
    // lands. This matters most on the Loop page's CycleDeltaTiles
    // where every metric_update event re-renders the tile.
    const fromValue = display;
    const toValue = value;
    if (fromValue === toValue) return;
    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      // ease-out cubic for a confident settle
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(fromValue + (toValue - fromValue) * eased);
      if (t < 1) raf = requestAnimationFrame(tick);
      else setDisplay(toValue);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [started, value, durationMs]);

  const rendered = format ? format(display) : Math.round(display).toString();
  return (
    <span ref={ref} className={className} aria-label={ariaLabel}>
      {rendered}
    </span>
  );
}