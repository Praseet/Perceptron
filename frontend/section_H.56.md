# H.56 Test the actual user story, not only the DOM

The highest-value Playwright scenarios are:

```text
Home
→ Run the loop
→ Loop page opens with 1-cycle prefill

Identify
→ open SE-001
→ click Generate sample
→ Generate page prefilled

Generate
→ generate
→ go to Defend
→ generated transaction is loaded

Defend
→ predict
→ probability and SHAP appear

Loop
→ run
→ events appear
→ deltas update
→ history gains a row
```

These sequences are more valuable than dozens of isolated CSS assertions.

---

