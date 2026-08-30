# H.32 Honest metric labeling

Use phrases that make metric provenance clear.

Good:

```text
Test PR-AUC
Validation recall
False negatives
Operating threshold
Historical feedback-loop result
```

Bad:

```text
Accuracy
Success rate
AI score
Confidence
```

when those are not the actual metrics.

Do not rename PR-AUC to “accuracy.”

Do not rename recall to “detection rate” unless the relevant spec explicitly wants that wording.

---

