import { ArrowUpRight, ArrowDownRight, Minus } from "../icons";
import { CountUp } from "./count-up";

interface KpiTileProps {
  label: string;
  value: number;
  // Direction the call site considers "good". up-is-good for PR-AUC,
  // recall, precision; down-is-good for false-negative count, latency.
  direction: "up-is-good" | "down-is-good";
  delta?: number; // percent change vs prior period
  format?: (n: number) => string;
  className?: string;
}

// Large mono numeral + label + optional delta chip.
// Delta chip color: green if the change aligns with `direction`, red
// otherwise. Sign convention is per-metric, not hardcoded.
export function KpiTile({
  label,
  value,
  direction,
  delta,
  format,
  className,
}: KpiTileProps) {
  const deltaGood =
    delta == null
      ? null
      : direction === "up-is-good"
        ? delta >= 0
        : delta <= 0;
  const deltaColor = deltaGood
    ? "var(--status-safe)"
    : "var(--risk-critical)";
  const DeltaIcon =
    delta == null
      ? null
      : delta > 0
        ? ArrowUpRight
        : delta < 0
          ? ArrowDownRight
          : Minus;
  return (
    <div
      className={
        "rounded-[var(--radius-card)] bg-[var(--bg-panel)] border border-[var(--border-subtle)] p-4 " +
        (className ?? "")
      }
    >
      <p className="text-caption">{label}</p>
      <p className="text-data-lg mt-1 text-[var(--text-primary)]">
        <CountUp value={value} format={format} />
      </p>
      {delta != null && DeltaIcon && (
        <div
          className="mt-2 inline-flex items-center gap-1 text-[0.6875rem] font-mono tabular-nums"
          style={{ color: deltaColor }}
        >
          <DeltaIcon aria-hidden />
          <span>{Math.abs(delta).toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}