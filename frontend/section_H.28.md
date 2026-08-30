# H.28 Legacy frontend quarantine rule

The supplied repository contains an older frontend implementation with files resembling:

```text
frontend/src/components/Sidebar.tsx
frontend/src/components/Header.tsx
frontend/src/components/Card.tsx
frontend/src/components/RiskScore.tsx
frontend/src/pages/Dashboard.tsx
```

That implementation is **not** to be evolved into the final AFL site.

Specific legacy characteristics that must not survive into the final implementation:

```text
Sidebar
FraudGuard wordmark
Dashboard / Investigations / Rules / Models nav
gradient card fills
glass card variant
hover lift
gradient text
fake hardcoded dashboard metrics
old color tokens such as --color-bg-0 / --color-bg-1
```

Delete or replace the legacy implementation as instructed by Phase 0. Do not merge it with the new architecture.

---

