import { cn } from "./cn";

// H.2.1: one horizontal bar variant, 0-100.
interface ProgressProps {
  value: number; // 0-100
  className?: string;
  ariaLabel?: string;
}

export function Progress({ value, className, ariaLabel }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={clamped}
      aria-label={ariaLabel}
      className={cn(
        "w-full h-1.5",
        "bg-[var(--bg-elevated)]",
        "rounded-full",
        "overflow-hidden",
        className,
      )}
    >
      <div
        className="h-full bg-[var(--accent-cyan)] transition-all duration-300"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}