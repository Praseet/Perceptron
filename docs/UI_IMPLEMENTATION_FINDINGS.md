# UI Implementation Findings -- Adversarial Fraud Lab (AFL)

> **Purpose.** Single source of truth for *building* the web prototype, assembled
> from the project docs, the actual codebase, and the locked design decisions
> in `docs/FRONTEND_VISION.md`. Use this when implementing, not `frontend-vision.md`
> (the older research doc) and not the raw source files.
>
> **Status.** Pre-implementation. No FastAPI app, no `src/api/`, no
> `frontend/` folder exist yet -- only the broken Streamlit `app.py`.
> Compiled 2026-08-28 by Cline. Deadline: 2026-08-31 (3 days).

---

## 0. Locked decisions (do not re-litigate)

| # | Decision | Value | Source |
|---|----------|-------|--------|
| 1 | **Project name** | Adversarial Fraud Lab (AFL) | `HACKATHON_MASTER_PLAN.md` |
| 2 | **Backend** | FastAPI at `src/api/main.py`, mounted at `/api/*` | `docs/FRONTEND_VISION.md` sec 4 |
| 3 | **Frontend stack** | Next.js 15 (App Router) + shadcn/ui + Tailwind + Recharts | `docs/FRONTEND_VISION.md` sec 0 |
| 4 | **State** | TanStack Query for server state; SSE (or polling fallback) for live loop | `docs/FRONTEND_VISION.md` sec 0 |
| 5 | **Aesthetic** | Dark cyber-command (Wiz / Darktrace / CrowdStrike) -- see sec 3 for full token spec | `docs/FRONTEND_VISION.md` sec 2 |
| 6 | **Hero** | 4-node loop diagram with one-shot ~2.4s animation | `docs/FRONTEND_VISION.md` sec 0, 2.5 |
| 7 | **IA** | Multi-view app, no sidebar. 4 nav items: Identify, Generate, Defend, Loop + Home | `docs/FRONTEND_VISION.md` sec 3, 6 |
| 8 | **Scope bias** | ~70% prototype, ~20% docx, ~10% repo hygiene | `docs/FRONTEND_VISION.md` sec 0 |
| 9 | **Demo resilience** | Every API endpoint accepts `?demo=true` and returns canned data so the demo never breaks | `docs/FRONTEND_VISION.md` sec 4 |
| 10 | **LLM in demo** | Off by default; rule-based fallback. Enable via `AFL_USE_LLM=1`; silently skip on any error | `docs/FRONTEND_VISION.md` sec 7 |
| 11 | **Hosting** | Local-only. `npm run dev` + `uvicorn src.api.main:app`. No Vercel deploy | `docs/FRONTEND_VISION.md` sec 7 |
| 12 | **Forbidden** | No new colors outside sec 3, no glassmorphism, no emoji in body copy, no `framer-motion` except hero | `docs/FRONTEND_VISION.md` sec 6 |

If any future implementation question conflicts with this table, this table wins.

---
