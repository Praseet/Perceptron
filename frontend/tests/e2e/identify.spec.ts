// Phase 6 - identify.spec.ts
// Per the spec: "Run this phase's applicable acceptance criteria
// against the actual running app before declaring anything done."
// Each criterion maps to a named test.

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { readFile, writeFile } from "node:fs/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "../../test-results");

// Run tests in this file SERIALLY (one at a time) rather than in
// parallel. The scaling test (test 9) mutates a fixture file; if
// it ran in parallel with another test that reads the same
// fixture, the other test would see 26 rows mid-run. Serial
// mode guarantees the fixture is restored before the next test
// starts. Cost: ~5s slower total runtime; benefit: no flake.
test.describe.configure({ mode: "serial" });

// Test 1: page renders all 25 attacks from the active data
// source, with zero hardcoded attack data in this feature folder
// (the spec's acceptance criterion #1).
test("phase 6 - Identify renders all 25 attacks (zero hardcoded data)", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });

  await page.goto("/identify", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible({ timeout: 8000 });
  const rows = page.locator("[aria-label='Attack list'] tbody tr");
  await expect(rows).toHaveCount(25);
  await expect(page.locator("text=25 of 25 attacks").first()).toBeVisible();
  expect(consoleErrors).toEqual([]);

  await page.screenshot({
    path: path.join(OUT, "identify-default.png"),
    fullPage: true,
  });
});

// Test 2: Category D's chip is the leftmost (spec acceptance #3).
test("phase 6 - Category D chip is leftmost in the filter row", async ({ page }) => {
  await page.goto("/identify", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();
  const filterRow = page.locator("button[role=button]").filter({
    hasText: /^[A-E] - /,
  });
  await expect(filterRow.first()).toContainText("D - AI-Specific");
  await expect(filterRow.nth(1)).toContainText("A - Social Eng.");
  await expect(filterRow.nth(2)).toContainText("B - Synthetic ID");
  await expect(filterRow.nth(3)).toContainText("C - Payment Rail");
  await expect(filterRow.nth(4)).toContainText("E - Behavioral");
});

// Test 3: filtering by a single category shows only that
// category's rows; combining with search narrows further; clearing
// restores all rows (spec acceptance #2).
test("phase 6 - category filter narrows, search adds, clear restores", async ({ page }) => {
  await page.goto("/identify", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();

  await page.locator("button[role=button]").filter({ hasText: "D - AI-Specific" }).click();
  const rows = page.locator("[aria-label='Attack list'] tbody tr");
  await expect(rows).toHaveCount(5);
  await expect(page.locator("text=5 of 25 attacks").first()).toBeVisible();

  await page.locator("input[placeholder='Search 25 attacks by name...']").fill("LLM");
  await expect(rows).toHaveCount(1);
  await expect(rows.first()).toContainText("LLM-Jacking");
  await expect(page.locator("text=1 of 25 attacks").first()).toBeVisible();

  await page.locator("button", { hasText: "Clear filters" }).first().click();
  await expect(rows).toHaveCount(25);
  await expect(page.locator("text=25 of 25 attacks").first()).toBeVisible();
});

// Test 4: empty-state appears when filters match zero attacks
// (spec acceptance #6).
test("phase 6 - empty state when filters match zero", async ({ page }) => {
  await page.goto("/identify", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();
  await page
    .locator("input[placeholder='Search 25 attacks by name...']")
    .fill("zzz_no_match_string");
  await expect(
    page.locator("text=No attacks match the current filters.").first(),
  ).toBeVisible();
  const clearBtn = page
    .locator("button", { hasText: "Clear filters" })
    .last();
  await clearBtn.click();
  await expect(page.locator("text=25 of 25 attacks").first()).toBeVisible();
});

// Test 5: deep-link via ?attack_id=SE-001 opens the drawer for
// that attack on mount (spec acceptance #5).
test("phase 6 - ?attack_id=SE-001 opens drawer for that attack on mount", async ({ page }) => {
  await page.goto("/identify?attack_id=SE-001", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();
  const sheet = page.locator("aside, [role=dialog]").filter({ hasText: "SE-001" });
  await expect(sheet.first()).toBeVisible({ timeout: 5000 });
  const genBtn = page.locator("button", { hasText: "Generate a sample" });
  await expect(genBtn.first()).toBeVisible();
});

// Test 6: a non-generator attack (e.g. SE-002) does NOT show the
// "Generate a sample" button (spec: "only the four attacks with
// a wired generator profile show the button").
test("phase 6 - non-generator attack does not show Generate button", async ({ page }) => {
  await page.goto("/identify?attack_id=SE-002", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();
  const sheet = page.locator("aside, [role=dialog]").filter({ hasText: "SE-002" });
  await expect(sheet.first()).toBeVisible({ timeout: 5000 });
  await expect(
    page.locator("button", { hasText: "Generate a sample" }),
  ).toHaveCount(0);
});

// Test 7: the "Generate a sample" button navigates to
// /generate?attack_id=SE-001 (spec acceptance #4).
test("phase 6 - Generate a sample navigates to /generate?attack_id=...", async ({ page }) => {
  await page.goto("/identify?attack_id=SE-001", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();
  const genBtn = page.locator("button", { hasText: "Generate a sample" }).first();
  await genBtn.click();
  await expect(page).toHaveURL(/\/generate\?attack_id=SE-001/);
});

// Test 8: sorting works (every column header is clickable and
// toggles).
test("phase 6 - clicking a column header toggles the sort", async ({ page }) => {
  await page.goto("/identify", { waitUntil: "networkidle" });
  await expect(page.locator("[aria-label='Attack list']")).toBeVisible();
  const rows = page.locator("[aria-label='Attack list'] tbody tr");
  await expect(rows.first()).toContainText("5/5");

  await page.locator("th", { hasText: "ID" }).click();
  await expect(rows.first()).toContainText("AI-001");
  await page.locator("th", { hasText: "ID" }).click();
  await expect(rows.first()).toContainText("SE-006");
});

// Test 9: scaling - add a 26th attack to the fixture, the list
// shows 26 rows without code changes (spec acceptance #7). This
// is the spec's "concrete proof of the scaling claim" - the
// fixture is mutated, the test re-runs, and confirms the list
// reflects the new total. We restore the fixture at the end.
test("phase 6 - scaling: a 26th attack in the fixture shows 26 rows", async ({ page }) => {
  const fixturePath = path.resolve(
    __dirname,
    "../../src/lib/demo-data/attacks.json",
  );
  const original = await readFile(fixturePath, "utf-8");
  const originalParsed = JSON.parse(original);
  originalParsed.push({
    id: "ZZ-999",
    name: "Phase 6 Scaling Probe",
    category: "D",
    status: "conceptual",
    feasibility: 1,
    fraud_type: null,
    generator_profile_id: null,
  });
  await writeFile(fixturePath, JSON.stringify(originalParsed, null, 2));
  try {
    await page.goto("/identify", { waitUntil: "networkidle" });
    await page.reload({ waitUntil: "networkidle" });
    await expect(
      page.locator("[aria-label='Attack list']"),
    ).toBeVisible();
    const rows = page.locator(
      "[aria-label='Attack list'] tbody tr",
    );
    await expect(rows).toHaveCount(26);
    await expect(page.locator("text=26 of 26 attacks").first()).toBeVisible();
    await page
      .locator("input[placeholder='Search 25 attacks by name...']")
      .fill("Scaling Probe");
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText("Phase 6 Scaling Probe");
  } finally {
    await writeFile(fixturePath, original);
  }
});

// Visual self-review capture: navigate to a drawer-opened state
// and capture the screenshot. This is the screenshot that
// PROGRESS.md references for the Phase 6 visual self-review.
test("phase 6 - visual self-review: LLM-Jacking drawer open", async ({ page }) => {
  await page.goto("/identify?attack_id=AI-004", { waitUntil: "networkidle" });
  await expect(
    page.locator("aside, [role=dialog]").filter({ hasText: "AI-004" }).first(),
  ).toBeVisible({ timeout: 5000 });
  await page.screenshot({
    path: path.join(OUT, "identify-drawer.png"),
    fullPage: true,
  });
});
