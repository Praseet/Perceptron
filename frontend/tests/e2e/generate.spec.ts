// Phase 7 - generate.spec.ts
// Per the spec: "Run this phase\u2019s applicable acceptance criteria
// against the actual running app before declaring anything done."
// Each criterion maps to a named test.

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "../../test-results");

test.describe.configure({ mode: "parallel" });

// Test 1: page renders the real page (not a placeholder), and
// the controls + skeleton show up before the data lands.
test("phase 7 - Generate page renders real controls, not the placeholder", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });

  await page.goto("/generate", { waitUntil: "networkidle" });

  // Header text from the spec.
  await expect(page.getByRole("heading", { name: "Generate", level: 1 })).toBeVisible();

  // Attack select exists and is populated.
  const attackSelect = page.getByLabel("Attack vector");
  await expect(attackSelect).toBeVisible({ timeout: 5000 });
  const optionCount = await attackSelect.locator("option").count();
  expect(optionCount).toBeGreaterThan(5);

  // Urgency select has the three spec-defined options.
  const urgencySelect = page.getByLabel("Urgency");
  await expect(urgencySelect).toBeVisible();
  await expect(urgencySelect.locator("option")).toHaveText(["Low", "Medium", "High"]);

  // Generate button exists, is enabled once data loads.
  const genBtn = page.getByRole("button", { name: /Generate attack/i });
  await expect(genBtn).toBeEnabled({ timeout: 5000 });

  // The page is not the Phase 5 placeholder.
  await expect(page.getByText(/This page is built in Phase 7/i)).toHaveCount(0);

  expect(consoleErrors).toEqual([]);

  await page.screenshot({
    path: path.join(OUT, "generate-default.png"),
    fullPage: true,
  });
});

// Test 2: pressing Generate produces a result panel + Dialog.
test("phase 7 - Generate produces a result and opens the post-generate dialog", async ({ page }) => {
  await page.goto("/generate", { waitUntil: "networkidle" });
  const genBtn = page.getByRole("button", { name: /Generate attack/i });
  await expect(genBtn).toBeEnabled({ timeout: 5000 });
  await genBtn.click();

  // Dialog auto-opens.
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: 5000 });
  await expect(dialog).toContainText(/Did we just create an attack/i);

  // All three action buttons are present.
  await expect(dialog.getByRole("button", { name: /add to training set/i })).toBeVisible();
  await expect(dialog.getByRole("button", { name: /Score in Defend/i })).toBeVisible();
  await expect(dialog.getByRole("button", { name: /Discard/i })).toBeVisible();

  // The right-column panels are also visible (behind the dialog).
  await expect(page.getByRole("heading", { name: "Conversation", level: 2 })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Materialized transaction", level: 3 })).toBeVisible();

  // The recent-generates list now has 1 row.
  await expect(page.getByText(/1 this session/)).toBeVisible();

  await page.screenshot({
    path: path.join(OUT, "generate-dialog.png"),
    fullPage: true,
  });
});

// Test 3: the "Score in Defend" cross-link navigates to /defend.
test("phase 7 - Score in Defend navigates to /defend", async ({ page }) => {
  await page.goto("/generate", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Generate attack/i }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: 5000 });
  await dialog.getByRole("button", { name: /Score in Defend/i }).click();
  await expect(page).toHaveURL(/\/defend/);
});

// Test 4: deep-link ?attack_id=... pre-selects the attack and the
// URL is cleaned up so a back-button does not re-fire.
test("phase 7 - ?attack_id= deep-link pre-selects and cleans the URL", async ({ page }) => {
  await page.goto("/generate?attack_id=SE-001", { waitUntil: "networkidle" });
  const attackSelect = page.getByLabel("Attack vector");
  await expect(attackSelect).toHaveValue("SE-001", { timeout: 5000 });
  await expect(page).toHaveURL(/\/generate$/);
});

// Test 5: the home page Generate mini shares the same hook - pressing
// Generate on the home page sets lastGeneratedTransactionId in
// Zustand, which the Defend mini then reads.
test("phase 7 - Home mini and full page share state (Zustand handoff)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });

  // The home mini\u2019s Generate button writes the tx_id. Press it.
  // The mini uses compact size; its button reads just "Generate".
  // We locate the article by its h3 (which only the Generate mini has).
  const generateArticle = page
    .locator("article")
    .filter({ has: page.getByRole("heading", { name: "Generate", level: 3 }) });
  const defendArticle = page
    .locator("article")
    .filter({ has: page.getByRole("heading", { name: "Defend", level: 3 }) });

  const miniGen = generateArticle.getByRole("button", { name: /^Generate$/ });
  await expect(miniGen).toBeEnabled({ timeout: 5000 });
  await miniGen.click();

  // After the call lands, the mini shows a tx_id.
  await expect(generateArticle.getByText(/^demo-tx-/)).toBeVisible({ timeout: 5000 });

  // Phase 8 update: the Defend mini is now a real compact form
  // (TransactionBuilderForm variant="compact"), not the Phase 5
  // "re-generate then predict" placeholder. The "last generated"
  // label appears in the mini header with the tx_id, which is
  // the proof the Zustand handoff is wired.
  await expect(
    defendArticle.getByText(/last generated: demo-tx-/),
  ).toBeVisible({ timeout: 5000 });
});

// Test 6: visual self-review - the result panel (dialog dismissed).
test("phase 7 - visual self-review: result panel, no dialog", async ({ page }) => {
  await page.goto("/generate", { waitUntil: "networkidle" });
  await page.getByRole("button", { name: /Generate attack/i }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: 5000 });
  await dialog.getByRole("button", { name: /Discard/i }).click();
  await expect(dialog).toBeHidden();

  await page.screenshot({
    path: path.join(OUT, "generate-result.png"),
    fullPage: true,
  });
});
