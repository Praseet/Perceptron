# H.47 Cline “one component, one responsibility” rule

Bad:

```text
HomePage.tsx
→ fetches attacks
→ fetches metrics
→ renders nav
→ renders footer
→ owns command palette
→ renders chart
→ formats dates
```

Better:

```text
HomePage
├── hero
├── hero-kpi-row
├── pillar-preview-cards
└── numbers-that-hold-up
```

with data access in hooks.

The exact file split remains phase-defined; the principle is to keep responsibilities legible.

---

