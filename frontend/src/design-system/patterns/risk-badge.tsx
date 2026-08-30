import { Badge } from "../primitives";

// 5-tier risk boundaries. These match the boundaries implied by
// Appendix D''s risk-color naming and the same values used in the
// older docs/DESIGN_SYSTEM.md. Boundary values verified by the
// showcase at exactly 90/70/40/10.
type RiskTier = "critical" | "high" | "medium" | "low" | "minimal";

function tierFromScore(score: number): RiskTier {
  if (score >= 90) return "critical";
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  if (score >= 10) return "low";
  return "minimal";
}

const TIER_VARIANT: Record<RiskTier, Parameters<typeof Badge>[0]["variant"]> = {
  critical: "risk-critical",
  high: "risk-high",
  medium: "risk-medium",
  low: "risk-low",
  minimal: "risk-minimal",
};

const TIER_LABEL: Record<RiskTier, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
  minimal: "Minimal",
};

interface RiskBadgeProps {
  score: number;
  // Renders BOTH the numeric score and the tier name as the label text
  // (e.g. "87 - High"). Never color or number alone.
  className?: string;
}

export function RiskBadge({ score, className }: RiskBadgeProps) {
  const tier = tierFromScore(score);
  const variant = TIER_VARIANT[tier];
  const label = `${score} - ${TIER_LABEL[tier]}`;
  return <Badge variant={variant} label={label} className={className} />;
}