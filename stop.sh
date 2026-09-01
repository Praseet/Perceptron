#!/usr/bin/env bash
# ===============================================================
# Adversarial Fraud Lab - stop script (macOS / Linux)
# ===============================================================
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo
echo "[stop] stopping Adversarial Fraud Lab..."
echo

pids=$(lsof -ti:8000,5173 2>/dev/null || true)
if [ -n "$pids" ]; then
  echo "$pids" | xargs kill -9 2>/dev/null || true
else
  echo "[stop] nothing found on :8000/:5173"
fi

if [ -f "$ROOT/.backend.pid" ]; then
  kill "$(cat "$ROOT/.backend.pid")" 2>/dev/null || true
  rm -f "$ROOT/.backend.pid"
fi
if [ -f "$ROOT/.frontend.pid" ]; then
  kill "$(cat "$ROOT/.frontend.pid")" 2>/dev/null || true
  rm -f "$ROOT/.frontend.pid"
fi

echo "[stop] done."
