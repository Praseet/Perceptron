# ML Pipeline Audit + Adversarial Loop Fix — Agent Brief

## Scope & guardrails (read first)
- You own the backend/ML pipeline only: data generation, train/val/test split, defender training, evaluation, and the generate→defend feedback loop.
- Do NOT touch anything under the frontend app (React/Vite/TS, the Identify/Generate/Defend/Loop UI, the design system, tests/e2e). A separate agent owns that.
- Team is intro-ML level on a ~10 day hackathon timeline — prefer simple, verifiable fixes over clever ones. A correctly-scoped train/val/test loop beats a fancier but leaky one.
- Before changing anything: run the current pipeline end-to-end once to capture baseline numbers (PR-AUC, precision/recall overall and per-fraud-type, case-level recall, frozen threshold). Save these to `BASELINE_METRICS.md`. Every later change gets compared against this baseline — if a change makes a number worse without a documented reason, revert it.
- Never silently change the frozen decision threshold or the existing fraud-type definitions. If you think either needs to change, flag it in your report — don't just do it.
- Last known good numbers, for a sanity check against your baseline run: test PR-AUC 0.9533, threshold 0.95, precision 0.989 / recall 0.841 (FN=17: 16 ai_impersonation + 1 bustout_identity), per-type PR-AUC ai_impersonation 0.7782 (weakest, n=37) and bustout_identity 0.9996 (n=70), case-level recall 0.6596. If your run doesn't roughly match this, stop and report the discrepancy before proceeding — something else may have changed since.

## Objective 1 (priority) — find and fix train/test leakage in the generate→defend loop
Answer these with actual evidence from the code (file + line), not assumption:

1. Locate the code that (a) does the original train/val/test split, (b) trains/retrains the defender, (c) evaluates it, and (d) drives the generate→defend loop — i.e. calls the generator, decides what counts as a "missed" case, and feeds new attacks back in.
2. Determine:
   - Which split does "missed case" mining read from — train, val, or test?
   - Where do newly generated attack samples get appended — train only, or elsewhere too?
   - Does the test split ever change size or content after the very first split? (It should never grow or shrink after round 1.)
   - Is the same frozen test set re-scored after every single retrain, or only at defined checkpoints?
3. **The bug to look for:** if missed-case mining reads from the test split — directly, or indirectly through a shared "evaluate" function that happens to be called on test data — that's leakage. You're using the test set's answers to decide what to teach the model, then re-grading on that same test set. The resulting score improvement is partly manufactured, not evidence of a better model. This is the same failure mode as tuning an attack against the exact model/data you'll then report robustness numbers on — it proves memorization, not generalization.
4. **Fix pattern** (implement unless there's a strong reason not to — explain any deviation in your report):
   - Split once, up front, into train / val / test (already exists per the "Final Audited" build — SMOTENC three-way split, threshold frozen on val).
   - Every round of the loop: train on train → evaluate on val → mine false negatives from **val only, never test** → generate new attack variants of those types → append only to train → retrain → re-evaluate on val to decide whether to keep looping.
   - Test set: touched at most twice — once early as a sanity baseline, once at the very end for the final reported number. Never used to decide what the generator targets.
   - Add an automated check (script or pytest case) asserting no transaction/case ID present in test also appears in train after any round — a hard leakage guard, not just a design intention.
5. If time allows: hold out one additional small slice of data that the mining loop never touches at all, even during development. Use it exactly once as the final "did this actually generalize" number. That's the strongest story for judges — the reported numbers are on data the attacker never got to study.

## Objective 2 — audit whether the attacker/generator side is genuinely adversarial
Current setup (Tier 1): rule-based/statistical synthetic generator + LLM-prompted conversational attack generation. Check which pattern it currently matches:

- **Weak (likely current state):** take a missed transaction, jitter a few numeric fields, relabel, done. This produces near-duplicates of cases the model already half-recognizes — retraining on these mostly teaches memorization of specific values, not the underlying pattern, and will look weak to judges evaluating the "Generate" pillar.
- **What you want:** characterize *why* those cases were missed first (SHAP or feature-importance comparison of caught vs. missed fraud of the same type — which features look "normal" on the missed ones), then have the generator explicitly target those blind spots — vary the non-detected dimensions more, keep the fraud mechanic intact, and route the LLM prompt to explicitly try to "look ordinary" on the features currently driving detection.

Steps:
1. Read the current generator code/prompts and determine which pattern it matches.
2. If it's the weak pattern, redesign it to: (a) pull feature-importance/SHAP values for the relevant fraud type, (b) tell the generator which features are top detection signals, (c) instruct it to vary those specific signals toward "normal" ranges while preserving the fraud's core logic, (d) keep diversity — don't only produce minor variants of the exact missed cases; sample across the whole fraud type's feature space so the model learns the pattern, not the instances.
3. Add a cheap diversity check: average pairwise feature-distance between newly generated samples and the missed cases they were derived from. Near-zero means they're near-duplicates — flag it and widen the generation/perturbation range until diversity is reasonable, without producing physically implausible transactions (negative amounts, impossible timestamps, etc.).
4. Optional stretch, only if the above is solid and time remains: occasionally have the generator invent a pattern that isn't just a variant of the 5 known types, to test whether the defender generalizes at all vs. only pattern-matches known types. Report this separately from main recall numbers — it's testing something different (true novelty detection).

## Other pipeline issues worth a quick look (only after the above is stable)
- Confirm SMOTE/SMOTENC oversampling is applied only inside the training fold, **after** the split. If it's applied before splitting, synthetic minority points can leak across the train/val/test boundary the same way (SMOTE draws neighbors from the full pre-split minority class) — same bug, different location. Check explicitly.
- ai_impersonation is the weakest fraud type (PR-AUC 0.78 vs 0.99+ for bustout_identity). Before adding model complexity, check whether this is a feature/labeling problem (not enough distinguishing signal for this type at all) rather than a "needs a fancier model" problem.
- Case-level recall (0.66) is much lower than transaction-level recall (0.84) — confirm how "case" is defined; one missed transaction may be failing an otherwise-correct case. Could be a scoring-definition issue rather than a model issue.
- If you touch the frozen threshold or split ratios for any reason, log old vs. new values and why in your final report.

## Deliverable / report format
For every change:
- What you found (file/line, which failure mode it matched, if any)
- What you changed
- Baseline metric vs. new metric (overall + per-fraud-type PR-AUC/recall, case-level recall)
- Leakage-guard test result (pass/fail)
- Generator diversity metric before/after (if the generator was touched)
- Anything considered but not changed, and why

## Definition of done
- [ ] Baseline captured before any change
- [ ] Leakage source (if any) identified with file/line evidence
- [ ] Loop fixed so mining reads from val, not test; test set untouched except at defined checkpoints
- [ ] Automated leakage-guard check added and passing
- [ ] Generator audited against the weak/strong pattern above; diversity metric reported
- [ ] SMOTE/SMOTENC fold-placement confirmed
- [ ] All frontend files (React/Vite app, design system, tests/e2e) untouched
- [ ] Final metrics compared to baseline table, with an explanation for every regression
