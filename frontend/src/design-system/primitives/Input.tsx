import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "./cn";

// H.6.4: never remove focus outline; the global :focus-visible rule
// in index.css provides the 2px var(--accent-cyan) ring.
type InputProps = InputHTMLAttributes<HTMLInputElement>;

// H.2.1 text + number only; built on plain <input>, not Radix.
export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, type = "text", ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-9 px-3 w-full",
        "bg-[var(--bg-base)]",
        "text-[var(--text-primary)]",
        "placeholder:text-[var(--text-muted)]",
        "font-sans text-[0.875rem]",
        "rounded-[var(--radius-input)]",
        "border border-[var(--border-subtle)]",
        "transition-colors duration-150",
        "hover:border-[var(--border-strong)]",
        "focus:border-[var(--accent-cyan)] focus:outline-none",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        className,
      )}
      {...rest}
    />
  );
});