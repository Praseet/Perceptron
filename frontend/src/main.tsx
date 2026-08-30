// Phase 5 - main.tsx
// Wraps the app in QueryClientProvider (TanStack Query) so the
// chrome's SystemStatusPill, the Home page's KPI row, and every
// future page's data hooks share the same cache.
//
// staleTime: 30s per the Phase 5 spec. refetchOnWindowFocus: false
// (a judge scrolling the page, clicking into a tab and back, or
// moving the mouse is not a meaningful refetch trigger).

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";
import App from "./App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
);
