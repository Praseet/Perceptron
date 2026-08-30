$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 11. Web research notes (2026-08-28)

- **shadcn/ui + Next.js 15 install (verified from ui.shadcn.com/docs/installation/next, 2026):** `pnpm dlx shadcn@latest init` (or `-t next` for App Router), then `pnpm dlx shadcn@latest add <component>`. New `components.json` is created at project root; aliases are `@/components/*` and `@/lib/*`.
- **FastAPI SSE (verified from fastapi.tiangolo.com/advanced/custom-response, 2026):** the recommended pattern is `return StreamingResponse(generator(), media_type="text/event-stream")`. Yield `f"data: {json.dumps(payload)}\n\n"` lines from the generator. For structured-event SSE, `sse-starlette` is a small library that handles the protocol correctly (heartbeats, last-event-id).
- **SHAP single-row (verified from shap.readthedocs.io, 2026):** `shap.TreeExplainer(model)(X_row)` returns an `Explanation` with `.values` (1D array of attributions), `.base_values` (scalar), `.data` (the input row). Sort by `|value|`, take top 10, return `[{feature, value, impact: "positive"|"negative"}, ...]`. Add the same `additivity_self_check` used in `explain.py` to ensure log-odds margin ~= base + sum(SHAP).
- **`web_search` tool was unavailable** in this session (credit/quota issue), so I could not run exhaustive search. Where I could, I used `fetch_web_content` on the canonical docs for shadcn, FastAPI, and SHAP and got current 2026 recommended patterns. If anything in sections 3-4 conflicts with what you see locally, the local docs win.

---

## 12. Source-of-truth map (what to read when stuck)

| Question | Read this | Path |
|---|---|---|
| What is the design? | Locked spec | `docs/FRONTEND_VISION.md` |
| What attacks exist? | Taxonomy | `docs/ATTACK_TAXONOMY.md` |
| What is the data shape? | Schema | `src/config.py` (`FEATURE_COLS`, `MODEL_COLS`) |
| How do I call the model? | Inference API | `src/fraud_model/inference.py` (`FraudInferenceService`) |
| How do I generate? | Generator entry | `src/generator/rule_generator.py` |
| How do I run the loop? | Loop entry | `src/models/feedback_loop.py` |
| What is the eval? | Eval + metrics | `src/models/evaluate.py` |
| What numbers are real? | Changelog | `CHANGELOG.md` |
| What is broken in app.py? | Audit | `frontend-vision.md` section 2 (research doc, kept for ref) |
| What is the build sequence? | Plan | `docs/HACKATHON_MASTER_PLAN.md` |

---

*End of findings doc. All cross-references point to files in this repo.*
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 8 added: $((Get-Item $path).Length) chars total"
'@
Add-Content -Path $path -Value $content -Encoding UTF8
