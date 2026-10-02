@echo off
rem ============================================================
rem  P-TRANSMIT AI — one-click local launcher (Windows)
rem  Starts backend (:8000) + frontend (:4173) and opens browser
rem  Double-click this file any time you want to run the platform.
rem ============================================================
title P-TRANSMIT AI - Local Host
cd /d "%~dp0"

echo.
echo  [1/3] Starting backend (FastAPI on http://127.0.0.1:8000) ...
cd backend
start "P-TRANSMIT backend" cmd /c "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
cd ..

rem Give the backend a moment to boot
timeout /t 5 /nobreak >nul

echo  [2/3] Starting frontend (production preview on http://localhost:4173) ...
cd frontend
start "P-TRANSMIT frontend" cmd /c "npx vite preview --port 4173 --strictPort --host"

rem Give the frontend a moment to boot
timeout /t 4 /nobreak >nul

echo  [3/3] Opening browser ...
start "" "http://localhost:4173"

echo.
echo  ============================================================
echo   P-TRANSMIT AI is running:
echo     - Local:      http://localhost:4173
echo     - Network:    http://10.246.147.117:4173  (same Wi-Fi devices)
echo     - API docs:   http://127.0.0.1:8000/docs
echo   Login: click "Enter live demo" (no account needed)
echo   Close the two opened windows to stop the servers.
echo  ============================================================
echo.
pause
