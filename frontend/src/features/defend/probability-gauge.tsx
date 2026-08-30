// Phase 8 - features/defend/probability-gauge.tsx
// Custom SVG arc gauge, 0-100, with a tick mark at the live
// operating threshold. Per the spec:
//   "ProbabilityGauge - custom SVG arc, 0-100, with a tick mark
//    at the live operating threshold pulled from getPrCurve()'s
//    operating_point.threshold (never hardcoded - this value
//    should visibly move if the demo fixture's threshold value
//    changes, proving it's wired live and not a fixed illustration)."
// This is the ONLY non-Recharts chart in Phase 8 - the spec is
// explicit that it must be a custom SVG, not a Recharts radial bar.

import { useEvalPrCurve } from "./use-defend";

interface ProbabilityGaugeProps {
  /** The probability to render, 0-1. */
  probability: number | null;
  /** Optional className for layout sizing. */
  className?: string;
}

// Geometry. The arc spans from -90deg (left, 0% mark) to +90deg
// (right, 100% mark), with 0% at the bottom-left and 100% at the
// bottom-right - the classic semicircle gauge orientation.
const CX = 100;
const CY = 90;
const R = 75;
const START_DEG = -180; // left
const END_DEG = 0; // right
// The full arc passes through -90deg (top). 0% sits at the left
// endpoint (-180deg = 180deg = -180 in svg terms), 100% at the
// right endpoint (0deg).

// Convert a percentage (0-100) to a point on the arc.
function polar(pct: number): { x: number; y: number } {
  const t = Math.max(0, Math.min(100, pct)) / 100;
  // We rotate the gauge: 0% at the LEFT, 100% at the RIGHT, the
  // top of the arc is the midpoint. In SVG coordinates, that's
  // START_DEG + t * (END_DEG - START_DEG) = -180 + t * 180.
  const deg = START_DEG + t * (END_DEG - START_DEG);
  const rad = (deg * Math.PI) / 180;
  return { x: CX + R * Math.cos(rad), y: CY + R * Math.sin(rad) };
}

// Build an SVG arc path from start% to end% on the gauge.
function arcPath(startPct: number, endPct: number): string {
  const start = polar(startPct);
  const end = polar(endPct);
  // The arc spans less than 180deg unless startPct=0 and endPct=100.
  // Use small-arc-flag = 0 (large-arc), sweep-flag = 1 (clockwise
  // in screen-coords, which is the natural gauge direction).
  const largeArc = endPct - startPct > 50 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${R} ${R} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

// Map a probability to a color band per the 5-tier risk
// spectrum (Phase 3 Badge) - critical / high / medium / low /
// minimal. These are the same tokens the Badge uses.
function colorForProbability(p: number): string {
  if (p >= 0.9) return "var(--risk-critical)";
  if (p >= 0.7) return "var(--risk-high)";
  if (p >= 0.5) return "var(--risk-medium)";
  if (p >= 0.3) return "var(--risk-low)";
  return "var(--status-safe)";
}

export function ProbabilityGauge({ probability, className }: ProbabilityGaugeProps) {
  const prCurve = useEvalPrCurve();
  // The threshold value is the source of truth for the tick
  // mark. It comes from the live query; if the demo fixture's
  // pr-curve.json is edited, this number visibly moves.
  const threshold = prCurve.data?.operating_point.threshold ?? 0.5;
  const probPct = probability == null ? null : Math.max(0, Math.min(100, probability * 100));

  return (
    <div className={"flex flex-col items-center " + (className ?? "")}>
      <svg
        viewBox="0 0 200 110"
        width="200"
        height="110"
        role="img"
        aria-label={
          probPct == null
            ? "Probability gauge, awaiting prediction"
            : `Probability gauge at ${probPct.toFixed(2)} percent, operating threshold ${(threshold * 100).toFixed(0)} percent`
        }
      >
        {/* Track (the un-reached portion of the arc, in muted color) */}
        <path
          d={arcPath(0, 100)}
          fill="none"
          stroke="var(--border-subtle)"
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* Fill (the reached portion) */}
        {probPct != null && probPct > 0 && (
          <path
            d={arcPath(0, probPct)}
            fill="none"
            stroke={colorForProbability(probability ?? 0)}
            strokeWidth="10"
            strokeLinecap="round"
          />
        )}
        {/* Operating-threshold tick mark. Drawn at the threshold
            percentage on the arc. Vertical line in --accent-cyan
            so it reads as a "marker" not part of the value. */}
        {(() => {
          const tick = polar(threshold * 100);
          return (
            <g>
              <line
                x1={tick.x}
                y1={tick.y - 12}
                x2={tick.x}
                y2={tick.y + 12}
                stroke="var(--accent-cyan)"
                strokeWidth="2"
              />
              <text
                x={tick.x}
                y={tick.y - 16}
                textAnchor="middle"
                className="font-mono tabular-nums"
                style={{ fontSize: 8, fill: "var(--accent-cyan)" }}
              >
                {(threshold * 100).toFixed(0)}%
              </text>
            </g>
          );
        })()}
        {/* Center probability readout. tabular-nums per H.68.1. */}
        <text
          x={CX}
          y={CY + 5}
          textAnchor="middle"
          className="font-mono tabular-nums"
          style={{ fontSize: 18, fill: "var(--text-primary)" }}
        >
          {probPct == null
            ? "\u2014"
            : `${probPct.toFixed(2)}%`}
        </text>
        <text
          x={CX}
          y={CY + 18}
          textAnchor="middle"
          className="font-mono"
          style={{ fontSize: 7, fill: "var(--text-muted)" }}
        >
          PROBABILITY
        </text>
      </svg>
      <p className="text-[0.6875rem] font-mono text-[var(--text-muted)] mt-1">
        operating threshold: <span className="tabular-nums text-[var(--accent-cyan)]">{(threshold * 100).toFixed(0)}%</span>
        {" "}(from getPrCurve)
      </p>
    </div>
  );
}
