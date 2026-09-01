// Phase 12 (§12.8.5) - the ONE shared easing curve for all motion added
// in this phase. Sourced from code already in this app per §12.16.4:
// count-up.tsx's "confident settle" uses an ease-out cubic
// (1 - Math.pow(1 - t, 3)), which is exactly this cubic-bezier.
// Import this everywhere Phase 12 adds motion (LoopFlowScene, nav
// underline, new primitives) instead of picking an easing ad hoc.
// As a CSS <easing-function> string it also retargets smoothly when a
// Motion transition is interrupted mid-flight (§12.5.5's requirement).

// Motion transitions (framer-motion's `ease` prop takes the 4-point
// bezier as a tuple, not a CSS string).
export const MOTION_EASE: [number, number, number, number] = [0.33, 1, 0.68, 1];

// The same curve as a CSS <easing-function> for plain CSS transitions.
export const MOTION_EASE_CSS = "cubic-bezier(0.33, 1, 0.68, 1)";

// Shared fast-transition duration for the small crossfades this phase
// adds (skeleton -> scene per §12.5.2.1 Bug A: 150-200ms).
export const MOTION_FAST_MS = 180;
