# Baseline Experiment — 2026-08-26

## Dataset
Total transactions: 213,638

Fraud:
- normal: 212,387
- account_takeover: 91
- ai_impersonation: 73
- auth_bypass: 240
- bustout_identity: 484
- card_testing: 363

## Split
Train: 149,546
Validation: 21,364
Test: 42,728

## Tier 1
Validation PR-AUC: 0.9458
Test PR-AUC: 0.9072

Frozen threshold: 0.96
Precision: 0.9044
Recall: 0.7834
F1: 0.8396
FP: 13
FN: 34

## AI Impersonation
Test transactions: 12
PR-AUC: 0.4538

AI-impersonation false negatives: 5

## Tier 2
Isolation Forest Test PR-AUC: 0.3356
AI-impersonation PR-AUC: 0.0168

## Important observation
AI impersonation remains substantially harder for the transaction model
than bustout/card-testing fraud.

## Status
BASELINE — DO NOT MODIFY.
