# H.36 Table and chart overflow contract

A visualization may have its own scroll/clip region, but the page must not unexpectedly overflow horizontally.

Required:

```text
body width = viewport
```

not:

```text
body width = content width
```

When a table is wider than the viewport:

```text
outer panel
→ horizontal overflow inside panel
```

rather than:

```text
whole page → horizontal overflow
```

---

