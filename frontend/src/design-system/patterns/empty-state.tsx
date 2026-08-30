import type { ReactNode } from "react";
import { Button } from "../primitives";

interface EmptyStateProps {
  icon?: ReactNode;
  message: string;
  action?: { label: string; onClick: () => void };
  className?: string;
}

// Generic empty state. Per H.2.6 / "Empty, Loading, and Error States":
// - icon (Lucide, never emoji)
// - one-line explanation of WHY it''s empty (not just "no data")
// - optional single action to resolve it
// The three specific copy strings are NOT hardcoded here; each page
// supplies its own message text.
export function EmptyState({ icon, message, action, className }: EmptyStateProps) {
  return (
    <div
      className={
        "flex flex-col items-center justify-center text-center p-8 rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] " +
        (className ?? "")
      }
    >
      {icon && (
        <div className="text-[var(--text-muted)] mb-3" aria-hidden="true">
          {icon}
        </div>
      )}
      <p className="text-[0.875rem] text-[var(--text-secondary)] max-w-sm">
        {message}
      </p>
      {action && (
        <div className="mt-4">
          <Button variant="secondary" onClick={action.onClick}>
            {action.label}
          </Button>
        </div>
      )}
    </div>
  );
}