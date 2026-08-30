import { cn } from "./cn";

// H.2.1: shimmers --bg-panel -> --bg-elevated, no spinners. Sized
// via className/style from the call site to match the shape of the
// content it stands in for.
interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={cn(
        "rounded-[var(--radius-input)]",
        "bg-[var(--bg-panel)]",
        "animate-pulse",
        className,
      )}
      style={style}
    />
  );
}