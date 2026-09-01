#!/usr/bin/env bash
# ===============================================================
# Adversarial Fraud Lab - one-command launcher (macOS / Linux)
# ===============================================================
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo
echo "=================================================="
echo "  Adversarial Fraud Lab - Project Launcher"
echo "=================================================="
echo "  Backend:  http://127.0.0.1:8000  (FastAPI)"
echo "  Frontend: http://127.0.0.1:5173  (Vite/React)"
echo

if [ ! -x ".venv/bin/python" ]; then
  echo "[preflight] .venv not found; creating it..."
  python3 -m venv .venv
fi

echo "[preflight] checking environment..."
if ! .venv/bin/python preflight_check.py; then
  echo "[preflight] environment NOT ready. Auto-installing..."
  read -rp "[preflight] proceed with install? [Y/n] " ans
  ans="${ans:-Y}"
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    .venv/bin/python preflight_check.py --install --yes
  else
    echo "[preflight] manual setup required."
    exit 1
  fi
fi

echo "[preflight] ENVIRONMENT READY -- starting stack."

# Kill anything already running on the two ports.
for port in 8000 5173; do
  pids=$(lsof -ti:"$port" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "[cleanup] killing pids $pids on port $port"
    echo "$pids" | xargs kill -9 2>/dev/null || true
  fi
done

echo "[backend] starting uvicorn on :8000..."
"$ROOT/.venv/bin/python" -m uvicorn src.api.main:app --port 8000 --host 127.0.0.1 > "$ROOT/backend.log" 2>&1 &
echo $! > "$ROOT/.backend.pid"

echo "[frontend] starting vite on :5173..."
( cd "$ROOT/frontend" && npm run dev > "$ROOT/frontend/dev.log" 2>&1 ) &
echo $! > "$ROOT/.frontend.pid"

echo "[wait] waiting for backend :8000 ..."
for i in $(seq 1 80); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/api/health || echo 000)
  if [ "$code" = "200" ]; then
    echo "[backend] up"
    break
  fi
  sleep 1
done

echo "[wait] waiting for frontend :5173 ..."
for i in $(seq 1 80); do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5173/ || echo 000)
  if [ "$code" = "200" ]; then
    echo "[frontend] up"
    break
  fi
  sleep 1
done

echo
echo "=================================================="
echo "  Stack started"
echo "=================================================="
echo "  Backend : http://127.0.0.1:8000/docs"
echo "  App     : http://127.0.0.1:5173/"
echo
echo "  Logs:  backend.log  +  frontend/dev.log"
echo "  Stop:  bash stop.sh"
echo

open http://127.0.0.1:5173/ 2>/dev/null || xdg-open http://127.0.0.1:5173/ 2>/dev/null || true
