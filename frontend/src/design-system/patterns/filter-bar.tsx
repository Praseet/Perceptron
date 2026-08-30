import { Search } from "../icons";
import { Input } from "../primitives";

export interface FilterChip {
  id: string;
  label: string;
  active: boolean;
  // Optional per-chip accent color. When set, the chip's border,
  // text, and dot use this color in the active state instead of
  // the default --accent-cyan. The inactive state still uses the
  // muted border/text/dot so the chip reads as "off" until clicked.
  // Phase 6's Identify page uses this to carry the
  // category-to-loop-leg color mapping per the spec.
  accent?: string;
}

interface FilterBarProps {
  chips: FilterChip[];
  onChipToggle: (chipId: string) => void;
  searchValue: string;
  onSearchChange: (next: string) => void;
  searchPlaceholder?: string;
  className?: string;
}

// A row of toggle chips + search Input. Fully controlled. Chips are
// styled like the Badge primitive but in a button role with pressed
// state, NOT a new primitive.
export function FilterBar({
  chips,
  onChipToggle,
  searchValue,
  onSearchChange,
  searchPlaceholder,
  className,
}: FilterBarProps) {
  return (
    <div
      className={
        "flex flex-wrap items-center gap-2 " + (className ?? "")
      }
    >
      {chips.map((chip) => {
        const accent = chip.accent ?? "var(--accent-cyan)";
        const baseClass =
          "inline-flex items-center gap-1.5 px-2 py-0.5 text-[0.75rem] font-medium rounded-full border transition-colors duration-150";
        const stateClass = chip.active
          ? ""
          : "border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)]";
        return (
          <button
            key={chip.id}
            role="button"
            aria-pressed={chip.active}
            onClick={() => onChipToggle(chip.id)}
            className={`${baseClass} ${stateClass}`.trim()}
            style={
              chip.active
                ? { borderColor: accent, color: accent }
                : undefined
            }
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                backgroundColor: chip.active ? accent : "var(--text-muted)",
              }}
              aria-hidden="true"
            />
            {chip.label}
          </button>
        );
      })}
      <div className="relative w-64 ml-auto">
        <Search
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
          aria-hidden
        />
        <Input
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={searchPlaceholder ?? "Search..."}
          className="pl-8 h-8 text-[0.8125rem]"
        />
      </div>
    </div>
  );
}