import { useEffect, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { X } from "../icons";
import { cn } from "./cn";

// H.2.4: Sheet/Dialog overlays MAY have a shadow, but no box-shadow
// is used here; border contrast carries the layering instead.
//
// `title` accepts ReactNode (not just string) so the chrome can
// pass a leading icon plus the title text in one slot without
// nesting a wrapper - same API extension Phase 5 made to Dialog.
//
// Phase 9.5 step 3: Sheet open/close is wrapped in AnimatePresence
// with opacity + small directional movement only (per H.71 §4.1:
// "opacity + small directional movement only, no bounce/scale/
// rotate"). Use case mapping: H.71 §G ("Identify drawer (medium)
// - Sheet open/close feels intentional, no galleries or shared-
// element drama"). The exit transition is preserved by keeping
// the component mounted during AnimatePresence's exit phase via
// the conditional `open && <motion.aside>` - AnimatePresence
// then keeps the motion element alive until exit completes.
interface SheetProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
}

const PANEL_DURATION_S = 0.18;
const BACKDROP_DURATION_S = 0.12;

export function Sheet({ open, onClose, title, children }: SheetProps) {
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // Phase 9.5 reduced-motion: when the user prefers reduced motion,
  // we render the panel immediately (no slide, no fade) so the
  // settled end-state is what they get from frame 1. AnimatePresence
  // still wraps the conditional so the open/close lifecycle is
  // identical - only the durations and offsets are skipped.
  const panelInitial = reduceMotion ? false : { x: 24, opacity: 0 };
  const panelAnimate = reduceMotion ? { x: 0, opacity: 1 } : { x: 0, opacity: 1 };
  const panelExit = reduceMotion ? { x: 0, opacity: 1 } : { x: 24, opacity: 0 };
  const panelTransition = reduceMotion
    ? { duration: 0 }
    : { duration: PANEL_DURATION_S, ease: "easeOut" as const };
  const backdropTransition = reduceMotion
    ? { duration: 0 }
    : { duration: BACKDROP_DURATION_S, ease: "easeOut" as const };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="sheet-root"
          className="fixed inset-0 z-50 flex justify-end"
          role="dialog"
          aria-modal="true"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={backdropTransition}
        >
          <motion.div
            className="absolute inset-0 bg-[var(--bg-base)] opacity-60"
            onClick={onClose}
            aria-hidden="true"
          />
          <motion.aside
            key="sheet-panel"
            className={cn(
              "relative h-full w-[420px] max-w-[90vw]",
              "bg-[var(--bg-panel)]",
              "border-l border-[var(--border-strong)]",
              "overflow-y-auto",
            )}
            initial={panelInitial}
            animate={panelAnimate}
            exit={panelExit}
            transition={panelTransition}
          >
            <header className="flex items-center justify-between h-12 px-4 border-b border-[var(--border-subtle)]">
              <h2 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
                {title}
              </h2>
              <button
                onClick={onClose}
                aria-label="Close"
                className="p-1 rounded text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)]"
              >
                <X aria-hidden />
              </button>
            </header>
            <div className="p-4">{children}</div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  );
}