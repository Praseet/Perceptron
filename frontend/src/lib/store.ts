// Phase 4 + 7 + 8 - lib/store.ts
// The one Zustand store.
//
// Phase 4 spec: exactly three fields
//   - commandPaletteOpen / setCommandPaletteOpen
//   - dataSource / setDataSource
//   - lastGeneratedTransactionId / setLastGeneratedTransactionId
// Per the spec's "if you find yourself wanting to add a fifth field,
// put it in that feature's own local state instead."
//
// Phase 8 deviation: a fourth field `lastGeneratedTransaction`
// (a `TransactionRowWithId | null`) is added as a deliberate,
// reasoned exception to the Phase 4 guidance. The spec for
// Phase 8 explicitly permits this:
//   "if you take this approach, extend `useAppStore` with
//    exactly one more field, `lastGeneratedTransaction:
//    TransactionRow | null`, and say explicitly in `PROGRESS.md`
//    that you're doing this as a deliberate, reasoned exception
//    to Phase 4's 'don't add a fifth field' guidance, because
//    this is precisely the 'two pages don't import each other,
//    they share state through the store' mechanism the folder
//    rules exist to enable"
// The ID field stays (the Defend page's "Load a transaction I
// just generated" link uses it as the predicate for visibility),
// and the full transaction lets Defend pre-fill all 23 fields
// without needing a getTransactionById endpoint that doesn't
// exist yet.

import { create } from "zustand";
import type { GenerateResult, TransactionRowWithId } from "./api/types";

export type DataSource = "demo" | "live";

interface AppState {
  // Command palette visibility (Phase 5 chrome)
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => void;

  // Which API client implementation to use (Phase 4 getApiClient)
  dataSource: DataSource;
  setDataSource: (src: DataSource) => void;

  // Last successfully generated transaction (Phase 7 -> Phase 8 handoff)
  lastGeneratedTransactionId: string | null;
  setLastGeneratedTransactionId: (id: string | null) => void;

  // Phase 8 deviation - the full transaction object. See the file
  // header for why this exists despite Phase 4's 3-field rule.
  lastGeneratedTransaction: TransactionRowWithId | null;
  setLastGeneratedTransaction: (tx: TransactionRowWithId | null) => void;

  // Phase 10.5 deviation - the full GenerateResult produced by the
  // Home page's Generate mini, so that clicking "See all" actually
  // restores the same result on the full Generate page rather than
  // resetting to its empty state. This is the same "two pages don't
  // import each other, they share state through the store"
  // mechanism Phase 8 explicitly carved out for the Generate->Defend
  // handoff. The full Generate page reads this on mount (via lazy
  // initial state in `selected`) so its default empty-state behavior
  // when arriving with no prior context is unchanged - if the user
  // navigates directly to /generate without going through the Home
  // mini, this field is null and the page shows its normal empty
  // state. See §5.3 in the refactor doc.
  lastHomeGenerateResult: GenerateResult | null;
  setLastHomeGenerateResult: (r: GenerateResult | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  commandPaletteOpen: false,
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

  dataSource: "demo", // VITE_DEMO_MODE=true is the committed default
  setDataSource: (src) => set({ dataSource: src }),

  lastGeneratedTransactionId: null,
  setLastGeneratedTransactionId: (id) =>
    set({ lastGeneratedTransactionId: id }),

  lastGeneratedTransaction: null,
  setLastGeneratedTransaction: (tx) => set({ lastGeneratedTransaction: tx }),

  lastHomeGenerateResult: null,
  setLastHomeGenerateResult: (r) => set({ lastHomeGenerateResult: r }),
}));