import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "./cn";

// H.5.1: only the three surface layers exist. No glass, no gradients.
// H.5.2: 1px solid var(--border-subtle) default border.
// H.5.3: card radius = 8px (var(--radius-card)).
// H.5.4: no gradients.
// H.2.4: no box-shadow on cards. Borders carry the visual hierarchy.
type CardVariant = "default" | "bordered";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  children: ReactNode;
}

export function Card({
  variant = "default",
  className,
  children,
  ...rest
}: CardProps) {
  // "default" and "bordered" share the same shape per H.2.4; the variant
  // prop is kept for API stability and future expansion (e.g. .console
  // contexts could opt into a heavier border treatment).
  return (
    <div
      className={cn(
        "rounded-[var(--radius-card)]",
        "bg-[var(--bg-panel)]",
        "border",
        variant === "default" && "border-[var(--border-subtle)]",
        variant === "bordered" && "border-[var(--border-strong)]",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}