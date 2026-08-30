# H.31 Home metrics reconciliation

There are multiple historical metrics in the repository:

- `README.md` contains an older 96.3% headline.
- `CHANGELOG.md` documents the frozen Tier 1 test PR-AUC as `0.9072`.
- older frontend-vision prose contains `0.807` in the homepage example.
- later Build Bible materializes `0.9072` as the current baseline.

### Final UI rule

Use the later Build Bible/CHANGELOG value:

```text
PR-AUC baseline = 0.9072
```

when a historical baseline is required.

For the live Home KPI, prefer the current `/api/system/status`/evaluation response over a hardcoded literal.

Do not display the stale README number as if it were current.

---

