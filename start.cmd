@echo off
REM ===============================================================
REM Adversarial Fraud Lab - one-command launcher (Windows)
REM Runs preflight_check.py --install --yes (auto-installs missing
REM Python/frontend deps with '*' progress), and only starts the
REM stack when ENVIRONMENT READY.
REM Stop with: stop.cmd
REM ===============================================================
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo ==================================================
echo   Adversarial Fraud Lab - Project Launcher
echo ==================================================
echo   Backend:  http://127.0.0.1:8000  (FastAPI)
echo   Frontend: http://127.0.0.1:5173  (Vite/React)
echo.

if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo [preflight] .venv not found; will auto-install below.
)

REM ---- Phase 1: preflight CHECK (no install) ----
echo [preflight] checking environment...
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%ROOT%preflight_check.py"
) else (
    py -3 "%ROOT%preflight_check.py"
)
if errorlevel 1 goto :need_fix

echo [preflight] ENVIRONMENT READY -- starting stack.
goto :launch

:need_fix
echo.
echo [preflight] environment NOT ready. See report above.
echo [preflight] auto-installing (watch for '*' progress)...
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%ROOT%preflight_check.py" --install --yes
) else (
    py -3 "%ROOT%preflight_check.py" --install --yes
)
if errorlevel 1 (
    echo [preflight] auto-install FAILED or partial.
    goto :manual
)

echo [preflight] install pass complete. Re-verifying...
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%ROOT%preflight_check.py"
) else (
    py -3 "%ROOT%preflight_check.py"
)
if errorlevel 1 (
    echo [preflight] still not ready after install.
    pause
    exit /b 1
)

echo [preflight] ENVIRONMENT READY -- starting stack.

:launch
REM Kill anything already running on the two ports.
for %%P in (8000 5173) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P " ^| findstr LISTENING') do (
        echo [cleanup] killing pid %%a on port %%P
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM Start backend.
echo [backend] starting uvicorn on :8000...
start "AFL-Backend" /MIN cmd /c "cd /d %ROOT% && %ROOT%.venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8000 --host 127.0.0.1 > %ROOT%backend.log 2>&1"

REM Start frontend.
echo [frontend] starting vite on :5173...
start "AFL-Frontend" /MIN cmd /c "cd /d %ROOT%frontend && npm run dev > %ROOT%frontend\dev.log 2>&1"

REM Wait for backend.
echo [wait] waiting for backend :8000 ...
set RETRIES=40
:wait_backend
ping -n 2 127.0.0.1 >nul 2>&1
set /a RETRIES-=1
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health | findstr "200" >nul
if !errorlevel!==0 goto :backend_up
if !RETRIES!==0 (echo [backend] TIMEOUT - check backend.log ^& goto :skip_backend)
goto :wait_backend
:backend_up
echo [backend] up
:skip_backend

REM Wait for frontend.
echo [wait] waiting for frontend :5173 ...
set RETRIES=40
:wait_frontend
ping -n 2 127.0.0.1 >nul 2>&1
set /a RETRIES-=1
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:5173/ | findstr "200" >nul
if !errorlevel!==0 goto :frontend_up
if !RETRIES!==0 (echo [frontend] TIMEOUT - check frontend\dev.log ^& goto :skip_frontend)
goto :wait_frontend
:frontend_up
echo [frontend] up
:skip_frontend

echo.
echo ==================================================
echo   Stack started
echo ==================================================
echo   Backend : http://127.0.0.1:8000/docs
echo   App     : http://127.0.0.1:5173/
echo.
echo   Logs:  backend.log  +  frontend\dev.log
echo   Stop:  stop.cmd
echo.

start http://127.0.0.1:5173/
endlocal
goto :eof

:manual
echo.
echo [preflight] MANUAL SETUP REQUIRED:
echo   1. py -3 -m venv .venv
echo   2. .venv\Scripts\python.exe -m pip install -r requirements.txt
echo   3. cd frontend ^& npm ci ^& cd ..
echo   4. python preflight_check.py
echo.
pause
exit /b 1
