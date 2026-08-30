// Phase 10 step 7 - cross-browser smoke.
//
// Per the spec: "Run the full spec suite (npx playwright test)
// across all three configured browser projects. Chromium passing
// and Firefox/WebKit failing is common specifically around SVG
// rendering (ReactFlow, Recharts) and backdrop-filter /
// custom-property fallback behavior. If either non-Chromium
// browser fails, diagnose whether it's a real rendering bug
// (fix it) or a test-authoring issue (a selector too
// Chromium-specific, a timing race - fix the test)."
//
// The spec explicitly says: "Do not mark a real cross-browser
// rendering bug as 'known issue, ship anyway' without explicitly
// recording that decision and its reasoning in PROGRESS.md".
//
// This smoke runs the smallest verification that touches each
// cross-browser surface area:
//   - SVG / ReactFlow (LoopDiagram) on Home + Loop
//   - Recharts (PR curve) on Defend
//   - Lucide icons (every page)
//   - prefers-reduced-motion and CSS custom properties

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { trackConsoleErrors, screenshotNameFor } from "./_smoke-helpers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "screenshots");

test.describe.configure({ mode: "serial" });

const ROUTES: Array<{ path: string; name: string; feature: string }> = [
  { path: "/", name: "home", feature: "ReactFlow (LoopDiagram)" },
  { path: "/identify", name: "identify", feature: "SVG icons (Lucide)" },
  { path: "/generate", name: "generate", feature: "custom-prop tokens" },
  { path: "/defend", name: "defend", feature: "Recharts (PR curve)" },
  { path: "/loop", name: "loop", feature: "ReactFlow + custom-prop tokens" },
];

for (const route of ROUTES) {
  test(`cross-browser - ${route.name} renders cleanly on this browser`, async ({
    page,
  }, testInfo) => {
    const tracker = trackConsoleErrors(page);
    await page.goto(route.path, { waitUntil: "networkidle" });

    if (route.path === "/" || route.path === "/loop") {
      await page.waitForTimeout(2800);
    }

    // Page-level H1 must render (cross-browser sanity).
    await expect(page.locator("h1").first()).toBeVisible();

    // The LoopDiagram on Home/Loop must render in Firefox and WebKit
    // too (SVG support varies). The Home page's hero hides the
    // diagram below the `lg` breakpoint (390px mobile viewport),
    // but the Loop page always renders its diagram.
    if (route.path === "/loop") {
      const diagram = page.locator(
        '[aria-label="Closed loop diagram: Identify, Generate, Defend, Improve"]',
      );
      await expect(diagram.first()).toBeVisible();
      // All 4 leg nodes must render (data-leg="identify|generate|defend|improve").
      for (const leg of ["identify", "generate", "defend", "improve"]) {
        await expect(
          page.locator(`[data-leg="${leg}"]`).first(),
        ).toBeVisible();
      }
    }

    // Recharts SVG on Defend.
    if (route.path === "/defend") {
      // Recharts uses inline SVG for the line chart.
      const svgCount = await page.locator("svg.recharts-surface").count();
      expect(svgCount).toBeGreaterThan(0);
    }

    // CSS custom properties must resolve (Firefox/WebKit both
    // support them, but confirm the resolved values look right).
    const bgBase = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--bg-base").trim(),
    );
    expect(bgBase).not.toBe("");

    await page.screenshot({
      path: path.join(OUT, screenshotNameFor(testInfo)),
      fullPage: true,
    });

    tracker.assertClean();
  });
}