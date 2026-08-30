// Phase 10.5 §6 - new Playwright coverage for the page-differentiation
// refactor's two specific behavioral changes that the existing Phase
// 5/7/8 spec files do not cover:
//   1. The Home Defend mini renders exactly 3 fields (amount, hour_of_day,
//      channel) - not 7 - per Phase 5's original locked spec, restored by
//      Phase 10.5 §5.2.
//   2. Generating on the Home Generate mini, then clicking "See all,"
//      shows the same result on /generate rather than an empty state -
//      the continuity bug closed by Phase 10.5 §5.3.
//
// These tests exist alongside (not in place of) the existing phase
// spec files. They run against the dev server in demo mode.

import { test, expect } from "@playwright/test";

test.describe.configure({ mode: "serial" });

test("phase 10.5 - Home Defend mini shows exactly 3 fields (amount, hour_of_day, channel)", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });

  // The Defend mini lives inside the "See it work" merged section
  // (per Phase 10.5 §5.1), inside an <article> whose header contains
  // the text "Defend".
  const defendMini = page.locator("article", { hasText: "Defend" }).first();
  await expect(defendMini).toBeVisible();

  // The 3 fields that should be visible in compact (mini) mode:
  // amount, hour_of_day, channel.
  await expect(defendMini.getByLabel("Amount")).toBeVisible();
  await expect(defendMini.getByLabel("Hour of day")).toBeVisible();
  await expect(defendMini.getByLabel("Channel")).toBeVisible();

  // The 4 fields that should be HIDDEN in compact mode (only on
  // the full /defend page):
  await expect(defendMini.getByLabel("New device")).toHaveCount(0);
  await expect(defendMini.getByLabel("tx last 1hr")).toHaveCount(0);
  await expect(defendMini.getByLabel("device trust age (days)")).toHaveCount(0);
  await expect(defendMini.getByLabel("count 30d")).toHaveCount(0);

  // The mini has the full Predict button (still labelled "Predict",
  // not "Predict →" - that's the full-page label).
  await expect(defendMini.getByRole("button", { name: "Predict" })).toBeVisible();
});

test("phase 10.5 - Full Defend page still renders all 7 primary fields plus advanced disclosure", async ({ page }) => {
  await page.goto("/defend", { waitUntil: "networkidle" });

  // The full page renders all 7 primary fields (no compact-mode
  // hiding). The 4 hidden-in-mini fields should all be present.
  await expect(page.getByLabel("Amount")).toBeVisible();
  await expect(page.getByLabel("Hour of day")).toBeVisible();
  await expect(page.getByLabel("Channel")).toBeVisible();
  await expect(page.getByLabel("New device")).toBeVisible();
  await expect(page.getByLabel("tx last 1hr")).toBeVisible();
  await expect(page.getByLabel("device trust age (days)")).toBeVisible();
  await expect(page.getByLabel("count 30d")).toBeVisible();

  // The full page exposes the "Advanced fields (using dataset
  // medians) - click to inspect" disclosure.
  await expect(
    page.getByRole("button", { name: /Advanced fields/i }),
  ).toBeVisible();
});

test("phase 10.5 - Generate on Home mini, click See all, same result on /generate", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });

  // The Generate mini lives in the merged section (Phase 10.5 §5.1).
  const generateMini = page.locator("article", { hasText: "Generate" }).first();
  await expect(generateMini).toBeVisible();

  // Click the mini's Generate button. The mini's button has
  // aria-label "Generate attack" (when the variant is "compact",
  // per GenerateControls.tsx line 162). The demo's runLoop
  // compresses to a few seconds.
  await generateMini.getByRole("button", { name: /Generate attack|Generate/ }).click();

  // Wait for the mini to show a transaction_id chip below the form
  // (per the current GenerateMini layout: "<p>...transaction_id</p>"
  // when controls.result is non-null).
  await expect(generateMini.locator("p.text-\\[0\\.625rem\\]")).toBeVisible({ timeout: 10000 });

  // Capture the transaction_id text from the mini for later comparison.
  const miniTxId = await generateMini.locator("p.text-\\[0\\.625rem\\]").first().innerText();
  expect(miniTxId).toMatch(/.+/);

  // Click "See all" - this navigates to /generate.
  await generateMini.getByRole("button", { name: "See all" }).click();

  // We should land on /generate.
  await page.waitForURL(/\/generate/);
  await expect(page.getByRole("heading", { level: 1, name: "Generate" })).toBeVisible();

  // Wait for the page to render the carried-forward result: a
  // Conversation heading inside a Card.
  await expect(
    page.getByRole("heading", { name: /Conversation/i }),
  ).toBeVisible({ timeout: 10000 });

  // The conversation transaction_id in the materialized tx panel
  // should match the one the mini showed. The full page renders
  // the id in two places (the conversation header label and the
  // transaction field), so we use .first() and exact-match to
  // disambiguate.
  await expect(page.getByText(miniTxId, { exact: true }).first()).toBeVisible();
});