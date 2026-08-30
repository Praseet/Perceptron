// Phase 5 - App.tsx
// Router only, no page content. Per "Folder and File Structure" the
// App.tsx is the router; every page lives in src/features/<page>.
// Five React.lazy-loaded routes using the route-path constants from
// lib/constants.ts.

import { lazy, Suspense } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./chrome/app-shell";
import { ROUTES } from "./lib/constants";

const HomePage = lazy(() => import("./features/home/home-page").then((m) => ({ default: m.HomePage })));
const IdentifyPage = lazy(() => import("./features/identify/identify-page").then((m) => ({ default: m.IdentifyPage })));
const GeneratePage = lazy(() => import("./features/generate/generate-page").then((m) => ({ default: m.GeneratePage })));
const DefendPage = lazy(() => import("./features/defend/defend-page").then((m) => ({ default: m.DefendPage })));
const LoopPage = lazy(() => import("./features/loop/loop-page").then((m) => ({ default: m.LoopPage })));

function PageFallback() {
  return (
    <div className="min-h-[40vh] flex items-center justify-center">
      <p className="text-[0.8125rem] text-[var(--text-muted)] font-mono">loading...</p>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            <Route path={ROUTES.home} element={<HomePage />} />
            <Route path={ROUTES.identify} element={<IdentifyPage />} />
            <Route path={ROUTES.generate} element={<GeneratePage />} />
            <Route path={ROUTES.defend} element={<DefendPage />} />
            <Route path={ROUTES.loop} element={<LoopPage />} />
            <Route path="*" element={<HomePage />} />
          </Routes>
        </Suspense>
      </AppShell>
    </BrowserRouter>
  );
}

export default App;
