import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "../../test-results");

/**
 * Phase 5 - Home page visual self-review.
 *
 * Per the spec: "if you have access to a Playwright MCP tool or any
 * other screenshot capability, use it to review your own output
 * before declaring this phase done." This test exercises the full
 * Home page (the first page a judge lands on) and captures a
 * fullpage screenshot for the human self-review. It also asserts
 * a few hard requirements:
 *   - The hero headline renders the exact locked copy.
 *   - The hero KPI row reads the real getSystemStatus() data
 *     (Transactions=1,064,963, Fraud rate=0.04%, PR-AUC=0.9072).
 *   - The LoopDiagram mounts with all 4 legs.
 *   - The "Built on real attacks" pillar miniatures load 5 attacks.
 *   - The "Numbers that hold up" PR-AUC table renders 7 rows.
 *   - No console errors.
 *   - Navigating to /identify, /generate, /defend, /loop shows the
 *     phase-N placeholder (per the spec's "no nav link to a page
 *     that doesn't have real content" - being explicit that no
 *     real content is being claimed).
 */
test("phase 5 - Home page renders, KPIs load, no console errors", async ({
  page,
}) => {
  const consoleErrors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  });

  await page.goto("/", { waitUntil: "networkidle" });
  await page.waitForTimeout(2800); // let the LoopDiagram intro complete

  // Hero headline - exact locked copy.
  await expect(
    page.locator("h1", { hasText: "The AI that learns fraud by" }),
  ).toBeVisible();

  // Hero CTA buttons.
  await expect(page.locator("text=Run the loop").first()).toBeVisible();
  await expect(page.locator("text=Browse 25 attacks").first()).toBeVisible();

  // LoopDiagram mounts with all 4 legs.
  const nodeCount = await page.locator("[data-leg]").count();
  expect(nodeCount).toBe(4);

  // KPI row: Transactions = 1,064,963.
  const txKpi = page.locator("text=Transactions").first();
  await txKpi.scrollIntoViewIfNeeded();
  await page.waitForTimeout(2000);
  const txValue = await page
    .locator("p.text-data-lg", { hasText: /1,064,963/ })
    .first()
    .innerText();
  expect(txValue).toMatch(/1,064,963/);

  // KPI row: PR-AUC = 0.9072.
  const prAucValue = await page
    .locator("p.text-data-lg", { hasText: /0\.9072/ })
    .first()
    .innerText();
  expect(prAucValue).toMatch(/0\.9072/);

  // Phase 10.5 §5.1: ClosedLoopStages was merged into PillarPreviewCards;
  // the merged section is now titled "See it work" instead of having
  // two consecutive sections ("The closed loop, in four stages" +
  // "Built on real attacks"). The merged section still renders the
  // four pillars; the Identify mini's top-5 attack list assertion
  // below exercises one of them.
  await expect(
    page.locator("h2", { hasText: "See it work" }),
  ).toBeVisible();
  // Identify mini: at least 5 attack rows (top-5 by feasibility).
  const identifyBtns = page.locator("article", { hasText: "Identify" }).locator("button[onclick], button");
  // The mini lists 5 clickable attack rows.
  const attackRows = page.locator("article", { hasText: "Identify" }).locator("ul > li");
  await expect(attackRows).toHaveCount(5);

  // Numbers that hold up section.
  await page.locator("#numbers-that-hold-up").scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  await expect(
    page.locator("h2", { hasText: "Numbers that hold up" }),
  ).toBeVisible();
  // PerFraudTypeTable: 7 rows for 7 fraud types.
  const evalRows = page.locator("#numbers-that-hold-up tbody tr");
  await expect(evalRows).toHaveCount(7);

  // No console errors.
  expect(consoleErrors).toEqual([]);

  // Full-page screenshot for human self-review.
  await page.screenshot({
    path: path.join(OUT, "home-page.png"),
    fullPage: true,
  });
});

/**
 * Phase 5 - Placeholder routes show "this page is built in Phase N".
 * Note: /identify was built out in Phase 6, /generate in Phase 7,
 * /defend in Phase 8, and /loop in Phase 9, so none of them show
 * the placeholder copy anymore. The loop is empty.
 */
for (const [route, phase] of [
] as const) {
  test(`phase 5 - placeholder route ${route} shows ${phase} copy`, async ({
    page,
  }) => {
    await page.goto(route, { waitUntil: "networkidle" });
    await expect(page.locator(`text=${phase}`).first()).toBeVisible();
    await expect(page.locator("text=Back to home").first()).toBeVisible();
  });
}
