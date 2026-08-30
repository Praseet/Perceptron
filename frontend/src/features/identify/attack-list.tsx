// Phase 6 + Phase 10 - features/identify/attack-list.tsx
// Hand-rolled local sort state. NOT virtualized.
// Phase 10 a11y: role="grid" removed from the wrapper because
// it requires role="row" children (collides with native <tr>);
// aria-label moved to the <Table> element.

import { useMemo, useState } from "react";
import { ChevronRight } from "../../design-system/icons";
import { Table, Th, Td, Tr, tableCellDensity } from "../../design-system/primitives/Table";
import type { Attack } from "../../lib/api/types";
import { AttackFeasibilityDots } from "./attack-feasibility-dots";
import { CATEGORY_COLOR } from "./attack-filter-bar";

const CATEGORY_LABEL: Record<Attack["category"], string> = {
  A: "A - Social Eng.",
  B: "B - Synthetic ID",
  C: "C - Payment Rail",
  D: "D - AI-Specific",
  E: "E - Behavioral",
};

const STATUS_COLOR: Record<Attack["status"], string> = {
  implemented: "var(--status-safe)",
  partial: "var(--status-warn)",
  conceptual: "var(--text-muted)",
  novel: "var(--loop-identify)",
  future: "var(--text-muted)",
};
const STATUS_LABEL: Record<Attack["status"], string> = {
  implemented: "Implemented",
  partial: "Partial",
  conceptual: "Conceptual",
  novel: "Novel",
  future: "Future",
};

type SortKey = "id" | "name" | "category" | "feasibility" | "status";
type SortDir = "asc" | "desc";
interface SortState { key: SortKey; dir: SortDir; }

function compareAttacks(a: Attack, b: Attack, sort: SortState): number {
  const av = a[sort.key];
  const bv = b[sort.key];
  let cmp: number;
  if (typeof av === "number" && typeof bv === "number") {
    cmp = av - bv;
  } else {
    cmp = String(av).toLowerCase().localeCompare(String(bv).toLowerCase());
  }
  return sort.dir === "asc" ? cmp : -cmp;
}

interface AttackListProps {
  attacks: Attack[];
  onOpenDetail: (id: string) => void;
}

export function AttackList({ attacks, onOpenDetail }: AttackListProps) {
  const [sort, setSort] = useState<SortState>({ key: "feasibility", dir: "desc" });

  const sorted = useMemo(() => {
    const out = attacks.slice();
    out.sort((a, b) => compareAttacks(a, b, sort));
    return out;
  }, [attacks, sort]);

  const toggleSort = (key: SortKey) => {
    setSort((s) =>
      s.key === key
        ? { key, dir: s.dir === "asc" ? "desc" : "asc" }
        : { key, dir: "desc" },
    );
  };

  const nextDirFor = (key: SortKey): SortDir | null =>
    sort.key === key ? sort.dir : null;

return (
    <div className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-hidden">
      <div className="overflow-x-auto">
        <Table aria-label="Attack list">
          <thead>
            <tr className="border-b border-[var(--border-subtle)]">
              <SortableTh label="ID" active={nextDirFor("id")} onClick={() => toggleSort("id")} className={tableCellDensity.default} />
              <SortableTh label="Name" active={nextDirFor("name")} onClick={() => toggleSort("name")} className={tableCellDensity.default} />
              <SortableTh label="Category" active={nextDirFor("category")} onClick={() => toggleSort("category")} className={tableCellDensity.default} />
              <SortableTh label="Feasibility" active={nextDirFor("feasibility")} onClick={() => toggleSort("feasibility")} className={tableCellDensity.default} />
              <SortableTh label="Status" active={nextDirFor("status")} onClick={() => toggleSort("status")} className={tableCellDensity.default} />
              <th className="w-8 text-right text-[0.75rem] font-semibold uppercase tracking-wider text-[var(--text-muted)] border-b border-[var(--border-subtle)]" aria-label="Open detail" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((attack) => (
              <Tr
                key={attack.id}
                onClick={() => onOpenDetail(attack.id)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onOpenDetail(attack.id);
                  }
                }}
                tabIndex={0}
                role="button"
                aria-label={`Open ${attack.name} detail`}
                className="cursor-pointer"
              >
                <Td className={tableCellDensity.default}>
                  <span className="font-mono text-[0.8125rem] text-[var(--text-mono)] tabular-nums">{attack.id}</span>
                </Td>
                <Td className={tableCellDensity.default}>
                  <span className="text-[0.875rem] text-[var(--text-primary)]">{attack.name}</span>
                </Td>
                <Td className={tableCellDensity.default}>
                  <CategoryChip category={attack.category} />
                </Td>
                <Td className={tableCellDensity.default}>
                  <AttackFeasibilityDots feasibility={attack.feasibility} />
                </Td>
                <Td className={tableCellDensity.default}>
                  <StatusChip status={attack.status} />
                </Td>
                <td className="w-8 text-right">
                  <ChevronRight aria-hidden style={{ color: "var(--text-muted)" }} />
                </td>
              </Tr>
            ))}
          </tbody>
        </Table>
      </div>
    </div>
  );
}

function SortableTh({ label, active, onClick, className }: { label: string; active: SortDir | null; onClick: () => void; className?: string; }) {
  return (
    <Th sortDirection={active} onSort={onClick} className={className}>
      {label}
    </Th>
  );
}

function CategoryChip({ category }: { category: Attack["category"] }) {
  const c = CATEGORY_COLOR[category];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[0.6875rem] font-medium rounded-full border"
      style={{ color: c, borderColor: c, backgroundColor: "transparent" }}
      aria-label={`Category ${category}`}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c }} aria-hidden />
      {CATEGORY_LABEL[category]}
    </span>
  );
}

function StatusChip({ status }: { status: Attack["status"] }) {
  const c = STATUS_COLOR[status];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 text-[0.6875rem] font-medium rounded-full border"
      style={{ color: c, borderColor: c, backgroundColor: "transparent" }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c }} aria-hidden />
      {STATUS_LABEL[status]}
    </span>
  );
}