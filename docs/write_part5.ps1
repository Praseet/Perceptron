$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 5. The four pages -- interaction model

### 5.1 Home (loop diagram + numbers that hold up)
- **Hero:** 4-node loop SVG with 2.4s intro animation, then 4s pulse.
  - Node colors: Identify `#B47AFF`, Generate `#FF6B35`, Defend `#00D4FF`, Improve `#00FF88`.
  - Click each node -> router-pushes to that page.
- **"Numbers that hold up"** -- 4 KPI tiles, all sourced from real data:
  - Transactions scored: `1,064,963` (real row count)
  - PR-AUC: `0.9072` (real frozen baseline test PR-AUC)
  - Attacks generated: `1,390` (sum of `FRAUD_TYPE_TARGETS`)
  - FN reduced by closed loop: `34 -> 32` (real, from CHANGELOG)
- **"The loop in motion"** -- 3 most recent runs from `/api/loop/history` with before/after.

### 5.2 Identify (attack taxonomy browser)
- Filterable table: 25 attacks from `docs/ATTACK_TAXONOMY.md`.
- Filter chips: Category (SE/KYC/PR/AI/BM), Status (Implemented/Partial/Conceptual/Novel), Feasibility (star count).
- Each row -> detail panel: description, feasibility rationale, **"Wired to a generator?"** badge, **"Generate a sample"** button -> pre-fills `/api/generate` on the Generate page with `attack_id`.
- AI-004 (LLM-Jacking) and AI-005 (Autonomous Fraud Agent) get a small `NOVEL` badge -- judges should find them in <5s.

### 5.3 Generate (paired narrative <-> transaction)
- Top: profile picker (4 wired profiles) + count + urgency dropdown + "Run" button.
- Below: **paired evidence view** -- left side: the LLM-generated *pretext* (the fake "voice clone script" text from `llm_generator`), right side: the transaction row it produced. A visible line connects `urgency_level` -> `three_ds_failure_prob` etc.
- **Drop rate readout:** `Generated: 12 | Dropped: 2 (pii_leaked: 1, transaction_not_attempted: 1) | Accepted: 10`. Show this honestly -- it is the fidelity argument.
- "Predict on this" button -> jumps to Defend page with the generated transaction pre-loaded.

### 5.4 Defend (the strongest page)
- **Top half:** Transaction builder (real `FEATURE_COLS` from config, 20 numeric + 3 categorical sliders/dropdowns) + "Predict" button. Calls `/api/predict`.
- **Result panel (right of builder):**
  - Big probability number (mono font) with status color (green/amber/red).
  - Top 10 SHAP features as a signed horizontal bar chart (Recharts). **Not a static PNG.**
- **Bottom half:**
  - Per-fraud-type PR-AUC table from `/api/eval/per-class`.
  - PR curve chart from `/api/eval/pr-curve` with the operating point marker.
  - Business threshold table at `[0.30, 0.50, 0.70, 0.90]` with precision/recall/F1/FP/FN per threshold.

### 5.5 Loop (the "watch it happen" page)
- "Run the loop" button (primary, big) -> `POST /api/loop/run` with SSE.
- Live event log streaming into a panel (each event = one row, mono font, timestamp).
- After completion: before/after panel:
  - Val recall: `0.8200 -> 0.8467`
  - Test recall: `0.7834 -> 0.7962`
  - FN: `34 -> 32`
  - PR-AUC: `0.9072 -> 0.9089`
  - Precision: `0.9044 -> 0.8562` (with a tooltip explaining the threshold tradeoff)
- "Recent runs" history list.

---
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 5 added: $((Get-Item $path).Length) chars total"
