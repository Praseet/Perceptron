@echo off
REM ===============================================================
REM Adversarial Fraud Lab - stop script (Windows)
REM Kills any process listening on ports 8000 and 5173.
REM ===============================================================
setlocal

echo.
echo [stop] stopping Adversarial Fraud Lab...
echo.

for %%P in (8000 5173) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%P " ^| findstr LISTENING') do (
        echo [stop] killing pid %%a on port %%P
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [stop] done.
endlocal