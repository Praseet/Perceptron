// Phase 6 - features/identify/attack-detail-drawer.tsx
// The detail drawer for a single attack. Phase 2 Sheet, full
// description, feasibility rationale (only what's in the source
// data - the spec is explicit: "if the unified file from Phase 0
// didn't carry a rationale field over from the prose in
// docs/ATTACK_TAXONOMY.md, render what's available rather than
// fabricating a rationale that wasn't in the source"). The four
// attacks with a wired generator_profile_id (SE-001, KYC-002,
// PR-003, AI-004) get a "Generate a sample ->" button that
// navigates to /generate?attack_id=<id> via URL search param (per
// the spec's "this is a one-time navigation hint" reasoning).

import { useNavigate } from "react-router-dom";
import { Sheet } from "../../design-system/primitives/Sheet";
import { Button } from "../../design-system/primitives/Button";
import { Badge } from "../../design-system/primitives/Badge";
import { Sparkles, ArrowRight, Radar } from "../../design-system/icons";
import { ROUTES } from "../../lib/constants";
import type { Attack } from "../../lib/api/types";
import { CATEGORY_COLOR } from "./attack-filter-bar";

const CATEGORY_LABEL: Record<Attack["category"], string> = {
  A: "A - Social Eng.",
  B: "B - Synthetic ID",
  C: "C - Payment Rail",
  D: "D - AI-Specific",
  E: "E - Behavioral",
};

const CATEGORY_LONG: Record<Attack["category"], string> = {
  A: "AI-Generated Social Engineering",
  B: "Synthetic Identity and KYC Fraud",
  C: "Payment Rail Exploitation",
  D: "AI-Specific Attacks",
  E: "Behavioral Manipulation",
};

interface AttackDetailDrawerProps {
  attack: Attack | null;
  open: boolean;
  onClose: () => void;
}

export function AttackDetailDrawer({
  attack,
  open,
  onClose,
}: AttackDetailDrawerProps) {
  const navigate = useNavigate();

  if (!attack) return null;
  const color = CATEGORY_COLOR[attack.category];
  const canGenerate = attack.generator_profile_id != null;

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title={
        <span className="inline-flex items-center gap-2">
          <Radar aria-hidden style={{ color }} />
          <span className="text-[var(--accent-cyan)] font-mono text-[0.8125rem]">
            {attack.id}
          </span>
        </span>
      }
    >
      <div className="space-y-5">
        <header>
          <h3 className="text-page-title text-[var(--text-primary)] leading-tight">
            {attack.name}
          </h3>
          <div className="mt-2 flex items-center flex-wrap gap-2">
            <span
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[0.6875rem] font-medium rounded-full border"
              style={{ color, borderColor: color, backgroundColor: "transparent" }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: color }}
                aria-hidden
              />
              {CATEGORY_LABEL[attack.category]}
            </span>
            <span className="text-[0.6875rem] font-mono text-[var(--text-muted)]">
              {CATEGORY_LONG[attack.category]}
            </span>
          </div>
        </header>

        <Section title="Description">
          {/* Descriptions are sourced from the taxonomy prose in
              docs/ATTACK_TAXONOMY.md and are now carried in the
              unified attacks.json fixture, so the real description
              renders for all 25 attacks. The fallback below stays on
              guard for any row that lacks one (e.g. a transient
              fixture mutation) so we never fabricate prose - we only
              show what the source actually carries. */}
          {attack.description ? (
            <p className="text-[0.875rem] text-[var(--text-secondary)] leading-[1.6]">
              {attack.description}
            </p>
          ) : (
            <p className="text-[0.8125rem] text-[var(--text-muted)] italic">
              No description is carried in the fixture for this
              attack. The source prose in{" "}
              <span className="font-mono">docs/ATTACK_TAXONOMY.md</span>
              {" "}covers it.
            </p>
          )}
        </Section>

        <Section title="Feasibility rationale">
          {/* Per the spec: "feasibility rationale (if attacks.json
              has one - if the unified file from Phase 0 didn't
              carry a rationale field over from the prose in
              docs/ATTACK_TAXONOMY.md, render what's available
              rather than fabricating a rationale that wasn't in
              the source)." The current fixture has a single
              feasibility number (1-5) per attack and no rationale
              field. We render the number honestly. */}
          <p className="text-[0.875rem] text-[var(--text-secondary)] leading-[1.6]">
            <span className="text-[var(--text-primary)] font-mono">
              {attack.feasibility}
            </span>
            {" "}out of 5 - per the source taxonomy doc
            <span className="text-[var(--text-muted)]"> (</span>
            <span className="text-[var(--text-muted)] font-mono">docs/ATTACK_TAXONOMY.md</span>
            <span className="text-[var(--text-muted)]">)</span>.
            A narrative rationale is not present in the unified
            fixture; the source prose covers it.
          </p>
        </Section>

        <Section title="Implementation">
          <div className="space-y-2">
            <Row label="Status">
              <Badge
                variant="neutral"
                label={
                  attack.status === "implemented"
                    ? "Implemented"
                    : attack.status === "partial"
                      ? "Partial"
                      : attack.status === "novel"
                        ? "Novel"
                        : attack.status === "future"
                          ? "Future"
                          : "Conceptual"
                }
              />
            </Row>
            <Row label="Fraud type">
              <span className="text-data text-[var(--text-primary)]">
                {attack.fraud_type ?? <span className="text-[var(--text-muted)]">null</span>}
              </span>
            </Row>
            <Row label="Generator profile">
              <span className="text-data text-[var(--text-primary)]">
                {attack.generator_profile_id ?? <span className="text-[var(--text-muted)]">null</span>}
              </span>
            </Row>
          </div>
        </Section>

        {/* Per the spec: the "Generate a sample ->" button is
            shown ONLY for the four attacks with a wired
            generator_profile_id. For the other 21 attacks the
            button is not rendered. */}
        {canGenerate && (
          <div className="pt-2 border-t border-[var(--border-subtle)]">
            <Button
              variant="primary"
              onClick={() => {
                onClose();
                navigate(
                  `${ROUTES.generate}?attack_id=${encodeURIComponent(attack.id)}`,
                );
              }}
              className="w-full"
            >
              <Sparkles aria-hidden />
              <span>Generate a sample</span>
              <ArrowRight aria-hidden />
            </Button>
            <p className="mt-2 text-[0.6875rem] text-[var(--text-muted)] font-mono text-center">
              Navigates to /generate?attack_id={attack.id} (URL search param, not the store)
            </p>
          </div>
        )}
      </div>
    </Sheet>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h4 className="text-[0.6875rem] font-mono uppercase tracking-[0.12em] text-[var(--text-muted)] mb-2">
        {title}
      </h4>
      {children}
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-2 text-[0.8125rem]">
      <span className="text-[var(--text-muted)] font-mono uppercase tracking-wider text-[0.6875rem]">
        {label}
      </span>
      <span>{children}</span>
    </div>
  );
}
