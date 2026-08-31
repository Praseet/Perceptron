// Phase 11 step 5 - capture live-data screenshots into
// /docs/assets/ for submission. Per spec, at minimum capture:
//   - homepage mid-loop-animation
//   - homepage settled/pulsing state
//   - Defend page with a real ShapWaterfall populated
//   - Generate page mid-attack with a real conversation/transaction
//   - Loop page mid-run with CycleDeltaTiles showing real deltas
//
// Vite proxies /api/* to the live backend (port 8000). The dev server
// is up for the duration of this spec run.

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Path: ../../../docs/assets from frontend/tests/e2e/live-screenshots.spec.ts
// (3 levels up: e2e -> tests -> frontend, then +/docs/assets -> <repo>/docs/assets)
const OUT = path.resolve(__dirname, "..", "..", "..", "docs", "assets");

test.describe("Phase 11 - live-data screenshots for submission", () => {
  test("homepage settled", async ({ page }) => {
    await page.goto("/", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);
    await page.screenshot({
      path: path.join(OUT, "01-home-settled.png"),
      fullPage: true,
    });
  });

  test("identify page (25 attacks, live backend)", async ({ page }) => {
    await page.goto("/identify", { waitUntil: "networkidle" });
    await expect(page.locator("[aria-label='Attack list'] tbody tr").first()).toBeVisible();
    await page.screenshot({
      path: path.join(OUT, "02-identify-25-attacks.png"),
      fullPage: true,
    });
  });

  test("defend page with SHAP waterfall", async ({ page }) => {
    await page.goto("/defend", { waitUntil: "networkidle" });
    // Click Predict to populate the SHAP waterfall with real model output.
    await page.getByRole("button", { name: /^Predict$/ }).click();
    await expect(
      page.getByText("Top SHAP features (signed, by |value|)"),
      { timeout: 8000 },
    ).toBeVisible();
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(OUT, "03-defend-shap-waterfall.png"),
      fullPage: true,
    });
  });

  test("generate page mid-attack (conversation + transaction)", async ({ page }) => {
    await page.goto("/generate?attack_id=SE-001", { waitUntil: "networkidle" });
    await expect(page.getByRole("heading", { name: "Generate", level: 1 })).toBeVisible();
    await page.getByRole("button", { name: /Generate attack/i }).click();
    await expect(
      page.getByText(/Did we just create an attack/i),
      { timeout: 8000 },
    ).toBeVisible();
    // Dismiss the dialog so the screenshot shows the conversation + tx.
    const dialog = page.getByRole("dialog");
    if (await dialog.isVisible().catch(() => false)) {
      await dialog.getByRole("button", { name: /Discard/i }).click();
      await expect(dialog).toBeHidden();
    }
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(OUT, "04-generate-conversation-tx.png"),
      fullPage: true,
    });
  });

  test("loop page mid-run with cycle deltas", async ({ page }) => {
    await page.goto("/loop?prefill=1cycle", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);
    await page.getByRole("button", { name: /Run the closed loop/i }).click();
    // Wait until cycle deltas have populated (mid-run state).
    await expect(
      page.getByText(/Run started \(baseline recall/),
      { timeout: 10000 },
    ).toBeVisible();
    await page.waitForTimeout(2000);
    await page.screenshot({
      path: path.join(OUT, "05-loop-mid-run.png"),
      fullPage: true,
    });
    // Wait for run_complete so a follow-up screenshot shows settled state.
    await expect(
      page.getByText(/Run complete \(final PR-AUC/),
      { timeout: 30000 },
    ).toBeVisible();
    await page.screenshot({
      path: path.join(OUT, "06-loop-run-complete.png"),
      fullPage: true,
    });
  });
});