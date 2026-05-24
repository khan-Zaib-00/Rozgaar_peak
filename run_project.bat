@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    RozgaarSphere - Project Starter
echo ==========================================
echo.

:: Step 1: Cleanup any existing process on port 5001
echo [*] Checking for existing server on port 5001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5001') do (
    echo [!] Found existing process %%a. Terminating...
    taskkill /F /PID %%a >nul 2>&1
)

:: Step 2: Start the server
echo [*] Starting Flask server...
start "RozgaarSphere Server" cmd /c "python app.py & pause"

:: Step 3: Wait for server to be responsive
echo [*] Waiting for server to initialize...
:wait_loop
set "ready=0"
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5001') do (
    set "ready=1"
)
if !ready! equ 0 (
    timeout /t 1 /nobreak >nul
    goto wait_loop
)

echo [+] Server is ready!
echo [*] Launching browser...
start http://127.0.0.1:5001

echo.
echo ==========================================
echo    Project is running at http://127.0.0.1:5001
echo    Keep the server window open.
echo ==========================================
echo.
pause

