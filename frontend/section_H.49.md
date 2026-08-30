# H.49 Cline debugging order

When a visual does not look right:

1. inspect computed CSS,
2. check the token variable resolves,
3. check container dimensions,
4. check flex/grid constraints,
5. check overflow,
6. check browser default styles,
7. only then modify component code.

Do not immediately add:

```text
!important
```

or arbitrary transform offsets.

---

