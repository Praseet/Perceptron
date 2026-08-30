# H.61 Explicit “do not use” source files for visual decisions

These are useful for understanding history but should not be treated as the current visual source of truth:

```text
frontend-vision.md
docs/DESIGN_SYSTEM.md
legacy frontend source from frontend.zip
```

`docs/FRONTEND_VISION.md` and this build bible control the final design direction.

The reason for this explicit list is to prevent an agent from seeing the old light-mode design-system document or legacy dashboard and “helpfully” reintroducing the wrong system.

---

