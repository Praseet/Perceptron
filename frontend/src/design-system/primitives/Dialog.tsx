import { useEffect, type ReactNode } from "react";
import { X } from "../icons";

// H.2.1: used later for the command palette (cmdk composed inside).
// Centered modal variant; no shadow per H.2.4.
//
// `title` accepts ReactNode (not just string) so the chrome can
// pass a leading icon plus the title text in one slot without
// nesting a wrapper - this is the only API extension vs. the
// strict-string version that lived here through Phase 4.
interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: ReactNode;
  children: ReactNode;
}

export function Dialog({ open, onClose, title, children }: DialogProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
    >
      <div
        className="absolute inset-0 bg-[var(--bg-base)] opacity-60"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative w-[480px] max-w-[90vw] bg-[var(--bg-panel)] border border-[var(--border-strong)] rounded-[var(--radius-card)] overflow-hidden">
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
      </div>
    </div>
  );
}