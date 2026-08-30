import { useState, type ReactNode } from "react";
import { cn } from "./cn";

// H.2.1: built ahead of a concrete need as named "future-flexibility
// scaffolding" in the spec. No current page uses in-page tabs; this
// is the one explicit exception to "don't build ahead of need."
interface Tab {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTabId?: string;
  className?: string;
}

export function Tabs({ tabs, defaultTabId, className }: TabsProps) {
  const [active, setActive] = useState(defaultTabId ?? tabs[0]?.id);
  return (
    <div className={className}>
      <div
        role="tablist"
        className="flex border-b border-[var(--border-subtle)] gap-1"
      >
        {tabs.map((t) => {
          const isActive = t.id === active;
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(t.id)}
              className={cn(
                "h-9 px-3",
                "text-[0.8125rem] font-medium",
                "transition-colors duration-150",
                "-mb-px border-b-2",
                isActive
                  ? "text-[var(--text-primary)] border-[var(--accent-cyan)]"
                  : "text-[var(--text-muted)] border-transparent hover:text-[var(--text-secondary)]",
              )}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      <div className="pt-3">
        {tabs.map((t) =>
          t.id === active ? (
            <div key={t.id} role="tabpanel">
              {t.content}
            </div>
          ) : null,
        )}
      </div>
    </div>
  );
}