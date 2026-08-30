$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 6. 3-day sequence (revised -- prototype is the star)

### Day 1 (28 Aug) -- foundation
- **AM:** `src/api/main.py` FastAPI skeleton; wrap `predict_single` + `health_check`; CORS; verify with `curl` that `/api/predict` returns a real probability.
- **PM:** Next.js 15 scaffold (`pnpm create next-app@latest`), shadcn init, Tailwind tokens from section 3 wired into `tailwind.config.ts`, homepage with the loop diagram (static first, then animated), 4 nav items, footer. End of day: working homepage that loads, loop animates, nav links go to placeholder pages.

### Day 2 (29 Aug) -- the four pages
- **AM:** **Defend page first** (highest-judge-time, SHAP waterfall, PR curve, business thresholds, live predictor).
- **PM:** Generate (LLM path with rule-based fallback) -> Identify (read view over taxonomy).

### Day 3 (30 Aug) -- the loop, polish, freeze
- **AM:** Loop page (SSE-backed "Run the loop", cycle history, before/after).
- **PM:** Playwright-MCP screenshot every page at 1440x900 and 390x844; self-review against section 3 anti-patterns; fix. Run full demo twice from cold start.
- **Eve:** 6-page docx walkthrough opening with a screenshot of the homepage loop.

### Day 4 (31 Aug) -- emergency fixes only. Do not refactor.

---

## 7. Forbidden list (per section 6 of locked doc, re-stated)

- No new colors outside section 3 tokens. No `bg-blue-500`, no `text-purple-300`.
- No glassmorphism. No `backdrop-blur`, no `bg-white/10` over backgrounds.
- No emoji in body copy. Lucide only.
- No `framer-motion` outside the homepage loop and number counters.
- No Lottie, no video, no animated GIFs. Static SVG only.
- No "powered by AI" / "intelligent" / "smart" copy.
- No fake numbers. Every metric on the homepage is from real eval or recomputed.
- No shadcn `bg-gradient-*` anywhere.
- No sidebar. 4 nav items are the IA.
- No Tailwind defaults -- every color is a token, every spacing a multiple of 8.
- No emoji icons. Lucide only.

---

## 8. Open decisions to confirm before code

1. **Package manager:** `pnpm` (recommended for shadcn) vs `npm` vs `bun`. Default to `pnpm` unless user objects.
2. **TanStack Query version:** current is v5 (stable, React 18+ + 19 supported).
3. **App Router vs Pages Router:** App Router (locked in `docs/FRONTEND_VISION.md` section 0).
4. **TypeScript strict:** yes (catches `predict_single` dict shape errors at build time).
5. **LLM dependency in dev:** `AFL_USE_LLM` defaults to unset -> rule-based path; demo never hits the LLM.
6. **Data source for `/api/attacks`:** hardcode into `src/api/data/attacks.yaml` at build time, NOT parse the Markdown at runtime (avoids a markdown dep on the API server).

---
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 6 added: $((Get-Item $path).Length) chars total"
