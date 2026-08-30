// Phase 10 step 2 - shared smoke-test helpers.
// Every page's smoke spec follows the same shape:
//   - Navigate to the route
//   - Assert the page's header text (exact copy from each phase's spec) is visible
//   - Capture console errors at error level (warn is allowed except React key-prop)
//   - Exercise the one interaction each page exists to demonstrate
//   - Take a full-page screenshot saved to tests/e2e/screenshots/<page>-<project>.png
//
// This module exports the common helpers so the per-page specs stay short.

import { Page, expect } from "@playwright/test";

/**
 * Attach a console error listener to the page. Returns the listener
 * (with `.messages`) so the test can assert zero messages were logged
 * at `error` level during the page lifecycle. A `warn` is acceptable and
 * is logged to the test report but not failed on, unless it's a React
 * key-prop warning (which IS a real bug and does fail the test).
 */
export function trackConsoleErrors(page: Page) {
  const messages: { type: string; text: string }[] = [];
  const handler = (msg: { type(): string; text(): string }) => {
    messages.push({ type: msg.type(), text: msg.text() });
  };
  page.on("console", handler);
  return {
    messages,
    detach: () => page.off("console", handler),
    /**
     * Assert: zero error-level messages. Returns any key-prop warnings
     * so the test can fail on them even if they're warn-level.
     */
    assertClean() {
      const errors = messages.filter((m) => m.type === "error");
      const reactKeyWarnings = messages.filter(
        (m) =>
          (m.type === "warning" || m.type === "warn") &&
          /each child in a list should have a unique "key" prop/i.test(m.text),
      );
      expect(errors, `console errors: ${JSON.stringify(errors)}`).toEqual([]);
      expect(reactKeyWarnings, `React key-prop warnings: ${JSON.stringify(reactKeyWarnings)}`).toEqual([]);
    },
  };
}

/**
 * Take the per-page screenshot. The project name embeds the viewport
 * (chromium-desktop, chromium-mobile, etc.), so the filename is
 * `<page>-<project>.png`. The directory is tests/e2e/screenshots/.
 */
export function screenshotNameFor(testInfo: { title: string; project: { name: string } }): string {
  const page = testInfo.title.split(" ")[0].toLowerCase();
  return `${page}-${testInfo.project.name}.png`;
}