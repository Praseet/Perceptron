#!/usr/bin/env pwsh
# AFL Full Project Stopper.
#
# Stops the backend (uvicorn on :8000) and frontend (vite on :5173)
# processes started by start.ps1.

param()

Write-Host "[stop] killing anything on :8000 (backend) and :5173 (frontend)..." -ForegroundColor Cyan
foreach ($port in 8000, 5173) {
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue).OwningProcess |
        Where-Object { $_ -gt 0 } | Select-Object -Unique
    foreach ($pid in $pids) {
        Write-Host "  killing pid $pid on port $port" -ForegroundColor DarkGray
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[done] both processes stopped." -ForegroundColor Green