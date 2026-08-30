// Phase 10 step 2 - identify smoke spec.
// Navigates to "/identify", asserts the page header, captures
// console errors, exercises the category-filter chip interaction
// (per the Phase 10 spec), and saves a full-page screenshot.
//
// The Identify page renders a 25-row attack taxonomy with a filter
// bar at the top (5 category chips + a search input). Clicking a
// category chip narrows the table to that category.
//
// The existing tests/e2e/identify.spec.ts already covers this page's
// functionality exhaustively. This is the dedicated Phase 10 smoke
// spec: same assertions, but with Phase 10's required console-error
// tracking and screenshot-at-tests/e2e/screenshots/ pattern.

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { trackConsoleErrors, screenshotNameFor } from "./_smoke-helpers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "screenshots");

test("identify page renders, category chip narrows table, no console errors", async ({ page }, testInfo) => {
  const tracker = trackConsoleErrors(page);
  await page.goto("/identify", { waitUntil: "networkidle" });

  // Header (exact copy from src/features/identify/identify-page.tsx).
  // Phase 10.5 §5.8: the page's top-level h1 changed from
  // "Attack Taxonomy" to "Identify" to match every other feature
  // page's single-word leg-name pattern. The h1 still exists at
  // level 1; only the visible text changed.
  await expect(
    page.getByRole("heading", { level: 1, name: "Identify" }),
  ).toBeVisible();

  // All 25 attacks load (per Phase 6 acceptance criteria).
  await expect(page.locator("tbody tr")).toHaveCount(25);

  // Interaction per Phase 10 spec: "Identify — the taxonomy table
  // filters when a category chip is clicked."
  const chipA = page.getByRole("button", { name: /A - Social Eng\./ }).first();
  await expect(chipA).toBeVisible();
  await chipA.click();

  // After clicking the chip, the table should be filtered. We assert
  // a count of fewer than 25.
  await expect(page.locator("tbody tr")).not.toHaveCount(25);

  // Reset filter so the screenshot shows the full table. The category
  // chip is a toggle (click again to deactivate); the "All" chip
  // only resets the status filter, not the category filter.
  await chipA.click();
  await expect(page.locator("tbody tr")).toHaveCount(25);

  await page.screenshot({
    path: path.join(OUT, screenshotNameFor(testInfo)),
    fullPage: true,
  });

  tracker.assertClean();
});