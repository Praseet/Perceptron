You are building the web prototype for "Adversarial Fraud Lab" (AFL), a
closed-loop red-team/blue-team GenAI payment fraud detection system, for
submission to the Mastercard Innovation Challenge @ GFF 2026. This is a
real hackathon submission with a real deadline — treat every requirement
below as load-bearing, not a suggestion.

═══════════════════════════════════════════════════════════════════
NON-NEGOTIABLE: THE ACTUAL SUBMISSION REQUIREMENTS
═══════════════════════════════════════════════════════════════════
The hackathon requires exactly three artifacts. You are only building #3,
but everything you build must serve these five judging criteria:
diversity of attacks identified · fidelity of attacks in simulation ·
detection algorithm efficacy · novelty · real-world feasibility in live
payments.

If you cannot explain how a page, feature, or design choice serves one of
those five criteria or the "closed-loop system in action" requirement,
deprioritize it. Do not add scope that doesn't serve them. Do not drop
scope that does, without asking me first.

═══════════════════════════════════════════════════════════════════
STEP 0 — DO NOT SKIP: VERIFY REAL DATA EXISTS BEFORE BUILDING ANYTHING
═══════════════════════════════════════════════════════════════════
Check the repo right now for: data/, models_artifacts/, any .pkl, any
metrics .json, any evaluation output. As of my last check, NONE of these
exist — meaning the generation + training pipeline
(src/generator/ → src/features/engineering.py → src/models/train.py)
has apparently never been run end-to-end.

If that's still true: your first job is to actually run that pipeline
(or tell me precisely what's blocking you from running it — missing API
key, missing dependency, unclear entry point, whatever it is) and produce
real output files. Do NOT proceed to build UI around numbers that don't
exist yet. If running the full pipeline isn't feasible in the time you
have, say so explicitly and we'll scope down together — but do not
paper over the gap by inventing a plausible-sounding number instead.

═══════════════════════════════════════════════════════════════════
ABSOLUTE BAN — THESE PATTERNS ARE NOT ALLOWED ANYWHERE IN THIS CODEBASE
═══════════════════════════════════════════════════════════════════
A previous attempt at this failed specifically because of these. Do not
repeat them:
- No comment or variable containing "mock", "demo", "sample", "fake",
  "placeholder", or "dummy" data. Never write `// Mock data` and then an
  array of invented transactions. If you need example rows to develop
  against before the API is wired, generate them from a documented dev
  fixture file that is clearly separate from production code paths and
  never shipped as if it were live.
- No invented metrics of any kind — no PR-AUC, precision, recall, F1,
  transaction counts, or dollar amounts typed as literals in component
  code. Every number visible in the UI must be read from a real file
  (docs/ATTACK_TAXONOMY.md, a metrics/eval output file, a live API
  response) — trace each one back to its source before you use it.
- No fraud-type names, attack labels, or entity IDs invented from
  imagination ("Velocity Attack", "Proxy IP Usage", etc.). The real fraud
  types are defined in the codebase (account_takeover, ai_impersonation,
  auth_bypass, bustout_identity, card_testing, synthetic_identity,
  bnpl_abuse) and the real attack taxonomy is in
  docs/ATTACK_TAXONOMY.md — read these files, don't guess at what they
  contain.
- No navigation link to a page that doesn't have real content. If you
  run out of time before a page is real, remove it from the nav rather
  than link to "Coming soon" — a dead-looking placeholder page reads
  worse in front of judges than a smaller, complete app.
- No declaring a task done based on the dev server starting. `npm run
  dev` does not type-check. You must run the actual production build
  command and confirm a clean exit code before saying anything is
  finished.

═══════════════════════════════════════════════════════════════════
USE YOUR FRONTEND TOOLS/SKILLS — THIS IS NOT OPTIONAL
═══════════════════════════════════════════════════════════════════
Before writing a single line of UI code, inventory every frontend-related
skill, MCP tool, design tool, browser/preview tool, or component library
you have access to. These exist specifically to get you past a generic
default look — use them at every stage, not just once at the start:
- Before deciding on layout/visual direction for EACH page, consult
  whatever design-guidance skill you have for how to approach it.
- If you have any way to actually render/screenshot what you've built,
  use it after every meaningful change — don't just read your own JSX
  and assume it looks right.
- If a tool or skill you'd expect to have for this kind of work is
  missing, tell me explicitly, by name, rather than quietly working
  around the gap. I want to know your real capability ceiling.
Treat "I didn't use an available tool that could have improved this" as
a failure condition on the same level as a build error.

═══════════════════════════════════════════════════════════════════
DESIGN DIRECTION — ALREADY AGREED, DO NOT SILENTLY CHANGE IT
═══════════════════════════════════════════════════════════════════
This is a security/fraud-defense product. The agreed direction is a dark,
cybersecurity-native visual language synthesizing:
- Darktrace: dark background, restrained high-contrast accent reserved
  for threat/alert states, network/graph visualization for entity
  relationships (directly relevant — device-sharing and fraud-ring
  connections in the data are literally a graph).
- Datadog: information-dense real-time monitoring layout — many live
  numbers, legible via strict grid/card discipline, not clutter.
- Stripe: typographic confidence, generous whitespace, purposeful
  (not decorative) motion.
A previous attempt silently swapped this for a light, generic
Notion/Stripe-only palette without asking. Do not do that. If you think
there's a genuinely better direction, propose it and ask — do not just
build it and hope I don't notice.

Concretely, this means: a real dark-mode-first token system (not a
light palette with a dark mode bolted on), a single committed color/type
system used identically across every page (same card pattern, same
spacing scale, same motion timing everywhere), and enough restraint that
nothing feels decorative-for-its-own-sake. Genuinely study what makes
Stripe/Datadog/Darktrace NOT look like a template — it's typically:
unusual but legible type scale, asymmetric/considered layout rather than
centered generic grids, one confident accent color used sparingly, and
motion that communicates state change rather than just being present.

═══════════════════════════════════════════════════════════════════
ARCHITECTURE — SCALABLE, MINIMAL, NOT GENERIC
═══════════════════════════════════════════════════════════════════
- Real data layer: a typed API client in src/lib (one place all fetches
  go through, not scattered per-component fetch calls), custom hooks in
  src/hooks built on @tanstack/react-query for every piece of live data,
  and if react state needs to be shared across components, use zustand
  in src/stores deliberately — don't leave these directories empty while
  the dependencies sit unused in package.json.
- Backend: a thin FastAPI service wrapping the EXISTING trained model
  and feature-building code in src/ — do not reimplement fraud detection
  logic in JavaScript. The frontend calls this API; it does not simulate
  it.
- Code must be minimal, not sprawling: shared primitives (Card, Badge,
  RiskScore, DataTable, MetricStat) reused across every page, not
  hand-rolled markup repeated per page. No dead imports, no duplicate
  styling approaches (pick ONE way to apply a semantic color — either a
  Tailwind class or an inline CSS variable, never both on the same
  element for the same purpose).
- Every page must be reachable and real before you move to the next.
  Priority order, ranked against the judging criteria — do these in
  order, and do not start a later one before an earlier one is complete
  and verified:
  1. Overview/Dashboard — real-world feasibility, first impression
  2. Attack Taxonomy browser — diversity of attacks identified (pull
     every entry from docs/ATTACK_TAXONOMY.md, not a 5-row sample)
  3. Live Model Demo — detection algorithm efficacy, must call the real
     API and real model, not a client-side heuristic
  4. Model Performance detail — detection algorithm efficacy, real
     metrics only
  5. Fraud Ring / Attack Graph (reactflow) — novelty, this is the
     closed-loop story made visible
  6. Feedback Loop view — fidelity + the explicit "closed-loop system in
     action" requirement
  Investigations/Rules/Settings are lower priority — only build them if
  1-6 are genuinely complete, and if you don't get to them, remove them
  from navigation rather than ship a dead link.

═══════════════════════════════════════════════════════════════════
WHEN UNSURE, ASK — DO NOT GUESS AND MOVE ON
═══════════════════════════════════════════════════════════════════
Ask me before: changing the agreed design direction, changing page scope
from the priority list above, or proceeding when you can't find a real
data source for something the UI needs to show. Batch questions where
you can, but a structurally important unknown does not get silently
resolved with your best guess.

═══════════════════════════════════════════════════════════════════
BEFORE YOU DECLARE ANYTHING DONE — RUN THIS CHECKLIST AND SHOW ME PROOF
═══════════════════════════════════════════════════════════════════
1. Run the actual production build command. Paste the real output.
   Exit code must be 0. Not "it should work" — show me it worked.
2. Grep your own codebase for: "mock", "demo", "sample", "fake",
   "placeholder", "dummy", "Coming soon". Paste the output. It must be
   empty (aside from legitimate uses like a real placeholder="" input
   attribute).
3. For every nav link, confirm it renders real, non-empty content —
   list each page and what real data source it's reading from.
4. Confirm the Live Demo page's prediction actually calls your FastAPI
   backend and your real trained model — not a client-side formula.
5. Only after all four of the above are true, tell me it's done, and
   show me what's left unbuilt (if anything) honestly rather than
   implying full scope was reached if it wasn't.