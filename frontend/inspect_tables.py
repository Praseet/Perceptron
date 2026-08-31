import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://127.0.0.1:5173/loop", wait_until="networkidle")
        await page.wait_for_timeout(3500)
        # Count tables and find Run history one
        n = await page.locator("table").count()
        print(f"tables on /loop: {n}")
        for i in range(n):
            loc = page.locator("table").nth(i)
            txt = await loc.inner_text()
            label = await loc.evaluate("(el) => el.closest('[aria-label]')?.getAttribute('aria-label') || '(no label)'")
            print(f"  table {i}: parent aria-label={label}; first 80 chars of text: {txt[:80]!r}")
        await browser.close()

asyncio.run(main())