@echo off
REM AFL Full Project - one-command launcher for Windows.
REM Starts the FastAPI backend + Vite frontend in two hidden windows.
REM Logs go to backend.log and frontend\dev.log.
REM Stop with: stop.cmd   (or close the two processes via Task Manager).

setlocal

echo.
echo ==============================================
echo   Adversarial Fraud Lab - Full Stack Launcher
echo ==============================================
echo   Backend:  http://127.0.0.1:8000  (FastAPI)
echo   Frontend: http://127.0.0.1:5173  (Vite/React)
echo.

REM Kill anything already running on the two ports.
for %%P in (8000 5173) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P " ^| findstr LISTENING') do (
        echo [cleanup] killing pid %%a on port %%P
        taskkill /F /PID %%a >nul 2>&1
    )
)

REM Start backend.
echo [backend] starting uvicorn on :8000...
cd /d "%~dp0"
start "AFL-Backend" /MIN cmd /c "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8000 --host 127.0.0.1 > backend.log 2>&1"

REM Start frontend.
echo [frontend] starting vite on :5173...
cd /d "%~dp0frontend"
start "AFL-Frontend" /MIN cmd /c "cd /d %~dp0frontend && npm run dev > dev.log 2>&1"

REM Wait for backend.
echo [wait] waiting for backend :8000 ...
set RETRIES=30
:wait_backend
ping -n 2 127.0.0.1 >nul 2>&1
set /a RETRIES-=1
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health | findstr "200" >nul
if %errorlevel%==0 goto :backend_up
if %RETRIES%==0 echo [backend] TIMEOUT - check backend.log
if %RETRIES%==0 goto :skip_backend
goto :wait_backend
:backend_up
echo [backend] up
:skip_backend

REM Wait for frontend.
echo [wait] waiting for frontend :5173 ...
set RETRIES=30
:wait_frontend
ping -n 2 127.0.0.1 >nul 2>&1
set /a RETRIES-=1
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:5173/ | findstr "200" >nul
if %errorlevel%==0 goto :frontend_up
if %RETRIES%==0 echo [frontend] TIMEOUT - check frontend\dev.log
if %RETRIES%==0 goto :skip_frontend
goto :wait_frontend
:frontend_up
echo [frontend] up
:skip_frontend

echo.
echo ==============================================
echo   Demo is live
echo ==============================================
echo   Open http://127.0.0.1:5173/ in your browser
echo.
echo   Logs:  backend.log  +  frontend\dev.log
echo   Stop:  stop.cmd
echo.

REM Open browser if explorer.exe is available (non-headless only).
start http://127.0.0.1:5173/

endlocal