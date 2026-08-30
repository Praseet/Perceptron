$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 4. The API contract (locked)

FastAPI app at `src/api/main.py`, mounted at `/api/*`. Every endpoint accepts
`?demo=true` and returns canned data on import errors or model load failure.
All paths return JSON. Loop endpoints stream SSE.

```text
GET  /api/attacks
  -> [{id, name, category, status, feasibility, fraud_type, description}]

GET  /api/attacks/{id}
  -> single attack, with description and link to its generation config

POST /api/generate
  body: { attack_id: str, user_id: int | "random", urgency: "low"|"medium"|"high" | null }
  -> { run_id, conversation: [...], transaction: {...}, accepted: bool,
       rejection_reason?: str, drop_stats: {reason: count} }
  streams SSE if run > 2s; otherwise returns full payload

POST /api/predict
  body: { transaction: {...} }   // FEATURE_COLS-shaped dict
  -> { probability: float, threshold: float, label: "legit"|"fraud",
       shap: [{feature, value, impact}, ...] }   // top 10 features, signed

GET  /api/eval/per-class
  -> [{ fraud_type, count, precision, recall, pr_auc, fpr }]

GET  /api/eval/pr-curve
  -> { precision: [...], recall: [...], thresholds: [...],
       operating_point: {precision, recall, threshold} }

GET  /api/loop/history
  -> [{ run_id, started_at, duration_s, final_pr_auc, n_cycles, n_new_attacks }]

POST /api/loop/run
  body: { fraud_type: "all"|"...", n_new_attacks: int, max_cycles: int }
  -> streams SSE: { type: "cycle_start"|"cycle_end"|"miss_added"|"metric_update",
                   cycle, metric?, value?, ... }

GET  /api/system/status
  -> { online: bool, n_users, n_transactions, fraud_rate,
       pr_auc_test, last_retrain_at }
```

### 4.1 Implementation notes for each endpoint

- **`/api/attacks`** -- read once from `docs/ATTACK_TAXONOMY.md` at server startup, or hard-parse into a YAML in `src/api/data/attacks.yaml` to avoid runtime Markdown parsing. The latter is preferred (see section 8.6).
- **`/api/generate`** -- wraps `rule_generator.generate_case_batch` for the rule path; wraps `llm_generator.generate_llm_case_batch` + `materialize_llm_transaction` for the LLM path. Captures `drop_stats` from the `materialize_*` call. Honors `AFL_USE_LLM` env var; falls back to rule-based on any LLM error.
- **`/api/predict`** -- calls `FraudInferenceService.predict_single` then `shap.TreeExplainer(model)(features_single)` for a single row, returns top 10 features by `|SHAP|` with sign. **New per-tx SHAP function needed; current `explain.py` only does batch.** The pattern (confirmed from current SHAP docs): `explainer = shap.TreeExplainer(model); sv = explainer(X_row); top10 = sorted(zip(sv.feature_names, sv.values[0]), key=lambda kv: -abs(kv[1]))[:10]`.
- **`/api/eval/per-class` & `/api/eval/pr-curve`** -- call the existing `src/models/evaluate.py` logic, cache result (eval takes seconds, not ms).
- **`/api/loop/run`** -- uses FastAPI `StreamingResponse(generator(), media_type="text/event-stream")` (confirmed from FastAPI docs). Inside, call `feedback_loop.main()` with a `tee` callback that yields cycle/recall/FN updates as SSE `data: {json}\n\n` lines. Demo fallback: if real run is disabled, emit pre-canned cycle data from the CHANGELOG.
- **`/api/system/status`** -- count rows in `data/raw/transactions.csv` (1,064,963), return `pr_auc_test` from `xgboost_tier1.json` (load model + run on a cached sample of test_df).

---
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 4 added: $((Get-Item $path).Length) chars total"
