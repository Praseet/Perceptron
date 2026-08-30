import { defineConfig, devices } from "@playwright/test";

// Phase 10 step 1: six total run configurations per spec file:
//   chromium-desktop  (Desktop Chrome @ 1440x900)
//   chromium-mobile   (Desktop Chrome @ 390x844, iPhone-class)
//   firefox-desktop   (Desktop Firefox @ 1440x900)
//   firefox-mobile    (Desktop Firefox @ 390x844)
//   webkit-desktop    (Desktop Safari @ 1440x900)
//   webkit-mobile     (Desktop Safari @ 390x844)
// Screenshot naming (Phase 10 step 2): tests/e2e/screenshots/<page>-<project>.png
// where <project> matches one of the six names above (e.g.
// home-chromium-desktop.png). Project name embeds the viewport.

const DESKTOP_VIEWPORT = { width: 1440, height: 900 };
const MOBILE_VIEWPORT = { width: 390, height: 844 };

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false, // single shared dev server; serial avoids port contention
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "list",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:5173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium-desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: DESKTOP_VIEWPORT,
      },
    },
    {
      name: "chromium-mobile",
      use: {
        ...devices["Desktop Chrome"],
        viewport: MOBILE_VIEWPORT,
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "firefox-desktop",
      use: {
        ...devices["Desktop Firefox"],
        viewport: DESKTOP_VIEWPORT,
      },
    },
    {
      name: "firefox-mobile",
      use: {
        ...devices["Desktop Firefox"],
        viewport: MOBILE_VIEWPORT,
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "webkit-desktop",
      use: {
        ...devices["Desktop Safari"],
        viewport: DESKTOP_VIEWPORT,
      },
    },
    {
      name: "webkit-mobile",
      use: {
        ...devices["Desktop Safari"],
        viewport: MOBILE_VIEWPORT,
        isMobile: true,
        hasTouch: true,
      },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});