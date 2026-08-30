import { useState, type ReactNode } from "react";
import { cn } from "./cn";

// H.2.1: one variant. Used for SHAP explanations and chart data
// points later. Native title is replaced with a controlled popover
// for consistent token-based styling.
interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Tooltip({ content, children, className }: TooltipProps) {
  const [open, setOpen] = useState(false);
  return (
    <span
      className={cn("relative inline-flex", className)}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      {children}
      {open && (
        <span
          role="tooltip"
          className={cn(
            "absolute z-50 left-1/2 -translate-x-1/2 top-full mt-2",
            "px-2 py-1",
            "text-[0.75rem]",
            "bg-[var(--bg-elevated)]",
            "text-[var(--text-primary)]",
            "border border-[var(--border-strong)]",
            "rounded-[var(--radius-input)]",
            "whitespace-nowrap",
            "pointer-events-none",
          )}
        >
          {content}
        </span>
      )}
    </span>
  );
}