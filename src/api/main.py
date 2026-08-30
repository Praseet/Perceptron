"""
AFL FastAPI backend - Phase 0 stub.

This phase only proves:
  - the process boots
  - CORS is configured so Vite (http://localhost:5173) can call it
  - GET /api/health returns a literal stub shape

Real endpoint logic (wrapping FraudInferenceService, generators, feedback
loop) is later phases' work. Do not expand this file in Phase 0.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Adversarial Fraud Lab API",
    version="0.1.0",
    description="Closed-loop red-team/blue-team fraud detection. Phase 0 stub.",
)

# Permissive CORS scoped to local dev origins only.
# Do not open to "*" - even though there is no auth, sloppy defaults are
# sloppy defaults.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Literal stub for Phase 0. Later phases fill in real values."""
    return {
        "status": "ok",
        "model_loaded": False,
        "data_loaded": False,
        "n_users": 0,
    }