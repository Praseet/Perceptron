# H.44 Cline execution protocol

Cline should execute each phase in this exact order:

## Step A — read

Before editing:

```text
README.md
docs/FRONTEND_VISION.md
frontend/PROGRESS.md
relevant phase
Appendix H sections relevant to that phase
```

Then inspect the actual files named in the phase.

---

## Step B — reconcile

Before writing code:

- identify any ambiguity,
- look for an existing repo implementation,
- decide from the authority order,
- avoid asking a question when Appendix H already answers it.

---

## Step C — implement the smallest complete change

Do not prematurely implement future phases.

Do not add:

```text
new page
new abstraction
new dependency
new design token
new backend feature
```

unless the current phase or an explicitly documented contract completion requires it.

---

## Step D — run the app

Use the actual dev server.

Do not rely exclusively on:

```text
TypeScript compile
```

because visual and interaction errors can survive type-checking.

---

## Step E — inspect the browser

For relevant phases:

```text
desktop screenshot
mobile screenshot
console
network
computed styles
keyboard navigation
```

Use Playwright or browser tooling available to Cline.

---

## Step F — verify against acceptance criteria

Do not write:

```text
all criteria passed
```

unless each criterion was actually checked.

The existing project requires evidence-oriented `PROGRESS.md` entries.

---

## Step G — append progress

Record:

```text
files
deviations
verified criteria
known issues
```

Never rewrite old entries.

---

