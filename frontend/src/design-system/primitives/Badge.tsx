import type { HTMLAttributes } from "react";
import { cn } from "./cn";

// H.2.1: every variant takes a required `label` prop. Color is never
// the only signal (accessibility). TypeScript's `label: string` is the
// compile-time guarantee - cannot be omitted.
type BadgeVariant =
  | "neutral"
  | "risk-critical"
  | "risk-high"
  | "risk-medium"
  | "risk-low"
  | "risk-minimal"
  | "loop-identify"
  | "loop-generate"
  | "loop-defend"
  | "loop-improve";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant: BadgeVariant;
  label: string;
}

// Token name -> CSS variable. Centralized here so a future token
// rename touches one place, not nine call sites.
const COLOR_MAP: Record<BadgeVariant, string> = {
  "neutral": "var(--text-secondary)",
  "risk-critical": "var(--risk-critical)",
  "risk-high": "var(--risk-high)",
  "risk-medium": "var(--risk-medium)",
  "risk-low": "var(--risk-low)",
  "risk-minimal": "var(--risk-minimal)",
  "loop-identify": "var(--loop-identify)",
  "loop-generate": "var(--loop-attack)",
  "loop-defend": "var(--loop-defend)",
  "loop-improve": "var(--loop-improve)",
};

export function Badge({ variant, label, className, ...rest }: BadgeProps) {
  const color = COLOR_MAP[variant];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5",
        "px-2 py-0.5",
        "text-[0.75rem] font-medium",
        "rounded-full",
        "border",
        className,
      )}
      style={{
        color,
        borderColor: color,
        backgroundColor: "transparent",
      }}
      {...rest}
    >
      {/* Small leading dot uses the same color - reinforces the
          non-color signal requirement since dot + text together make
          the variant unambiguous to anyone who can see one or the
          other. */}
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}