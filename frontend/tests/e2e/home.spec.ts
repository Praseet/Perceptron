// Phase 10 step 2 - home smoke spec.
// Navigates to "/", asserts the Hero h1, captures console errors,
// waits for the LoopDiagram mount animation to complete (the pulse
// state starts after 2400ms - per loop-diagram.tsx ANIM_TOTAL_MS),
// and saves a full-page screenshot.
//
// This is the first page a judge lands on; it must render cleanly
// with no console errors and the diagram must reach its settled pulse.

import { test, expect } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { trackConsoleErrors, screenshotNameFor } from "./_smoke-helpers";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const OUT = path.resolve(__dirname, "screenshots");

test("home page renders, loop diagram reaches settled pulse, no console errors", async ({ page }, testInfo) => {
  const tracker = trackConsoleErrors(page);
  await page.goto("/", { waitUntil: "networkidle" });

  // Headline (exact copy from src/features/home/hero.tsx)
  await expect(
    page.getByRole("heading", { level: 1, name: /The AI that learns fraud by/i }),
  ).toBeVisible();

  // The hero CTA - per Phase 5 spec the "Run the loop" button is the
  // primary call to action. Its presence + the link to /loop?prefill=1cycle
  // is the interaction that demonstrates the page works.
  // Use exact: true because the global nav also has a "Run the loop,
  // pre-filled for 1 cycle" button.
  const runTheLoop = page.getByRole("button", { name: "Run the loop", exact: true });
  await expect(runTheLoop).toBeVisible();

  // The LoopDiagram's mount animation runs over 2.4s. Wait for the
  // settled state (pulse overlay active) to render so the screenshot
  // captures the page in its final form.
  await page.waitForTimeout(2800);

  // The diagram is hidden below the `lg` breakpoint (the hero stacks
  // copy above and tucks the diagram behind a `hidden lg:block`
  // gate because the 480x480 SVG overflows a phone viewport). On
  // mobile this assertion is intentionally skipped; the spec only
  // requires the diagram to reach settled pulse on desktop where it
  // is actually rendered.
  const isDesktop = testInfo.project.name.endsWith("desktop");
  if (isDesktop) {
    await expect(
      page.locator(
        '[aria-label="Closed loop diagram: Identify, Generate, Defend, Improve"]',
      ),
    ).toBeVisible();

    // Interaction per Phase 10 spec: "Home — the loop diagram's
    // mount animation completes and settles into its pulse state."
    // The wait above is the interaction's effect; additionally
    // verify the "static - v1" settled-state label is present.
    await expect(
      page.locator('div.console span:has-text("static - v1")').first(),
    ).toBeVisible();
  }

  // Take a full-page screenshot.
  await page.screenshot({
    path: path.join(OUT, screenshotNameFor(testInfo)),
    fullPage: true,
  });

  tracker.assertClean();
});