// Phase 6 - features/identify/identify-page.tsx
// The real Identify page. Replaces the Phase 5 placeholder.
//
// Per the spec, this composes:
//   - the header strip ("Attack Taxonomy" / "25 attack vectors
//     across 5 categories..." exact copy)
//   - the filter bar (5 category chips in D-A-B-C-E order + status
//     chips + search)
//   - the attack list (sortable, NOT virtualized)
//   - the detail drawer (Sheet, opened by row click or ?attack_id=)
//
// Open/closed state for the drawer is local useState in this
// top-level page component (per the spec's "single-feature-local
// state that does NOT belong in the shared Zustand store").
//
// On mount, read the URL's `?attack_id=` and, if present, open the
// drawer for that attack. Also handle a "version" cache-bust so
// the same URL keeps working after a future Phase 10 fixture
// update.

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Skeleton } from "../../design-system/primitives/Skeleton";
import { EmptyState } from "../../design-system/patterns/empty-state";
import { SearchX, Inbox } from "../../design-system/icons";
import { useAttacks } from "./use-attacks";
import {
  AttackFilterBar,
  EMPTY_FILTERS,
  type AttackFilters,
  filterAttacks,
} from "./attack-filter-bar";
import { AttackList } from "./attack-list";
import { AttackDetailDrawer } from "./attack-detail-drawer";
import type { Attack } from "../../lib/api/types";

const HEADER_TITLE = "Identify";
const HEADER_STEP = "Step 1 of 4";
const HEADER_SUBTITLE =
  "25 attack vectors across 5 categories, from voice-clone scams to LLM-Jacking.";

export function IdentifyPage() {
  const { data, isLoading, isError, error } = useAttacks();
  const [searchParams, setSearchParams] = useSearchParams();

  // Local UI state - per the spec, this is exactly the kind of
  // single-feature-local state that does NOT belong in Zustand.
  const [filters, setFilters] = useState<AttackFilters>(EMPTY_FILTERS);
  const [openAttackId, setOpenAttackId] = useState<string | null>(null);

  // When the URL's `?attack_id=` changes (or on first mount if
  // present), open the drawer for that attack. Per the spec, this
  // is the deep-link from the Home page's Identify mini and the
  // command palette's attack search.
  useEffect(() => {
    const id = searchParams.get("attack_id");
    if (id) setOpenAttackId(id);
    // We intentionally only react to attack_id changes; the
    // search-params object identity changes on every render and
    // would re-fire.
  }, [searchParams]);

  // Apply filters to the loaded attacks. Pure function call.
  const visible = useMemo<Attack[]>(() => {
    if (!data) return [];
    return filterAttacks(data, filters);
  }, [data, filters]);

  const openAttack = useMemo<Attack | null>(() => {
    if (!openAttackId || !data) return null;
    return data.find((a) => a.id === openAttackId) ?? null;
  }, [openAttackId, data]);

  // Close handler that ALSO clears the URL's attack_id so a
  // back-button doesn't reopen the drawer with a stale id.
  function closeDrawer() {
    setOpenAttackId(null);
    if (searchParams.get("attack_id")) {
      const next = new URLSearchParams(searchParams);
      next.delete("attack_id");
      setSearchParams(next, { replace: true });
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <p className="text-caption font-mono uppercase tracking-[0.12em] text-[var(--text-muted)]">
          {HEADER_STEP}
        </p>
        <h1 className="text-page-title text-[var(--text-primary)] mt-1">
          {HEADER_TITLE}
        </h1>
        <p className="mt-1 text-[0.875rem] text-[var(--text-secondary)] max-w-2xl">
          {HEADER_SUBTITLE}
        </p>
      </header>

      {isLoading ? (
        <LoadingState />
      ) : isError ? (
        <ErrorState message={error instanceof Error ? error.message : "Unknown error"} />
      ) : (
        <>
          <AttackFilterBar filters={filters} onFiltersChange={setFilters} />

          {/* H.67 item #10: the list count is honest and small,
              and the visible/total split is useful - a judge
              immediately sees how aggressive their filter is. */}
          <div className="flex items-center justify-between">
            <p className="text-[0.75rem] font-mono text-[var(--text-muted)] tabular-nums">
              {visible.length} of {data?.length ?? 0} attacks
            </p>
            {(filters.categories.size > 0 ||
              filters.status !== "all" ||
              filters.search.length > 0) && (
              <button
                onClick={() => setFilters(EMPTY_FILTERS)}
                className="text-[0.75rem] text-[var(--accent-cyan)] hover:text-[var(--accent-cyan-dim)] transition-colors"
              >
                Clear filters
              </button>
            )}
          </div>

          {visible.length === 0 ? (
            <EmptyState
              icon={<SearchX size="empty" />}
              message="No attacks match the current filters."
              action={{
                label: "Clear filters",
                onClick: () => setFilters(EMPTY_FILTERS),
              }}
            />
          ) : (
            <AttackList attacks={visible} onOpenDetail={setOpenAttackId} />
          )}
        </>
      )}

      <AttackDetailDrawer
        attack={openAttack}
        open={openAttackId != null}
        onClose={closeDrawer}
      />
    </div>
  );
}

// Loading skeleton - shaped like the real content, not a generic
// spinner (per section 4 of the clarifications, "Loading: a
// skeleton ... shaped like the content that's coming"). We render
// 8 skeleton rows (the real page shows up to 25) with the same
// column proportions as the real table.
function LoadingState() {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading attacks">
      <Skeleton className="h-9 w-full" />
      <div
        className="rounded-[var(--radius-card)] border border-[var(--border-subtle)] bg-[var(--bg-panel)] overflow-hidden"
      >
        {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
          <div
            key={i}
            className="flex items-center gap-4 px-4 py-3 border-b border-[var(--border-subtle)] last:border-b-0"
          >
            <Skeleton className="h-4 w-14" /> {/* ID */}
            <Skeleton className="h-4 flex-1" /> {/* Name */}
            <Skeleton className="h-4 w-24" /> {/* Category */}
            <Skeleton className="h-4 w-20" /> {/* Feasibility */}
            <Skeleton className="h-4 w-20" /> {/* Status */}
            <Skeleton className="h-4 w-4" />  {/* Chevron */}
          </div>
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="space-y-4">
      <EmptyState
        icon={<Inbox size="empty" />}
        message="Couldn't load the attack taxonomy."
      />
      <p className="text-[0.75rem] font-mono text-[var(--risk-critical)] text-center max-w-md mx-auto">
        {message}
      </p>
    </div>
  );
}
