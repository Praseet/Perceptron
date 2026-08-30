// Phase 9 - features/loop/run-history-table.tsx
// Per the Phase 9 spec step 6:
//   "RunHistoryTable - @tanstack/react-table bound Table
//    (Phase 2), columns: start time, duration, final PR-AUC,
//    cycles run, new attacks added, a 'View artifacts ->'
//    external link to whatever output-directory path the
//    API/demo fixture returns. Wire the EmptyState pattern
//    for 'no cycles run this session,' per 'Empty, Loading,
//    and Error States.'"
//
// The page prepends a new row from run_complete to the
// `recentRuns` prop, so this table is purely presentational:
// render what's in `rows`, or render EmptyState if `rows` is
// empty.

import { useMemo } from "react";
import {
  useTable,
  flexRender,
} from "@tanstack/react-table";
import { createCoreRowModel } from "@tanstack/table-core";

// @tanstack/react-table@9.2.4 is a transitional v9 release - its
// type signatures (ColumnDef<TFeatures, TData, TValue>) are
// significantly more complex than the v8 `useReactTable` shape the
// body of this file was written against (see the Phase 6
// PROGRESS.md entry on this same v9 deviation in
// features/identify/attack-list.tsx, which avoided the issue by
// hand-rolling local sort state). This file is purely
// presentational: no sorting, no filtering, no pagination - just
// `getRowModel().rows.map(...)`. We therefore type the columns
// locally with `any` and cast the useTable options to bridge the
// v9 API. Runtime behavior is unchanged.
import { Card, Table, Th, Td } from "../../design-system/primitives";
import { EmptyState } from "../../design-system/patterns/empty-state";
import { Inbox, ExternalLink } from "../../design-system/icons";
import { formatRelative, formatDuration } from "../../lib/format";
import type { LoopHistoryEntry } from "../../lib/api/types";

interface RunHistoryTableProps {
  rows: LoopHistoryEntry[];
}

function formatStart(iso: string): string {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function RunHistoryTable({ rows }: RunHistoryTableProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const columns = useMemo<any[]>(
    () => [
      {
        accessorKey: "started_at",
        header: "Start time",
        cell: (info: { getValue: () => unknown }) => (
          <span className="font-mono tabular-nums text-[var(--text-secondary)]">
            {formatStart(String(info.getValue()))}
            <span className="block text-[0.625rem] text-[var(--text-muted)]">
              {formatRelative(String(info.getValue()))}
            </span>
          </span>
        ),
      },
      {
        accessorKey: "duration_s",
        header: "Duration",
        cell: (info: { getValue: () => unknown }) => (
          <span className="font-mono tabular-nums text-[var(--text-primary)]">
            {formatDuration(Number(info.getValue()))}
          </span>
        ),
      },
      {
        accessorKey: "final_pr_auc",
        header: "Final PR-AUC",
        cell: (info: { getValue: () => unknown }) => (
          <span className="font-mono tabular-nums text-[var(--text-primary)]">
            {Number(info.getValue()).toFixed(4)}
          </span>
        ),
      },
      {
        accessorKey: "n_cycles",
        header: "Cycles",
        cell: (info: { getValue: () => unknown }) => (
          <span className="font-mono tabular-nums text-[var(--text-secondary)]">
            {String(info.getValue())}
          </span>
        ),
      },
      {
        accessorKey: "n_new_attacks",
        header: "New attacks",
        cell: (info: { getValue: () => unknown }) => (
          <span className="font-mono tabular-nums text-[var(--text-secondary)]">
            {String(info.getValue())}
          </span>
        ),
      },
      {
        id: "artifacts",
        header: "Artifacts",
        cell: (info: { row: { original: LoopHistoryEntry } }) => {
          const url = info.row.original.artifact_url;
          if (!url) {
            return (
              <span className="text-[0.625rem] font-mono text-[var(--text-muted)]">
                -
              </span>
            );
          }
          return (
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[0.75rem] text-[var(--accent-cyan)] hover:text-[var(--accent-cyan-dim)] transition-colors"
            >
              View artifacts
              <ExternalLink aria-hidden size="inline" />
            </a>
          );
        },
      },
    ],
    [],
  );

  const table = useTable({
    data: rows,
    columns,
    createCoreRowModel: createCoreRowModel(),
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } as any);

  if (rows.length === 0) {
    return (
      <EmptyState
        icon={<Inbox size="empty" />}
        message="No cycles run this session. Click Run on the controls to start a closed-loop pass; each completed run will appear here."
      />
    );
  }

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[0.875rem] font-semibold text-[var(--text-primary)]">
          Run history
        </h3>
        <span className="text-[0.625rem] font-mono text-[var(--text-muted)] tabular-nums">
          {rows.length} run{rows.length === 1 ? "" : "s"}
        </span>
      </div>
      <div
        className="overflow-x-auto"
        tabIndex={0}
        role="region"
        aria-label="Run history table (scrollable horizontally)"
      >
        <Table size="compact">
          <thead>
            <tr>
              {table.getHeaderGroups()[0].headers.map((header) => (
                <Th key={header.id}>
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </Th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-b border-[var(--border-subtle)] last:border-b-0">
                {row.getAllCells().map((cell) => (
                  <Td key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </Td>
                ))}
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </Card>
  );
}
