# H.45 Cline “do not get confused” checklist

Before creating a new file, ask internally:

```text
Is this explicitly required by the current phase?
Does an existing file already own this concern?
Will this introduce a second source of truth?
Does this cross the feature dependency boundary?
Can the requirement be satisfied by existing primitives?
```

If the answer indicates duplication, stop and use the existing layer.

---

