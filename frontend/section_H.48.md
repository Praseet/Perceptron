# H.48 Cline “do not create wrapper soup” rule

Do not create:

```text
PanelWrapper
CardWrapper
SectionWrapper
VisualWrapper
DashboardShell
InnerPanel
PanelInner
PanelContent
```

for every `<div>`.

Create components only when:

- they have repeated behavior,
- they have stable semantics,
- they are explicitly part of the design system,
- or the phase names them.

Prefer simple markup for one-off layout.

---

