#!/usr/bin/env pwsh
# AFL Full Project Launcher
#
# One command to start the entire Adversarial Fraud Lab demo:
#   - Real XGBoost Tier 1 + Isolation Forest Tier 2 backend on :8000
#   - Vite + React 19 frontend on :5173 (proxies /api/* to backend)
#
# Usage:
#   pwsh .\start.ps1           # start everything in the current shell
#   pwsh .\start.ps1 -Open    # also open the demo URL in your browser
#
# On first run it will create the .venv and npm install. After that
# the script just starts both processes.

param(
    [switch]$Open = $false,
    [switch]$BackendOnly = $false,
    [switch]$FrontendOnly = $false
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "")
Set-Location $root

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Adversarial Fraud Lab - Full Stack Launcher" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Backend:  http://127.0.0.1:8000  (FastAPI)" -ForegroundColor Gray
Write-Host "  Frontend: http://127.0.0.1:5173  (Vite/React)" -ForegroundColor Gray
Write-Host ""

# --- 1. Verify Python venv ---
$venvPython = Join-Path $root ".venv/Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[setup] Creating Python venv..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }
    Write-Host "[setup] Installing Python deps..." -ForegroundColor Yellow
    & $venvPython -m pip install --quiet --upgrade pip
    & $venvPython -m pip install --quiet fastapi uvicorn pydantic numpy pandas scikit-learn xgboost joblib
}

# --- 2. Verify node_modules ---
$frontendDir = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[setup] Installing frontend deps (npm install)..." -ForegroundColor Yellow
    Push-Location $frontendDir
    try { npm install }
    finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw "Failed npm install" }
}

# --- 3. Verify .env file ---
$envFile = Join-Path $frontendDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "[setup] Writing frontend/.env (live cutover config)..." -ForegroundColor Yellow
    @"
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_MODE=false
"@ | Set-Content -Path $envFile -Encoding utf8 -NoNewline
}

# --- 4. Kill anything already on :8000 or :5173 ---
foreach ($port in 8000, 5173) {
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess |
        Where-Object { $_ -gt 0 } | Select-Object -Unique
    foreach ($pid in $pids) {
        Write-Host "[cleanup] killing pid $pid on port $port" -ForegroundColor DarkGray
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Milliseconds 500

# --- 5. Start the backend ---
if (-not $FrontendOnly) {
    Write-Host "[backend] starting uvicorn on :8000..." -ForegroundColor Green
    $backendLog = Join-Path $root "backend.log"
    if (Test-Path $backendLog) { Remove-Item $backendLog }
    $backendArgs = @(
        "-NoProfile", "-Command",
        "cd '$root'; & '$venvPython' -m uvicorn src.api.main:app --port 8000 --host 127.0.0.1 *> '$backendLog'"
    )
    Start-Process -FilePath "powershell" -ArgumentList $backendArgs -WindowStyle Hidden
}

# --- 6. Start the frontend ---
if (-not $BackendOnly) {
    Write-Host "[frontend] starting vite on :5173..." -ForegroundColor Green
    $frontendLog = Join-Path $frontendDir "dev.log"
    if (Test-Path $frontendLog) { Remove-Item $frontendLog }
    $frontendArgs = @(
        "-NoProfile", "-Command",
        "cd '$frontendDir'; npm run dev *> '$frontendLog'"
    )
    Start-Process -FilePath "powershell" -ArgumentList $frontendArgs -WindowStyle Hidden
}

# --- 7. Wait for both to come up ---
Write-Host "[wait] waiting for backend :8000 ..." -ForegroundColor Gray
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host "[backend] up" -ForegroundColor Green
        break
    } catch {
        if ($i -eq 29) { Write-Host "[backend] TIMEOUT - check backend.log" -ForegroundColor Red }
    }
}

if (-not $BackendOnly) {
    Write-Host "[wait] waiting for frontend :5173 ..." -ForegroundColor Gray
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 2 | Out-Null
            Write-Host "[frontend] up" -ForegroundColor Green
            break
        } catch {
            if ($i -eq 29) { Write-Host "[frontend] TIMEOUT - check frontend/dev.log" -ForegroundColor Red }
        }
    }
}

# --- 8. Health summary ---
Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Demo is live" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Cyan
try {
    $health = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing).Content | ConvertFrom-Json
    Write-Host ("  Backend health: status=$($health.status)  model_loaded=$($health.model_loaded)  data_loaded=$($health.data_loaded)  n_users=$($health.n_users)") -ForegroundColor White
} catch {}
Write-Host "  Open http://127.0.0.1:5173/ in your browser" -ForegroundColor White
Write-Host ""
Write-Host "  Logs: backend.log and frontend/dev.log" -ForegroundColor DarkGray
Write-Host "  Stop: pwsh .\stop.ps1   (or kill the two powershell.exe processes)" -ForegroundColor DarkGray
Write-Host ""

# --- 9. Optionally open browser ---
if ($Open) {
    Write-Host "[open] launching http://127.0.0.1:5173/ in your default browser..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:5173/"
}