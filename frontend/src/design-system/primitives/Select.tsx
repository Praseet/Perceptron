import { forwardRef, type SelectHTMLAttributes, type ReactNode } from "react";
import { cn } from "./cn";

// H.2.1: single-select only (no multi-select needed by any page).
// Built on native <select> (no Radix) to avoid the dependency for a
// primitive that is functionally identical to a styled native select
// in this build.
type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  children: ReactNode;
};

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, children, ...rest },
  ref,
) {
  return (
    <select
      ref={ref}
      className={cn(
        "h-9 px-3 pr-8 w-full",
        "bg-[var(--bg-base)]",
        "text-[var(--text-primary)]",
        "font-sans text-[0.875rem]",
        "rounded-[var(--radius-input)]",
        "border border-[var(--border-subtle)]",
        "transition-colors duration-150",
        "hover:border-[var(--border-strong)]",
        "focus:border-[var(--accent-cyan)] focus:outline-none",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "appearance-none cursor-pointer",
        className,
      )}
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%238B9DC3' stroke-width='2'><path d='M6 9l6 6 6-6'/></svg>\")",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "right 0.75rem center",
      }}
      {...rest}
    >
      {children}
    </select>
  );
});