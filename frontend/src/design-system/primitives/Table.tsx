import type { HTMLAttributes, ReactNode, ThHTMLAttributes, TdHTMLAttributes } from "react";
import { cn } from "./cn";

// H.2.1: built on plain <table> with @tanstack/react-table installed
// for later phases to compose on top. `compact` / `default` row-density
// variants. Sortable column headers via the optional `onSort` prop on
// <Th>.
type TableSize = "default" | "compact";

interface TableProps extends HTMLAttributes<HTMLTableElement> {
  size?: TableSize;
  children: ReactNode;
}

export function Table({ size = "default", className, children, ...rest }: TableProps) {
  return (
    <table
      className={cn("w-full border-collapse", className)}
      {...rest}
    >
      {children}
    </table>
  );
}

export function Th({
  className,
  children,
  sortDirection,
  onSort,
  ...rest
}: ThHTMLAttributes<HTMLTableCellElement> & {
  sortDirection?: "asc" | "desc" | null;
  onSort?: () => void;
}) {
  const sortable = !!onSort;
  return (
    <th
      className={cn(
        "text-left",
        "text-[0.75rem] font-semibold uppercase tracking-wider",
        "text-[var(--text-muted)]",
        "border-b border-[var(--border-subtle)]",
        sortable && "cursor-pointer select-none hover:text-[var(--text-primary)]",
        className,
      )}
      onClick={onSort}
      {...rest}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        {sortable && (
          <span aria-hidden="true" className="text-[var(--accent-cyan)]">
            {sortDirection === "asc" ? "\u25B2" : sortDirection === "desc" ? "\u25BC" : "\u21F5"}
          </span>
        )}
      </span>
    </th>
  );
}

export function Td({ className, children, ...rest }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td
      className={cn(
        "text-[0.875rem] text-[var(--text-primary)]",
        "border-b border-[var(--border-subtle)]",
        className,
      )}
      {...rest}
    >
      {children}
    </td>
  );
}

export function Tr({ className, children, ...rest }: HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        "transition-colors duration-150",
        "hover:bg-[var(--bg-elevated)]",
        className,
      )}
      {...rest}
    >
      {children}
    </tr>
  );
}

// Convenience density helpers.
export const tableCellDensity = {
  default: "px-4 py-3",
  compact: "px-3 py-2",
} as const;

export type { TableSize };