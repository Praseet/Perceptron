// Phase 5+10.5 - features/home/home-page.tsx
// The Home page. Composes the hero, KPI row, merged pillar-preview
// section (now containing Identify/Generate/Defend live minis plus
// the Improve card that used to live in the separate
// ClosedLoopStages section - per Phase 10.5 §5.1), and
// numbers-that-hold-up. This is the page a judge lands on first -
// the entire product's job is to answer "is the closed loop real"
// within 5 seconds.
//
// The page also surfaces a "Cmd+K" hint in the chrome (rendered
// by the command palette's empty state on first open) - judges
// who notice the keyboard shortcut get a faster way to navigate.

import { Hero } from "./hero";
import { HeroKpiRow } from "./hero-kpi-row";
import { PillarPreviewCards } from "./pillar-preview-cards";
import { NumbersThatHoldUp } from "./numbers-that-hold-up";

export function HomePage() {
  return (
    <div className="space-y-12">
      <Hero />
      <HeroKpiRow />
      <PillarPreviewCards />
      <NumbersThatHoldUp />
    </div>
  );
}