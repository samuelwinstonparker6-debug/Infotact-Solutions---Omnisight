@echo off
echo ========================================================
echo   Starting OmniSight Services (Backend + Frontend)
echo ========================================================

echo [1/2] Launching OmniSight FastAPI Backend on http://127.0.0.1:8000 ...
start "OmniSight Backend" cmd /k "cd /d "%~dp0omnisight" && C:\Python314\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

timeout /t 2 /nobreak >nul

echo [2/2] Launching OmniSight React Frontend on http://127.0.0.1:5173 ...
start "OmniSight Frontend" cmd /k "cd /d "%~dp0omnisight\frontend" && npm run dev -- --host 127.0.0.1"

echo.
echo ========================================================
echo   Both services are starting!
echo   Frontend: http://127.0.0.1:5173
echo   Backend:  http://127.0.0.1:8000
echo   Docs:     http://127.0.0.1:8000/docs
echo ========================================================

