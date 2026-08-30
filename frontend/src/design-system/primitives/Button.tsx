import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "./cn";

type ButtonVariant = "primary" | "secondary" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: ReactNode;
}

// H.6.2: no spinner, preserve dimensions while pending, no multiple
// cyan primary buttons in the same panel (caller responsibility).
// H.6.4: never remove focus outline. Default browser focus-visible is
// overridden by the global :focus-visible rule in index.css (the
// 2px var(--accent-cyan) outline).
export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium",
        "rounded-[var(--radius-input)]",
        "transition-colors duration-150",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" &&
          "bg-[var(--accent-cyan)] text-[var(--bg-base)] hover:bg-[var(--accent-cyan-dim)]",
        variant === "secondary" &&
          "bg-transparent text-[var(--text-primary)] border border-[var(--border-strong)] hover:bg-[var(--bg-elevated)]",
        variant === "ghost" &&
          "bg-transparent text-[var(--text-secondary)] hover:text-[var(--accent-cyan)] hover:bg-[var(--bg-elevated)]",
        size === "sm" && "h-8 px-3 text-[0.8125rem]",
        size === "md" && "h-9 px-4 text-[0.875rem]",
        size === "lg" && "h-10 px-5 text-[0.9375rem]",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}