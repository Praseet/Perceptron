// Phase 5 - chrome/app-shell.tsx
// Wraps every route with the persistent chrome (top nav, footer,
// command palette). The router in App.tsx renders <AppShell> as its
// outer element so the chrome persists across route changes rather
// than being re-rendered by each page.
//
// Children are rendered inside the main content area, with a max-width
// of var(--max-w-home) to keep line lengths readable on wide screens
// (the spec's locked width).

import { ReactNode } from "react";
import { TopNav } from "./top-nav";
import { Footer } from "./footer";
import { CommandPalette } from "./command-palette";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col bg-[var(--bg-base)] text-[var(--text-primary)]">
      <TopNav />
      <CommandPalette />
      <main
        id="main"
        role="main"
        className="flex-1 w-full max-w-[var(--max-w-home)] mx-auto px-6 py-8"
      >
        {children}
      </main>
      <Footer />
    </div>
  );
}