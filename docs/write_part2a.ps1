$path = 'D:\Projects\fraud_model\docs\UI_IMPLEMENTATION_FINDINGS.md'
$content = @'

## 1. What the codebase actually gives us (audited 2026-08-28)

### 1.1 Identify -- the attack surface
- **`src/identify/attack_profiles.py`** -- `ATTACK_PROFILES` dict with 4 wired profiles:
  - `voice_clone_scam` (SE-001, fraud_type=`ai_impersonation`)
  - `synthetic_identity_basic` (KYC-002, fraud_type=`synthetic_identity`)
  - `bnpl_max_out` (PR-003, fraud_type=`bnpl_abuse`)
  - `llm_jacking` (AI-004, fraud_type=`ai_impersonation`) -- **the novel contribution**
  - Each has `amount_range`, `urgency`, `evasion_techniques`, `description`. **No live narration here -- only config.**
- **`docs/ATTACK_TAXONOMY.md`** -- 25 attacks, 5 categories (SE / KYC / PR / AI / BM) with feasibility star ratings, status (Implemented / Partial / Conceptual / **TO IMPLEMENT** / **NOVEL**).
- **The taxonomy doc is the source of truth for the Identify page.** The Python module is only a subset of it. **For the UI we read the Markdown.**

### 1.2 Generate -- the attack simulation engine
- **`src/generator/rule_generator.py`** -- orchestrator; produces 1,064,963-row `data/raw/transactions.csv` with 7 fraud types.
- **`src/generator/llm_generator.py`** -- 1,347 lines. LLM writes a fraud *pretext* (a fake "voice clone script", a fake "support call"), a judge model validates no PII leaks, then `materialize_llm_transaction()` (L1258) turns the conversation into a row.
- **`src/generator/anti_leakage.py`** -- validates generated transactions do not leak card data, etc.
- **`FRAUD_TYPE_TARGETS` in `src/config.py`** -- exact target counts: `account_takeover=120`, `ai_impersonation=80`, `auth_bypass=220`, `bustout_identity=450`, `card_testing=340`, `synthetic_identity=100`, `bnpl_abuse=80` (total fraud = 1,390, with ~212K normal = 213,638 rows in train+val+test).
- **`data/raw/generation_log.csv`** -- audit trail with `case_id, fraud_type, user_id, burst_size, probing_mode, device, n_transactions, auth_failures_before_success, new_device, geo_anomaly, ring_id`.
- **Drop stats** -- `materialize_llm_transaction` takes a `drop_stats: dict | None` param; `rule_generator.py` line 478+ tracks it. Reasons: `transaction_not_attempted`, `insufficient_prior_history`, `pii_leaked`, etc. Read these at the call site to populate the Generate page drop readout.

### 1.3 Defend -- the live inference
- **`src/fraud_model/inference.py` -- `FraudInferenceService`** with these public methods (confirmed from source):
  - `predict_single(tx: dict, threshold=0.5, include_tier2=False)` -- returns dict with `probability`, `label`, plus tier2 fields
  - `predict_batch(df, threshold=0.5, include_tier2=False)` -- returns DataFrame
  - `get_business_metrics(proba, y_true, thresholds=BUSINESS_THRESHOLDS)` -- returns list[dict] with precision/recall/F1/FP/FN per threshold
  - `health_check()` -- returns dict with `tier1_loaded`, `tier2_loaded`, `tier2_p99_threshold`, `test_prediction`
  - `initialize()` -- lazy-loads artifacts
'@
Add-Content -Path $path -Value $content -Encoding UTF8
Write-Output "Part 2a added: $((Get-Item $path).Length) chars total"
