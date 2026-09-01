# AFL — Reliability, One-Click Launcher & Bugfix Implementation Spec

**Audience:** an AI coding agent (Cline, Claude Code, etc.) working directly in
the `Praseet/Perceptron` repo, on the machine that has the real local working
tree (including files that are NOT yet pushed to GitHub).

**Revision note (this version):** the original spec asked the agent to
*investigate* whether certain files existed locally-but-uncommitted. That
investigation has now been done directly against the actual local working
tree and the actual GitHub state. Section 0 and the "Confirmed" callouts in
P0/P1 below are empirical findings, not hypotheses — treat them as verified
facts, not things to re-derive from scratch. Everywhere else in the doc, the
original author's claims were spot-checked against the real source files and
matched exactly; those sections are unchanged except for added Task IDs and
a status-log convention.

**How to work through this doc:** run Section 0 first, always. Then fix P0–P8
in order, each gated on the previous one's Acceptance Test passing. Each
section has Problem / Evidence / Exact Fix / Acceptance Test. Do not skip an
Acceptance Test — run it and confirm it passes before moving to the next
section. Do not redesign, restyle, or "improve" anything not listed here. Do
not touch the visual design system, color tokens, animation timing, or
component APIs beyond what each fix requires. Keep diffs minimal and scoped.

**Status log (new):** after each numbered task (`[T0.1]`, `[P0]`, `[P1]`, …)
finishes — pass or fail — append one line to `AGENT_PROGRESS_LOG.md` at the
repo root: `<UTC timestamp>  <task id>  <PASS|FAIL>  <one-line note>`. Create
the file if it doesn't exist. This is so the run is resumable and auditable
if the agent session is interrupted mid-spec; it is not itself an
acceptance-test requirement for any section, just do it as you go.

---

## Section 0 — Repo/Local-Tree Reconciliation Audit (run first, before P0)

**Why this exists:** this spec makes several "file X does not exist in the
repo" claims. Those claims are about what's on GitHub, not about what's on
this machine. A direct audit (done while preparing this revision) already
found **two confirmed cases** where a file the spec discusses is missing from
GitHub but is present, complete, and substantial in the local working
tree — meaning the correct move is reconciliation (commit / merge / extend),
not "write it from scratch." Do not assume any other "missing" claim in this
doc is actually missing locally until you've checked. This section makes
that check systematic instead of ad hoc.

**[T0.1] Enumerate every untracked and modified path.** At the repo root:
```bash
git status --porcelain=v1
git ls-files --others --exclude-standard   # untracked, respecting .gitignore
git diff --name-only                        # tracked but modified, uncommitted
git diff --cached --name-only               # staged but uncommitted
```
Save the combined output — you'll cross-reference it against every fix
section below before acting on any "does not exist" claim.

**[T0.2] Confirmed finding #1 — `frontend/src/design-system/patterns/loop-flow-scene.tsx`.**
This file exists locally right now: **1,013 lines**, a real, complete
`LoopFlowScene` component (not a stub). It is untracked — `git log --all
--diff-filter=A --name-only -- '**/loop-flow-scene.tsx'` returns nothing
because it has never been committed, ever, on any branch. This is the exact
file P0 below is about. Do not recreate it; it already exists. The fix is
`git add` + commit, after resolving the dead `LoopDiagram` export (see P0).

**[T0.3] Confirmed finding #2 — `preflight_check.py`.** This file also
already exists locally at the repo root (not just "missing," as P1's
original problem statement assumed) and is untracked. It is a real,
working preflight script — but it implements a **different, older CLI
contract** than the one P1 specifies (different exit codes, no `--yes`
flag, no Phase 4 data/model generation, no `.env` writing, no `y/n` prompts,
different final-line text). Full gap analysis is in the rewritten P1 below.
**Do not blindly overwrite this file** — it has real, correct logic
(package-name→import-name mapping, node/npm checks, import smoke test) that
should be preserved and extended, not discarded.

**[T0.4] For every other "does not exist" or "is missing" claim in P2–P8,**
grep the audit output from T0.1 for that filename before acting. If a file
the spec says to create already exists locally (tracked or untracked),
treat that as a merge/extend task and note the discrepancy in
`AGENT_PROGRESS_LOG.md`, rather than silently overwriting it.

**[T0.5] Root-level untracked-file inventory.** Beyond the two files above,
the repo root's local working tree has ~75 additional untracked files that
are *not* covered by any `.gitignore` rule and are not obvious build/log
noise (that noise — `*.log`, `dev.err`, `*.tsbuildinfo`, `test-results/`,
etc. — is correctly gitignored already and can be ignored here). These fall
into two buckets; **do not delete or commit any of them without asking** —
just produce the categorized list as a comment block at the top of
`AGENT_PROGRESS_LOG.md` for the user to triage:

- **Likely-real, undocumented content** (worth asking the user whether to
  commit): `AFL_BACKEND_ML_FIXES_AND_ENHANCEMENTS (1).md`, the six
  `phase12-*.png` screenshots, `apply_best_model.py`, `build_manifest.py`,
  `backend_smoke_test.py`, `_check.py` / `_check_history.py` /
  `_check_perclass.py`, `_launch.bat`, `test_health.bat`, `test_launch.bat`.
- **Likely scratch/debug debris** (worth asking the user whether to delete
  or add explicit `.gitignore` rules for, so `git status` stops being noisy):
  in `frontend/`, the ~50 `section_H.*.md` fragment files, `h65.md` /
  `h67.md` / `h68.md`, `home-test.html`, `lfs-check*.html`,
  `extract-viz.py`, `fix_selectors.py`, `inspect_tables.py`,
  `anti-pattern-audit.ps1`, `afl_phase12_signature_motion_and_polish_v4.md`
  (136 KB) — these look like intermediate artifacts from a prior audit/
  report-generation pass, not source the app depends on. Verify nothing in
  `frontend/src` imports or reads any of them before suggesting deletion
  (`grep -rn` each basename against `frontend/src`).

**[T0.6] `.gitignore` sanity check.** Confirm the root `.gitignore` already
covers `frontend/*.log`, `frontend/dist/`, `frontend/test-results/`,
`frontend/*.tsbuildinfo`, `frontend/*.zip`, `frontend/*.report.html`,
`.env`, `models_artifacts/*.joblib|*.pkl`, `data/processed/` — it does,
verified. No changes needed to `.gitignore` for the noise category; the
finding in T0.5 is about files *not* covered by any existing rule.

**Acceptance test:** `AGENT_PROGRESS_LOG.md` exists with the T0.1 audit
output summarized and the T0.5 categorized list present as a comment block,
before any P0 code change is made.

---

## P0 — Repo/local-tree sync check (do this first, it blocks everything else)

**Problem — confirmed, not hypothetical (see T0.2):**
`frontend/src/design-system/patterns/index.ts` contains:
```ts
export { LoopDiagram } from "./loop-diagram";
```
`frontend/src/design-system/patterns/loop-diagram.tsx` **does not exist,
locally or on GitHub** — confirmed absent from both the working tree and
`git log --all --diff-filter=A --name-only` (it was deleted in commit
`4882040` and never recreated). Separately,
`frontend/src/features/home/hero.tsx` and
`frontend/src/features/loop/loop-page.tsx` both do:
```ts
const LoopFlowScene = lazy(() =>
  import("../../design-system/patterns/loop-flow-scene").then((m) => ({
    default: m.LoopFlowScene,
  })),
);
```
`loop-flow-scene.tsx` **is confirmed present locally** (1,013 lines, real
component, exports `LoopFlowScene`) **and confirmed absent from every commit
on GitHub** (T0.2). This means the code currently on GitHub cannot build a
working frontend for anyone who clones it fresh — `index.ts` has a dead
import, and the two pages that show the signature loop animation import a
file that exists only on this machine. The demo works locally purely because
of this one untracked file.

**Also confirmed:** no file anywhere in `frontend/src` renders `<LoopDiagram
...>` as JSX — the only references to the string `LoopDiagram` are the dead
export line itself and a handful of comments (`icons.ts`, `index.css`,
`hero.tsx`). There is no live consumer to preserve.

**[P0.1] Exact fix (steps 1–3 are now direct actions, not investigation —
the investigation is done):**
1. Stage the real file: `git add frontend/src/design-system/patterns/loop-flow-scene.tsx`.
2. Delete the dead export line from
   `frontend/src/design-system/patterns/index.ts`:
   ```diff
   -export { LoopDiagram } from "./loop-diagram";
   ```
   (Confirmed safe — no JSX consumer exists anywhere in `frontend/src`; this
   was re-verified with `grep -rn "<LoopDiagram" frontend/src` returning no
   hits, in addition to the general `LoopDiagram` grep.)
3. Run `git log --all --diff-filter=A --name-only -- '**/loop-diagram.tsx'
   '**/loop-flow-scene.tsx'` after committing, to confirm `loop-flow-scene.tsx`
   is now tracked and `loop-diagram.tsx` correctly stays untracked/absent
   (it should never be recreated — it's dead).
4. Do a clean-clone smoke test: `git clone <repo> /tmp/afl-clean-test && cd
   /tmp/afl-clean-test/frontend && npm install && npm run build`. This must
   succeed with zero module-resolution errors. This is the real acceptance
   bar — "works on my machine" is not sufficient, it must work from a fresh
   `git clone`.
5. Commit and push. Do not proceed to any other section until this succeeds.

**Acceptance test [P0]:** `npm run build` succeeds from a completely fresh
`git clone` of the pushed branch, with no missing-module errors.

---

## P1 — `preflight_check.py` (the launcher's missing brain)

**Problem — revised per T0.3.** `start.cmd` (repo root) calls
`preflight_check.py`:
```bat
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%ROOT%preflight_check.py"
) else (
    py -3 "%ROOT%preflight_check.py"
)
if errorlevel 1 goto :need_fix
...
"%ROOT%.venv\Scripts\python.exe" "%ROOT%preflight_check.py" --install
```
`start.cmd`'s own comments describe the intended contract precisely: *"Runs
preflight_check.py, offers to auto-install missing Python / frontend deps
(with '*' progress), and only starts the stack when ENVIRONMENT READY."*
**A version of this file already exists locally, untracked, at the repo
root** (confirmed in T0.3) — it is not a stub, it's ~300 lines of working
logic. It is missing from GitHub, so a fresh clone still fails at the first
preflight call exactly as the original problem statement described, but the
fix is **reconcile the existing script against the contract below**, not
write a new one from a blank file.

**Gap analysis — existing local script vs. the contract this section
specifies:**

| Area | Existing local script | Contract needed |
|---|---|---|
| `--yes` flag for non-interactive confirm | Not present | Required |
| `y/n` prompts before installing | Not present — installs unconditionally when `--install` is passed | Required (unless `--yes`) |
| Phase ordering / labeling | Checks are unlabeled, run together | Required: `[Phase i/5] <name>` header per phase |
| Phase 4 (data/model generation) | **Entirely absent** — only checks `models_artifacts/*` and `data/processed/*` as static artifact paths, never runs `run_pipeline.py` / `train.py` / `anomaly.py` to generate them | Required — this is the actual functional gap, not just a contract-compliance gap: a fresh clone with this script alone still can't self-heal past "artifacts missing" |
| Phase 5 (`frontend/.env` generation) | Not present | Required |
| `*` progress heartbeat while installing | **Already present and correct** (`install_python_deps`, `install_frontend_deps` both do this via `Popen` + poll loop) — keep as-is | — |
| Import-name mapping for packages whose dist name ≠ import name | **Already present and more complete than the spec anticipated** (`IMPORT_NAMES` dict covers `scikit-learn`→`sklearn`, `imbalanced-learn`→`imblearn`, etc.) | Keep as-is, extend if Phase 2's package diff needs it |
| Node/npm check | **Already present** (`check_node`) | Keep as-is |
| Backend import smoke test | **Already present** (`check_import_smoke`) — a nice-to-have beyond the original contract | Keep as-is |
| Exit codes | `0`=ready, `1`=python missing, `2`=python deps failed, `3`=frontend deps failed, `5`=general preflight failure (no `4` currently used) | The contract below only requires `0`=ready / nonzero=not-ready, since `start.cmd` uses `if errorlevel 1` (true for *any* nonzero code) — **the existing multi-code scheme is compatible, keep it**, just make sure the new Phase 4 failure path returns a nonzero code too (use `4`, currently unused, for "artifacts/data-pipeline failed") |
| Final line text | Prints `ENVIRONMENT READY` or `PREFLIGHT FAILED` | Contract wants `ENVIRONMENT READY` / `ENVIRONMENT NOT READY` exactly — **small rename needed**, `PREFLIGHT FAILED` → `ENVIRONMENT NOT READY` |

**[P1.1] Exact fix — extend the existing `preflight_check.py` in place:**
1. Add an `argparse` (or simple `sys.argv` check, matching the file's
   existing style) for `--yes` alongside the existing `--install` check.
2. Wrap each existing check with a `[Phase i/5] <name>` header print, per
   the Output format requirements below, and renumber to 5 phases total
   (venv, Python packages, frontend packages, data/model artifacts, `.env`).
3. Before any `--install` action, if `--yes` is not set, prompt
   `input("... [Y/n] ")` and only proceed on empty/`y`/`Y`. If `--yes` is
   set, skip the prompt and proceed.
4. **Add Phase 4 as new logic** (this phase doesn't exist in the current
   script at all): check whether `data/processed/X_test.pkl`,
   `models_artifacts/xgboost_tier1.json`, and
   `models_artifacts/isolation_forest_tier2.joblib` all exist — **read these
   three paths from `src/config.py`'s `X_TEST_PKL`, `XGB_TIER1_JSON`,
   `ISO_FOREST_TIER2_JOBLIB` constants**, do not hardcode strings that could
   drift from config (this codebase already has an `ARTIFACTS` list
   hardcoded as strings — replace those three entries with the config-driven
   values, the other three paths in that list can stay as literals since
   they're not exposed as named config constants). On install, run in this
   exact sequence, each its own subprocess with its own `[Step i/3] <name>…`
   label and `*` heartbeat:
   1. `<venv_python> run_pipeline.py`
   2. `<venv_python> src/models/train.py`
   3. `<venv_python> src/models/anomaly.py`
   Stop immediately and print the last ~20 lines of stderr if any step
   fails; do not run later steps against a partially-generated dataset.
5. **Add Phase 5** (also entirely new): if `frontend/.env` doesn't exist,
   write it directly (no prompt — it's a 2-line config file, not an
   install):
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_DEMO_MODE=false
   ```
   matching what `start.ps1` already does.
6. Rename the final-line string from `PREFLIGHT FAILED` to
   `ENVIRONMENT NOT READY`; keep `ENVIRONMENT READY` as-is.
7. Use exit code `4` for a Phase 4 (data/model pipeline) failure — currently
   unused in the existing scheme, keeps the rest backward-compatible.
8. Everything else in the existing file (`IMPORT_NAMES`, `check_python`,
   `check_deps`, `check_node`, `install_python_deps`,
   `install_frontend_deps`, `check_import_smoke`) is correct and
   contract-compliant already — do not rewrite it, only wire it into the
   new phase-numbered, prompted, `--yes`-aware flow.

### Output format requirements
- Every phase prints a one-line header like `[Phase 2/5] Python packages`
  before its check, and a final `[OK]` or `[MISSING]`/`[FAILED]` line after.
- The final line of check-only mode must be exactly one of:
  `ENVIRONMENT READY` (all phases OK) or `ENVIRONMENT NOT READY` (at least
  one phase missing).
- Exit codes: `0` = ready (check mode) or install succeeded fully (install
  mode); nonzero = not ready / install failed partway (`start.cmd` only
  checks `errorlevel 1`, i.e. any nonzero, so the existing multi-value
  scheme — 1/2/3/4/5 for different failure phases — is fine to keep for
  human-readable diagnosis).

**Acceptance test [P1]:** On a machine with no `.venv`, no `node_modules`,
and no `data/`/`models_artifacts/` contents: `python preflight_check.py`
reports `ENVIRONMENT NOT READY` and exits nonzero, listing all 5 phases
correctly (not 4 — Phase 5's `.env` check counts too). `python
preflight_check.py --install --yes` then completes all phases with visible
`*` progress and no silent multi-second gaps, and a subsequent `python
preflight_check.py` reports `ENVIRONMENT READY` and exits `0`. Separately,
confirm the *interactive* path: `python preflight_check.py --install`
(no `--yes`) actually pauses for a `y/n` answer before each install action.

---

## P2 — Cross-platform launcher parity + small script fixes

**[P2.0] Before starting, re-check T0.1's output** for `start.sh`,
`stop.cmd`, `stop.sh` — none of the three exist locally or on GitHub
(confirmed), so this section is a clean create, no reconciliation needed.

**Problem 1:** `start.ps1` and `start.cmd` are Windows-only (PowerShell /
cmd). There is no equivalent for macOS/Linux, so "someone using this repo on
their local machine" with a non-Windows OS has no one-click option at all.

**Problem 2 (small but real):** `start.cmd`'s header comment says `Stop with:
stop.cmd`, but only `stop.ps1` exists — there is no `stop.cmd`. Confirmed:
`stop.cmd` is absent both locally and on GitHub.

**Problem 3:** `start.ps1` installs Python deps with a hardcoded inline list
that is missing several packages the backend actually needs at runtime:
```powershell
& $venvPython -m pip install --quiet fastapi uvicorn pydantic numpy pandas scikit-learn xgboost joblib
```
This omits `shap` (imported by `/api/predict`'s explainability path — see
`src/api/main.py` `_get_shap_explainer()`), plus `imbalanced-learn`,
`openai`, `ctgan`, `torch`, `lightgbm`, `python-dotenv`, `matplotlib` from
`requirements.txt` — **confirmed**, all of these are present in the local
`requirements.txt` and absent from this hardcoded `pip install` line. A user
who only ever runs `start.ps1` (never `pip install -r requirements.txt`
directly) will hit a live `ImportError` the first time a prediction needs a
SHAP explanation.

**[P2.1] Exact fix:**
1. Add `stop.cmd` — a thin wrapper equivalent to `stop.ps1`'s port-kill logic
   (kill whatever is listening on 8000 and 5173, same as the cleanup block
   already in `start.cmd`'s `:launch` section — reuse that exact netstat/
   taskkill pattern instead of writing new logic).
2. Rewrite `start.ps1`'s dependency-install block to **call
   `preflight_check.py --install`** instead of its own hardcoded pip list,
   so there is exactly one source of truth for "what needs installing" (P1).
   Keep the rest of `start.ps1` (port cleanup, starting uvicorn/vite,
   waiting for health, opening the browser) as-is — it's fine.
3. Add `start.sh` for macOS/Linux, mirroring `start.cmd`'s logic:
   - Resolve repo root (`cd "$(dirname "$0")"`)
   - Run `.venv/bin/python preflight_check.py` (create `.venv` first via
     `python3 -m venv .venv` if it doesn't exist, matching `start.ps1`'s
     bootstrap behavior) — if not ready, prompt `y/n`, then run
     `preflight_check.py --install`
   - Kill anything on ports 8000/5173 (`lsof -ti:8000 | xargs kill -9
     2>/dev/null`, same for 5173)
   - Start `uvicorn src.api.main:app --port 8000 --host 127.0.0.1` and `npm
     run dev --prefix frontend`, each backgrounded with output redirected to
     `backend.log` / `frontend/dev.log` (same log file names `start.cmd`
     already uses, for consistency)
   - Poll `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health`
     until it returns `200` (timeout ~80s, matching `start.cmd`'s 40 retries
     × 2s), same for `http://127.0.0.1:5173/`
   - Open the browser (`open` on macOS, `xdg-open` on Linux — detect via
     `uname`)
   - `chmod +x start.sh`
4. Add `stop.sh` mirroring `stop.cmd`'s port-kill for macOS/Linux
   (`lsof -ti:8000,5173 | xargs kill -9 2>/dev/null`).

**Acceptance test [P2]:** On Windows, `start.cmd` still works end-to-end and
`stop.cmd` cleanly kills both servers. On macOS/Linux, `bash start.sh` takes
a machine with nothing set up all the way to a running demo at
`http://127.0.0.1:5173/`, and `bash stop.sh` cleanly stops both servers.

---

## P3 — `requirements.txt` missing `fastapi` / `uvicorn`

**Problem — confirmed directly against the local file.**
`requirements.txt` (35 lines, checked in full) has no `fastapi`, `uvicorn`,
or `python-multipart` line at all, despite `src/api/main.py` being a FastAPI
app started via `uvicorn` in every launcher script. Anyone running `pip
install -r requirements.txt` verbatim (the README's own instruction) gets a
backend that fails to import.

**[P3.1] Exact fix:** add these three lines to `requirements.txt` (the
existing file isn't alphabetized, so exact position doesn't matter,
presence does):
```
fastapi==0.121.0
uvicorn[standard]==0.38.0
python-multipart==0.0.20
```
Pin to whatever versions are actually compatible with the `pydantic==2.13.4`
already pinned in the file — verify with `pip install` in a scratch venv
before committing the pins, don't guess blindly.

**Acceptance test [P3]:** `pip install -r requirements.txt` into a brand-new
empty venv, then `python -c "import fastapi, uvicorn"` succeeds with no
error, and `uvicorn src.api.main:app --port 8000` boots without
`ModuleNotFoundError`.

---

## P4 — Hardcoded "1,390 attacks" KPI (wrong when no data is loaded)

**Problem — confirmed directly against the local file.**
`frontend/src/features/home/hero-kpi-row.tsx` line 26:
```ts
const ATTACKS_GENERATED_TOTAL = 1_390;
```
used at line 88 as `value={ATTACKS_GENERATED_TOTAL}` inside a `<KpiTile
label="Attacks generated" .../>`. This is a pure JS constant — it is shown
regardless of what the backend actually reports. The backend's
`_system_status()` in `src/api/main.py` correctly returns zeros when no data
is generated, but the frontend never reads any equivalent field for this
particular tile — confirmed no `n_attacks_generated` reference exists
anywhere in `hero-kpi-row.tsx` today.

**Exact fix — two parts:**

**Part A — backend: add a real, data-derived field.** In
`src/api/main.py`, inside `_system_status()`, compute the actual number of
generated attack cases from the real generation log, not from the static
`FRAUD_TYPE_TARGETS` config sum. Add a helper alongside the existing
`_load_lazy`-style loaders:
```python
def _generation_log_df():
    from config import GENERATION_LOG_CSV
    if not Path(GENERATION_LOG_CSV).exists():
        return None
    try:
        return pd.read_csv(GENERATION_LOG_CSV)
    except Exception as exc:
        print("[backend] failed to load generation log: " + str(exc), file=sys.stderr)
        return None
```
Then in `_system_status()`, add:
```python
gen_log = _generation_log_df()
n_attacks_generated = int(len(gen_log)) if gen_log is not None else 0
```
and add `"n_attacks_generated": n_attacks_generated,` to **both** return
statements in `_system_status()` (the early-return-on-no-data branch at the
top, where it should be `0`, and the main return at the bottom, where it
should be the real count). Add `n_attacks_generated: number` to the
`SystemStatus` interface in `frontend/src/lib/api/types.ts` (near the
existing `n_transactions` / `n_transactions_total` fields), matching the
naming convention already used there.

**Part B — frontend: consume the real field.** In
`hero-kpi-row.tsx`, delete the `ATTACKS_GENERATED_TOTAL` constant and its
comment block entirely, and change:
```tsx
<KpiTile
  label="Attacks generated"
  value={ATTACKS_GENERATED_TOTAL}
  direction="up-is-good"
  format={(n) => n.toLocaleString("en-US")}
/>
```
to:
```tsx
<KpiTile
  label="Attacks generated"
  value={status.data.n_attacks_generated}
  direction="up-is-good"
  format={(n) => n.toLocaleString("en-US")}
/>
```
Also check `frontend/src/lib/demo-data/` (the `VITE_DEMO_MODE=true` fixture
path) for a hardcoded `getSystemStatus()` mock — if it exists, give it a
sensible fixed `n_attacks_generated` value there too (demo mode is supposed
to show canned-but-plausible numbers, that's a different, legitimate case
from the live-mode bug being fixed here — don't remove the demo-mode
fixture, just make sure it has this field so TypeScript doesn't break).

**Acceptance test [P4]:** Start the backend against an empty `data/`
(`rm -rf data/processed models_artifacts/*.pkl models_artifacts/*.joblib`
temporarily, or just test against a machine that hasn't run Phase 4 of P1
yet) — the homepage must show `Attacks generated: 0`, not `1,390`. After
running the real pipeline (P1 Phase 4), the homepage must show the actual
`len(generation_log.csv)` row count, and that number must match what you get
from `wc -l data/raw/generation_log.csv` (minus the header row).

---

## P5 — Defend page "freeze" (button state decoupled from real request)

**Problem — confirmed directly against the local files.**
`frontend/src/features/defend/transaction-builder-form.tsx` line 262:
```tsx
<Button type="submit" ... disabled={form.formState.isSubmitting} aria-label="Predict">
```
`form.formState.isSubmitting` (react-hook-form) is only `true` while the
form's own `onSubmit` handler is executing. In
`frontend/src/features/defend/defend-page.tsx`, `handleSubmit` (line 60) is
synchronous — it calls `predict.mutate(tx, {...})` (fire-and-forget), not
`.mutateAsync()` (awaited), and returns immediately. So
`form.formState.isSubmitting` flips back to `false` essentially instantly,
re-enabling the submit button, while the actual network request (which
includes a cold-start SHAP explainer load + large pickled dataframe access
the first time — see `_get_shap_explainer()` and `_load_lazy()` in
`src/api/main.py`, both lazily initialized on first use) is still in flight.
`ProbabilityGaugeProps` (confirmed, `probability-gauge.tsx` line 14) has no
`isLoading` field today — the gauge has no loading state at all, it just
keeps displaying the previous result. Net effect: user clicks Predict, the
button looks immediately clickable again, nothing on the page visibly
changes for 2–5 seconds, then results pop in. This reads as "frozen," not
"loading."

**Exact fix — four parts:**

**Part A — tie the button to the real mutation state.** In
`transaction-builder-form.tsx`, the form needs to know about
`predict.isPending` from the parent. Add a prop:
```tsx
type TransactionBuilderFormProps = {
  onSubmit?: (tx: TransactionRowWithId) => void;
  isSubmitting?: boolean; // NEW
  // ...existing props
};
```
and use it for the button:
```tsx
<Button
  type="submit"
  variant="primary"
  size={isCompact ? "sm" : "md"}
  disabled={form.formState.isSubmitting || isSubmitting}
  aria-label="Predict"
>
  {isSubmitting ? <Loader2 aria-hidden className="animate-spin" /> : null}
  {isSubmitting ? "Scoring…" : "Predict"}
</Button>
```
(Match whatever the existing button's current label/icon pattern is — check
the file for how other buttons in this codebase show a pending label, e.g.
`generate-controls.tsx`'s `controls.isStreaming ? <Loader2 /> : <Sparkles
/>` pattern, and mirror that exact style for consistency rather than
inventing a new one.)

**Part B — pass it from the parent.** In `defend-page.tsx`:
```tsx
<TransactionBuilderForm onSubmit={handleSubmit} isSubmitting={predict.isPending || pendingTx != null} />
```

**Part C — give `ProbabilityGauge` a loading state too** — confirmed it
needs adding, `ProbabilityGaugeProps` currently only has `probability` and
`className`. Add `isLoading?: boolean` to the interface and render a
pulsing/skeleton state on the gauge needle while it's true, then pass it
from `defend-page.tsx` (which already computes this exact boolean for the
`ShapWaterfall` at line 111 — reuse it, don't recompute):
```tsx
<ProbabilityGauge
  probability={lastPrediction?.prediction.probability ?? null}
  isLoading={predict.isPending || pendingTx != null}
/>
```

**Part D — kill the cold-start delay at its source, not just paper over
it with a spinner.** In `src/api/main.py`'s `@app.on_event("startup")`
handler, after the existing model-loading code, eagerly warm the lazy
caches instead of waiting for the first user request to pay for them:
```python
@app.on_event("startup")
def _startup():
    global SERVICE, XGB_MODEL
    try:
        SERVICE = FraudInferenceService(...)
        SERVICE.initialize()
        XGB_MODEL = xgb.XGBClassifier()
        XGB_MODEL.load_model(XGB_TIER1_JSON)
        # NEW: warm the lazy caches now, not on the user's first click.
        _test_df()
        _x_test()
        _get_shap_explainer()
    except Exception as exc:
        print("[backend] startup failed: " + str(exc), file=sys.stderr)
        SERVICE = None
```
This moves the multi-second cost to backend boot time (which the launcher
already waits out via the `/api/health` polling loop in `start.cmd`/
`start.ps1`/the new `start.sh`) instead of the user's first interaction.
Note: this only helps if the artifacts already exist — if P1 Phase 4 hasn't
run yet, `_test_df()` will still return `None` here (caught safely by the
existing `_load_lazy` None-check), so this is purely additive and doesn't
introduce a new startup failure mode.

**Acceptance test [P5]:** After Part D, `curl http://127.0.0.1:8000/api/health`
immediately after the server finishes booting should be followed by a
`/api/predict` call that returns in well under 1 second (previously the
first call after boot would take multiple seconds). After Parts A–C, click
Predict in the browser and confirm: the button visibly shows a pending
state (label change + spinner) for the full duration of the request, the
probability gauge shows a loading state too, and the button does not become
clickable again until the response (success or error) has landed.

---

## P6 — Loop page "gets darker / brightness low" — diagnostic checklist

**Problem — now actionable, since P0 resolves the source-availability
issue.** Reported symptom: the loop diagram box on `/loop` sometimes appears
darker / lower-brightness than normal. The original spec author could not
locate `loop-flow-scene.tsx`'s source because it wasn't in the pushed repo
(see P0). It's now available locally (T0.2, 1,013 lines) — inspect it
directly for this section rather than reasoning about it blind. Investigate
in this order rather than guessing at a fix:

1. **Confirm it's not the always-on `.console` wrapper by design.** Both
   `hero.tsx` and `loop-page.tsx` wrap `<LoopFlowScene>` in a `className="console"`
   div unconditionally (in both ambient and live modes) — per
   `index.css`'s own comment this is an intentional "instrument panel" look
   (`--bg-base: #06090F`, etc., darker than the page background). This is
   not a bug — don't "fix" it by removing `.console`. The reported bug is
   specifically that it *sometimes* gets darker than its own normal state,
   i.e. something changes during use, not that it's dark to begin with.

2. **Check the `Suspense` fallback background token.** Both call sites use:
   ```tsx
   fallback={<div style={{ aspectRatio: "1 / 1", background: "var(--bg-panel)", ... }} />}
   ```
   Because this fallback renders *inside* the `.console` div, `--bg-panel`
   resolves to `.console`'s redefined `#0A0E1A`, not the page's normal
   `--bg-panel`. If `LoopFlowScene` ever re-suspends after initial mount
   (e.g. if it internally uses `React.lazy`/`Suspense`-driven data fetching,
   or if a parent re-key forces a remount — check for any `key={...}` prop
   passed to `<LoopFlowScene>` that changes when `sceneMode` or `run.events`
   changes), the panel would flash back to this darker fallback color
   mid-session. Search for any `key=` prop on the `<LoopFlowScene>` JSX in
   both files.

3. **Check for a stuck opacity/glow animation inside the component itself.**
   Per prior AFL project notes, this component has a documented history of
   "renders as a black box briefly before the diagram loads" and misaligned
   node outlines — both point at animation/mount-timing issues in this
   specific component. Look for any CSS `@keyframes` or inline
   `animation`/`transition` on `opacity`, `filter: brightness(...)`, or a
   glow/pulse effect tied to loop-event timing (`run.events` from
   `use-loop.ts`). If an event-driven pulse animation's `animation-fill-mode`
   or cleanup (`clearTimeout`/`cancelAnimationFrame`) is missing, rapid
   events (e.g. from the SSE stream during a live run) could leave the
   element's opacity/brightness stuck at a mid-animation low value instead
   of resetting to 100% when the stream ends.

4. **Check for an SVG `<filter>` with a hardcoded (non-unique) `id`.** If
   the component renders something like `<filter id="glow">` and is capable
   of being mounted more than once in the DOM at the same time (e.g. during
   a route transition where the Home page's ambient instance and the Loop
   page's instance briefly coexist, or in React 18 Strict Mode's
   dev-only double-invoke), duplicate SVG filter IDs are a well-known cause
   of one instance's filter silently referencing/being overridden by the
   other, which can visually manifest as incorrect brightness. If found,
   fix by generating a unique id per instance (e.g. `useId()` from React)
   instead of a literal string.

Do not apply all four as blind changes — inspect the actual component (now
locally available), identify which mechanism is actually occurring
(reproduce it, e.g. by running several loop cycles back-to-back and
watching devtools' Elements panel for the affected node's computed
`opacity`/`filter`/`background` at the moment it looks dark), then apply the
one fix that addresses the observed mechanism.

**Acceptance test [P6]:** run at least 5 consecutive loop cycles on `/loop`
(`Run →` button repeatedly) and confirm the diagram panel's brightness stays
visually constant throughout — no flash, dip, or stuck-dark state at any
point during or between runs.

---

## P7 — README Quick Start doesn't mention any of the above

**Problem:** `README.md`'s "Quick Start – Live Demo" section jumps straight
to running `uvicorn` and `npm run dev`, silently assuming `.venv`,
`node_modules`, and all data/model artifacts already exist. It never
mentions `run_pipeline.py`, `src/models/train.py`, or `src/models/anomaly.py`
anywhere in the Quick Start flow — a new clone has no path from "just
cloned" to "servers running" documented anywhere.

**Exact fix:** replace the "Quick Start – Live Demo" section with a single
documented entry point per OS, reflecting P1/P2:

```markdown
## Quick Start

One command sets up everything (Python venv, Python packages, frontend
packages, generates the training data, trains both models) and launches the
live demo:

**Windows:** `start.cmd`
**macOS / Linux:** `bash start.sh`

First run takes several minutes (data generation + model training). Every
run after that is fast — it only regenerates what's missing. You'll be
asked before anything is installed or generated.

Stop both servers: `stop.cmd` (Windows) or `bash stop.sh` (macOS/Linux).

To check readiness without changing anything: `python preflight_check.py`
```
Keep the existing "Backend" / "Frontend" / "Demo Mode (fallback)" manual
subsections below this as an "Advanced / manual setup" section for people
who want to run steps individually — don't delete that detail, just stop
presenting it as the primary path.

**Acceptance test [P7]:** a person who has only ever read the README (not
this spec) can go from `git clone` to a working demo using only commands the
README shows them.

---

## P8 — Accessibility pass

The user asked to "improve it for user accessibility." The repo already has
a Playwright + axe-core a11y suite (`frontend/tests/e2e/`, per
`docs/FRONTEND_VISION.md` / `PROGRESS.md` references to a11y testing) — run
it (`npx playwright test` in `frontend/`, find the a11y-tagged spec files)
before and after your changes and do not introduce new violations. On top of
that baseline, apply these specific, scoped improvements tied to the fixes
above (don't do a general redesign):

1. **Loading states need to be announced, not just visible.** For every
   `isLoading`/`isPending` state touched in P5 (Predict button, probability
   gauge, SHAP waterfall), ensure the container has `aria-busy="true"` while
   loading and `aria-live="polite"` on the region that receives the result,
   so screen reader users get "Scoring…" then the verdict announced, not
   silence followed by a sudden content swap.
2. **The Predict button's loading state must not rely on the spinner icon
   alone** — the text change to `"Scoring…"` in P5 Part A already covers
   this; keep both together (icon + text), never icon-only, for any loading
   button touched by this spec.
3. **KPI tiles that can legitimately show `0`** (P4's fix means "Attacks
   generated" can now correctly be `0` when no data is loaded) must be
   visually and semantically distinguishable from a loading/error state —
   check `KpiTile`'s handling of a `0` value doesn't get treated as falsy
   anywhere (e.g. `value || "—"` patterns would incorrectly show a dash for
   a real zero — search for this pattern in `kpi-tile.tsx` and fix if
   present, since P4 makes a real `0` a normal, expected state for the
   first time).
4. **Color contrast on `.console` dark-surface text.** Since P6 may touch
   opacity/brightness inside this surface, re-verify (e.g. via the browser
   devtools contrast checker or the axe-core suite) that any text/labels
   inside `.console` panels still meet WCAG AA contrast after your P6 fix —
   don't let a brightness fix regress text legibility.

**Acceptance test [P8]:** the existing axe-core Playwright suite passes with
zero new violations compared to a pre-change baseline run.

---

## Appendix A — Full untracked-file audit (repo root, verified against live GitHub state)

This table is the actual diff between the local repo-root working tree and
`https://github.com/Praseet/Perceptron`'s `main` branch root, as of this
revision. It's provided so the agent (and the user) don't have to re-derive
it — cross-check it against T0.1's fresh `git status` output in case
anything has changed since.

**Correctly gitignored (no action needed) — all `*.log`, `dev.err`,
`start_test*.log`, `backend*.log`, `pipeline_*.log`, `push*.log`,
`resplit*.log`, `smoke_*.log`, `sweep*.log`, `preflight2*.log`, `mcp.log`,
`api_test*.log`, `if_retrain*.log`, `cold_start_run.log`, the
`cline --id *.txt` session file — ~50 files total, all match existing
`.gitignore` rules.**

**Not gitignored, not on GitHub — needs a decision (see T0.5 for the
frontend-side equivalent list):**

| File | Type | Likely disposition |
|---|---|---|
| `.env` | env config | Correctly gitignored (`.env` rule) — no action |
| `AFL_BACKEND_ML_FIXES_AND_ENHANCEMENTS (1).md` | doc, 92 KB | Ask user — looks like real content, possibly a duplicate/newer version of something already committed |
| `_check.py`, `_check_history.py`, `_check_perclass.py` | scripts | Ask user — small eval/debug helpers |
| `_launch.bat`, `test_health.bat`, `test_launch.bat` | scripts | Ask user — alternate/older launcher attempts, may predate `start.cmd` |
| `apply_best_model.py`, `build_manifest.py`, `backend_smoke_test.py` | scripts | Ask user — look like real tooling, not scratch |
| `phase12-ambient-home.png`, `phase12-defend.png`, `phase12-home-ambient.png`, `phase12-identify-strip.png`, `phase12-identify-strip2.png`, `phase12-tokens-midflight.png` | screenshots | Ask user — likely design-review artifacts; `docs/assets/` already holds the committed submission screenshots, these may be superseded WIP shots |
| `start.cmd.bak` | backup file | Safe to delete — `.bak` of a file already tracked |
| `src.zip` (present **on GitHub**, absent locally) | archive | Reverse case — ask user why this was committed as a zip when `src/` is also tracked as a real folder; possible accidental/duplicate commit worth cleaning up separately from this spec's scope |

Do not act on any row in this table without the user's confirmation — this
section is informational, matching the spec's existing principle of
"flag to the user instead of guessing" (see P0's original step 3).

---

## Final checklist (verify all before considering this done)

- [ ] Section 0: audit run, `AGENT_PROGRESS_LOG.md` created with findings
- [ ] P0: fresh `git clone` → `npm install` → `npm run build` succeeds
- [ ] P1: `preflight_check.py` and `preflight_check.py --install [--yes]`
      both work exactly per the CLI contract above (5 phases, prompts,
      `.env` write, Phase 4 pipeline run), on a fully clean machine — and
      the existing script's working logic (import-name mapping, node
      check, import smoke test) was preserved, not discarded
- [ ] P2: `start.cmd` + `stop.cmd` work on Windows; `start.sh` + `stop.sh`
      work on macOS/Linux
- [ ] P3: `pip install -r requirements.txt` + `uvicorn src.api.main:app`
      boots cleanly with no `ModuleNotFoundError`
- [ ] P4: homepage shows `Attacks generated: 0` with no data, real count
      with data
- [ ] P5: Predict button visibly reflects the real request duration; cold
      first-request latency is gone (warmed at startup)
- [ ] P6: loop diagram brightness stays constant across 5+ consecutive runs
- [ ] P7: README's Quick Start is the actual, complete, working path
- [ ] P8: axe-core suite has zero new violations
- [ ] Appendix A: untracked-file table presented to the user for triage
      (nothing deleted or committed without their say-so)
