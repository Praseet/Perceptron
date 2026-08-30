# H.34 Business-threshold table semantics

Threshold rows:

```text
0.30
0.50
0.70
0.90
```

Columns:

```text
Threshold
Precision
Recall
F1
FP
FN
Alert rate
```

Potentially include:

```text
TP
TN
```

if width allows.

The point is to make the precision/recall tradeoff legible to an operational reviewer.

Do not highlight only the highest metric. The point is that threshold choice is a business decision.

---

