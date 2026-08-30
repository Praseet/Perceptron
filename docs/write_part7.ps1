$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 9. Files to create (final inventory)

### Backend (`src/api/`)
- `__init__.py`
- `main.py` -- FastAPI app, CORS, route mounting
- `routes/predict.py` -- `/api/predict` + SHAP-per-tx
- `routes/attacks.py` -- `/api/attacks`, `/api/attacks/{id}`
- `routes/generate.py` -- `/api/generate`
- `routes/eval.py` -- `/api/eval/per-class`, `/api/eval/pr-curve`
- `routes/loop.py` -- `/api/loop/run` (SSE), `/api/loop/history`
- `routes/system.py` -- `/api/system/status`
- `data/attacks.yaml` -- 25-attack taxonomy as data
- `services/inference.py` -- thin wrapper around `FraudInferenceService`
- `services/shap_explain.py` -- **new** per-tx SHAP function
- `services/generator.py` -- wraps `rule_generator` / `llm_generator`
- `services/loop_runner.py` -- wraps `feedback_loop` with SSE-friendly callbacks
- `requirements.txt` entry: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pyyaml`, `sse-starlette`

### Frontend (`frontend/`)
- `package.json` -- Next 15, React 19, shadcn deps
- `next.config.ts` -- `api rewrites: { "/api/*": "http://localhost:8000/api/*" }`
- `tailwind.config.ts` -- tokens from section 3
- `app/layout.tsx` -- Inter + JetBrains Mono + Space Grotesk, QueryClientProvider
- `app/page.tsx` -- Home (loop + KPIs)
- `app/identify/page.tsx`
- `app/generate/page.tsx`
- `app/defend/page.tsx`
- `app/loop/page.tsx`
- `components/nav.tsx` -- 4 nav items
- `components/loop-diagram.tsx` -- SVG with animation
- `components/shap-waterfall.tsx` -- Recharts bar
- `components/pr-curve.tsx` -- Recharts line
- `components/kpi-tile.tsx` -- number counter
- `lib/api.ts` -- typed fetch helpers
- `lib/sse.ts` -- `EventSource` wrapper
- `lib/queries.ts` -- TanStack Query hooks

---

## 10. What the implementer (Cline) should do, in order

1. **Confirm section 8 decisions with the user** (1 question only, see above).
2. **Build `src/api/`** end-to-end with `?demo=true` fallbacks on every endpoint. Verify with `curl`/`httpie`.
3. **Build `frontend/`** following the section 6 sequence. Use Playwright to screenshot every page after building it and self-critique against section 3.
4. **Wire SSE on the Loop page** with polling fallback if EventSource is awkward.
5. **Final pass:** mobile breakpoints, dark mode (already locked), accessibility (`aria-live` on the loop event log, keyboard focus on SHAP bars).
6. **Freeze.** No new features on Day 4.

---
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 7 added: $((Get-Item $path).Length) chars total"
