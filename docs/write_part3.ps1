$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 2. The 4 nav items mapped to backend capabilities

Every screen must answer one of the five scoring questions:
**diversity . fidelity . detection efficacy . novelty . real-world feasibility.**

| Page | Scoring axis | Backend source | Endpoints needed |
|---|---|---|---|
| **Home** (loop diagram) | novelty + closed loop | static + `/api/system/status` | `GET /api/system/status` |
| **Identify** | diversity | `docs/ATTACK_TAXONOMY.md` (read) | none (read-once at build) |
| **Generate** | fidelity | `src/generator/rule_generator.py`, `llm_generator.py` | `POST /api/generate`, `GET /api/attacks`, `GET /api/attacks/{id}` |
| **Defend** | detection efficacy | `FraudInferenceService`, `explain.py` (per-tx SHAP) | `POST /api/predict`, `GET /api/eval/per-class`, `GET /api/eval/pr-curve` |
| **Loop** | real-world feasibility + novelty | `feedback_loop.py` (live run via SSE) | `GET /api/loop/history`, `POST /api/loop/run` (SSE) |

---

## 3. Aesthetic system (locked) -- copy verbatim

### 3.1 Color tokens (Tailwind config)

| Token | Hex | Tailwind name | Used for |
|---|---|---|---|
| `--bg-base` | `#0A0E1A` | `bg-base` | page background |
| `--bg-panel` | `#0F1626` | `bg-panel` | card / panel |
| `--bg-elevated` | `#161E33` | `bg-elevated` | hover, focused, modals |
| `--bg-grid` | `#0D1322` | `bg-grid` | subtle grid texture layer |
| `--border-subtle` | `#1F2A44` | `border-subtle` | panel borders |
| `--border-strong` | `#2E3D5F` | `border-strong` | emphasized borders |
| `--text-primary` | `#E6ECFF` | `text-primary` | body text |
| `--text-secondary` | `#8B9DC3` | `text-secondary` | muted text |
| `--text-muted` | `#5A6B8A` | `text-muted` | meta text |
| `--text-mono` | `#B8C5DD` | `text-mono` | IDs, amounts, hashes |
| `--accent-cyan` | `#00D4FF` | `text-accent` / `border-accent` | brand, links, focus |
| `--accent-cyan-dim` | `#0088AA` | (hover/disabled) | |
| `--status-safe` | `#00FF88` | `text-safe` / `bg-safe` | pass / legit |
| `--status-warn` | `#FFB800` | `text-warn` / `bg-warn` | review |
| `--status-threat` | `#FF3D5A` | `text-threat` / `bg-threat` | fraud / fail |
| `--loop-attack` | `#FF6B35` | (Generate leg) | |
| `--loop-defend` | `#00D4FF` | (Defend leg) | |
| `--loop-identify` | `#B47AFF` | (Identify leg) | |
| `--loop-improve` | `#00FF88` | (Improve leg) | |

### 3.2 Typography
- **Sans:** Inter (UI / body / labels)
- **Mono:** JetBrains Mono (IDs, amounts, hashes, SHAP values -- the "this is a number, not prose" rule)
- **Display:** Space Grotesk (hero, large numerals)
- **No emoji in body copy. Icons only via Lucide** (shadcn default).

### 3.3 Layout primitives
- **8px grid.** Multiples of 8 (4 only inside table cells).
- **Max widths:** 1280px homepage, full-bleed loop diagram, 1024px docs-style pages.
- **Radii:** 8px cards, 4px inputs, **0px loop diagram nodes** (sharp = technical).
- **No shadows. Borders only.** Depth from `--bg-elevated` on hover, not `box-shadow`.

### 3.4 Motion (sparse -- one orchestrated moment per page)
- **Homepage hero:** 4-node loop animates once on mount, ~2.4s. Each leg lights up in sequence: Identify -> Generate -> Defend -> Improve. After first pass, each node pulses softly in its assigned color on a 4s cycle.
- **Number counters:** count up from 0 -> target over 1.2s on first viewport entry.
- **Chart reveals:** mount with opacity 0 -> 1, stagger 80ms.
- **No `framer-motion` outside hero + counters. Plain CSS transitions elsewhere.**

---
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 3 added: $((Get-Item $path).Length) chars total"
