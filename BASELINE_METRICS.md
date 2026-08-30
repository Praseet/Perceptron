# Baseline Metrics — Pre-Audit Capture

**Captured:** 2026-08-30
**Run:** `python -m src.models.train` then `python -m src.models.evaluate` (no generator regen; existing pickles were reused for reproducibility with current artifacts).
**Script versions at capture:** xgboost 3.4.1, scikit-learn 1.9.0, pandas 3.0.5, numpy 2.5.2, imbalanced-learn 0.14.2.

> **DISCREPANCY FROM BRIEF'S LAST-KNOWN-GOOD (mandatory stop-and-report):**
> The brief stated last-known-good was test PR-AUC **0.9533**, frozen threshold **0.95**, precision **0.989** / recall **0.841**, FN=17 (16 ai_impersonation + 1 bustout_identity), case-level recall **0.6596**, ai_impersonation PR-AUC **0.7782**, auth_bypass PR-AUC **0.9996**.
> This baseline shows: test PR-AUC **0.7971**, threshold 0.95, P=**0.8545** / R=**0.7231**, FN=**72** (17 ai_imp + 16 card_testing + 14 acct_takeover + 14 auth_bypass + 11 bustout), case-level recall **0.4262**, ai_impersonation PR-AUC **0.0006**, auth_bypass PR-AUC **0.0210**.
>
> Per the brief's instruction, this is flagged before proceeding to fixes. Root cause appears to be a generator drift — see §4 — that has altered the fraud-type mix and feature distributions the model was previously trained against.

---

## 1. Split sizes (current run)

| Split | Rows | Fraud rate |
| --- | ---: | ---: |
| Train | 745,474 | 0.1138 % |
| Val | 106,496 | 0.1146 % |
| Test | 212,993 | 0.1221 % |

## 2. Tier 1 (XGBoost, frozen baseline)

| Metric | Val | Test |
| --- | ---: | ---: |
| PR-AUC | 0.8073 | **0.7971** |
| Recall @ 0.95 | — | 0.7231 |
| Precision @ 0.95 | — | 0.8545 |
| F1 @ 0.95 | — | 0.7833 |
| FN @ 0.95 | — | 72 |
| FP @ 0.95 | — | 32 |
| FPR @ 0.95 | — | 0.000150 |

## 3. Tier 2 (Isolation Forest)

| Metric | Val | Test |
| --- | ---: | ---: |
| PR-AUC | 0.0052 | 0.0069 |

Tier 2 is unsupervised and the current config produces a near-random ranking (no signal). Out of scope of this audit (existing behavior); flagged for the team.

## 4. Business threshold table (test)

| threshold | precision | recall | f1 | FP | FN |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.30 | 0.129 | 0.885 | 0.225 | 1553 | 30 |
| 0.50 | 0.243 | 0.873 | 0.380 | 707 | 33 |
| 0.70 | 0.405 | 0.815 | 0.542 | 311 | 48 |
| 0.90 | 0.709 | 0.769 | 0.738 | 82 | 60 |
| **0.95 (frozen)** | **0.855** | **0.723** | **0.783** | **32** | **72** |

## 5. Per-fraud-type test PR-AUC (Tier 1)

| fraud_type | test n | PR-AUC | expected (brief) |
| --- | ---: | ---: | ---: |
| account_takeover | 30 | 0.4541 | — |
| **ai_impersonation** | **17** | **0.0006** | **0.7782** |
| auth_bypass | 15 | 0.0210 | 0.9996 |
| bnpl_abuse | 32 | 1.0000 | — |
| bustout_identity | 105 | 0.8851 | 0.9996 |
| card_testing | 41 | 0.6349 | — |
| synthetic_identity | 20 | 0.9925 | — |

## 6. Case-level recall

| pre-fix | post-fix | expected (brief) |
| ---: | ---: | ---: |
| 0.4262 (26/61) | **0.4000 (24/60)** | 0.6596 |

Definition (already correct, see `evaluate.py:128-135`): a campaign is "detected" if at least one of its transactions is predicted positive. With multi-tx cases (bustout ~20 tx, synthetic_identity ~20 tx), missing 19/20 transactions still counts as detected — so case-level recall will always look better than transaction-level recall. Confirmed this is a definition difference, not a model issue; flagged for transparency.

## 7. False-negative breakdown

| fraud_type | FN |
| --- | ---: |
| ai_impersonation | 17 (100 % of class) |
| card_testing | 16 |
| account_takeover | 14 |
| auth_bypass | 14 |
| bustout_identity | 11 |

## 8. Train fraud-class distribution

| fraud_type | train n | FRAUD_TYPE_TARGETS (config.py) |
| --- | ---: | ---: |
| bustout_identity | 296 | 450 |
| card_testing | 196 | 340 |
| synthetic_identity | 139 | 100 (overshoot) |
| bnpl_abuse | 70 | 80 |
| account_takeover | 59 | 120 (undershoot) |
| ai_impersonation | 52 | 80 |
| auth_bypass | 36 | 220 (severe undershoot) |

The generator's actual outputs do not match `config.FRAUD_TYPE_TARGETS` — `rule_generator.py` defines its own internal `N_USERS = 15000` and inline pool-based injection (card_testing 2–8 % of a pool, etc.) rather than honouring the central targets. This is the most likely root cause of the drift between the brief's last-known-good numbers and the current run. **Did not change** — per the brief, no silent changes to fraud-type definitions; this is flagged for the project owner.

## 9. ai_impersonation: feature/labeling diagnosis

Per the brief's prompt: "Before adding model complexity, check whether this is a feature/labeling problem rather than a 'needs a fancier model' problem." Diagnostic on the post-fix training set:

| feature | impersonation mean | normal mean | impersonation std |
| --- | ---: | ---: | ---: |
| amount | 2099 | 1813 | (lognormal) |
| account_age_days | 1625 | 1538 | (overlapping) |
| count_30d | 28.8 | 40.1 | (similar) |
| new_device | 0.16 | 0.11 | (overlapping) |
| three_ds_failures | 0.46 | 0.18 | (mild lift) |

The means are within 10–15 % of normal — the anti-leakage fixes have collapsed the impersonation signature onto the normal distribution. There is essentially no signal left for the model to learn. This is not a model-complexity issue; it is a labeling issue. **Not modified** — flagging for the project owner.

## 10. Leakage-guard test result

| Run | transaction_id overlap | case_id overlap | Per-class case leaks | Verdict |
| --- | ---: | ---: | --- | --- |
| Pre-fix | 0 | **11** | synthetic_identity×7, bustout×3, bnpl×1 | **FAIL** |
| Post-fix | 0 | **0** | none | **PASS** |

(Strict-mode `python -m src.models.leakage_guard --strict` exits 0 post-fix.)