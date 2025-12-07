@echo off
echo.
echo ========================================
echo   Starting Backend Server (FastAPI)
echo ========================================
echo.

start "Backend - FastAPI (Port 8000)" cmd /k "cd /d %~dp0 && call venv\Scripts\activate && uvicorn app.main:app --reload"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Starting Frontend Server (React)
echo ========================================
echo.

start "Frontend - React (Port 3000)" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   APPLICATION STARTED!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to open the application...
pause >nul

start http://localhost:3000

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause

