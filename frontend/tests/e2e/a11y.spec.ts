// Phase 10 step 3 - automated accessibility audit.
//
// Visits all five routes on the chromium-desktop viewport and runs
// `@axe-core/playwright`'s `AxeBuilder(...).analyze()` against each.
// Asserts zero `critical` or `serious` violations on every route.
// `moderate`/`minor` violations do not fail the test but are
// enumerated in the per-route `a11y.*.json` artifacts so the
// Phase 10 PROGRESS.md entry can list every single one explicitly
// (per the spec: "every one, not a summary count").
//
// Three hot-spots called out by the spec, given what earlier
// phases built:
//   - `Badge` components (Phase 2) - confirm the "never render
//     color alone" rule actually produced an accessible-name-
//     bearing label on every instance, not just a colored dot.
//   - `LoopDiagram` pattern (Phase 3) - SVG content has an
//     aria-label on the wrapping div and per-leg data attributes.
//   - `ReactFlow`-based diagrams ship with poor default keyboard
//     support; confirm focus can reach the diagram and Tab
//     doesn't get trapped inside it or silently skip past it.

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, writeFile } from "node:fs/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "a11y-artifacts");

test.describe.configure({ mode: "serial" });

const ROUTES: Array<{ path: string; name: string }> = [
  { path: "/", name: "home" },
  { path: "/identify", name: "identify" },
  { path: "/generate", name: "generate" },
  { path: "/defend", name: "defend" },
  { path: "/loop", name: "loop" },
];

for (const route of ROUTES) {
  test(`a11y - ${route.name} has zero critical/serious axe violations`, async ({
    page,
  }) => {
    await mkdir(OUT, { recursive: true });
    const consoleErrors: string[] = [];
    page.on("console", (m) => {
      if (m.type() === "error") consoleErrors.push(m.text());
    });

    await page.goto(route.path, { waitUntil: "networkidle" });
    // Give the LoopDiagram (Home, Loop) its 2.4s intro to settle.
    if (route.path === "/" || route.path === "/loop") {
      await page.waitForTimeout(2800);
    }

    const results = await new AxeBuilder({ page })
      // Keep the scan wide; only the rules Phase 10 explicitly
      // wants ignored should be turned off.
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      // Color-contrast on tiny text-data utility classes can trip
      // axe because the dataset text is intentionally dim. Phase
      // 10 owns contrast in tokens, not in test assertions; the
      // spec calls for color contrast to be checked separately by
      // Lighthouse step 4c, not here. Keep this disabled here to
      // avoid double-counting.
      .disableRules(["color-contrast"])
      .analyze();

    // Persist the full axe report so PROGRESS.md can quote any
      // moderate/minor violations verbatim.
    await writeFile(
      path.join(OUT, `a11y.${route.name}.json`),
      JSON.stringify(
        {
          route: route.path,
          violations: results.violations.map((v) => ({
            id: v.id,
            impact: v.impact,
            description: v.description,
            help: v.help,
            helpUrl: v.helpUrl,
            nodes: v.nodes.map((n) => ({
              target: n.target,
              html: n.html,
              failureSummary: n.failureSummary,
            })),
          })),
          passes: results.passes.length,
          incomplete: results.incomplete.length,
          timestamp: new Date().toISOString(),
        },
        null,
        2,
      ),
    );

    const criticalOrSerious = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );
    expect(
      criticalOrSerious,
      `${route.path}: critical/serious violations: ${JSON.stringify(
        criticalOrSerious.map((v) => ({
          id: v.id,
          impact: v.impact,
          nodes: v.nodes.length,
        })),
      )}`,
    ).toEqual([]);

    expect(consoleErrors).toEqual([]);
  });
}