import type { CSSProperties } from "react";

interface StatusPillProps {
  color: string; // any CSS color string; the dot picks it up directly
  text: string;
  className?: string;
  style?: CSSProperties;
}

// Small dot + text. Dot color is a prop (NOT hardcoded) so the
// global nav and other contexts can supply different colors with
// the same component. Common colors: --status-safe, --status-warn,
// --status-threat, --text-muted.
export function StatusPill({ color, text, className, style }: StatusPillProps) {
  return (
    <span
      className={"inline-flex items-center gap-2 " + (className ?? "")}
      style={style}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
        aria-hidden="true"
      />
      <span className="text-[0.75rem] text-[var(--text-secondary)]">{text}</span>
    </span>
  );
}