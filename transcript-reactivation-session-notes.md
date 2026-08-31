# Session Notes — Transcript Pipeline Reactivation

> Source brief: `agent-prompt-transcript-reactivation.md`
> Owner: this session (backend). Frontend (Checkpoint 6) belongs to a different session — do not touch it.

## Decisions from the user (2026-08-31) — binding for this task

1. **Scope:** Execute **Checkpoints 1–5 only** (backend pipeline). Checkpoint 6
   (frontend transcript display) is explicitly OUT of scope — the other session
   owns frontend work. Do not modify anything under `src/features/generate/` or
   any frontend file.
2. **LM Studio:** Not currently running / not in use right now. Before Checkpoint 2
   (any real model invocation), still stop and ask the user to start LM Studio and
   confirm the model is loaded at `LOCAL_BASE_URL` — per the brief's standing rule.
   Never assume it's serving.
3. **`data/transcripts.jsonl` old data:** **DELETE old data** (user's explicit
   instruction, overriding the brief's default of append-only). At Checkpoint 1
   recon, report the size/row count of any existing file first, then delete its
   contents before generation begins (do this at the point generation starts —
   Checkpoint 2 pilot — not before, unless the user says otherwise).
4. **`.env`:** User grants freedom to work with `.env` as needed for this task.
   Still: never echo/commit key material, and only report the pipeline-relevant
   values (`USE_LOCAL`, `LOCAL_BASE_URL`, `LOCAL_MODEL`, `LOCAL_MAX_TOKENS`,
   `LOCAL_TEMPERATURE`) as the brief requires. Do not commit `.env` changes to git.

## Standing rules (from the brief, unchanged)

- One checkpoint at a time; stop and report after each; wait for explicit
  user confirmation before proceeding.
- No edits to existing working code paths without asking (validator logic,
  other six fraud types, `models_artifacts/`, etc.).
- No fabricated/massaged numbers — report real yields, real metrics, real
  pass/fail output.
- Verification after relevant checkpoints: `leakage_guard --strict` after
  retrain (must exit 0); `npx tsc --noEmit` + Playwright only if frontend were
  touched (N/A in this scope).
- Log work as a new dated round in `RECOVERY_LOG.md` (backend) in the existing
  format — not as "Phase 12".
- Checkpoint 5 needs a second explicit user confirmation of the specific diff
  before it runs, even though the plan is pre-approved.

## Status

- [ ] Checkpoint 1 — Recon (read-only) — NOT STARTED
- [ ] Checkpoint 2 — Pilot generation (10/10) — blocked on LM Studio confirmation
- [ ] Checkpoint 3 — Full-volume generation (200/200)
- [ ] Checkpoint 4 — Build `src/models/transcript_classifier.py`
- [ ] Checkpoint 5 — Integrate into tabular pipeline (needs explicit go-ahead)
- [x] Checkpoint 6 — Frontend — OUT OF SCOPE (other session)
