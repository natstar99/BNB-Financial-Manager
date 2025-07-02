@echo off
echo.
echo ==========================================
echo  BNB Financial Manager - React Frontend
echo ==========================================
echo.

echo [1/3] Starting Backend API Server...
start "BNB API Server" cmd /k ".venv\Scripts\activate && python -m uvicorn api.main:app --reload --port 8000"

echo [2/3] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Frontend React Server...
start "BNB Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo  Servers Starting!
echo ==========================================
echo.
echo Backend API:     http://localhost:8000
echo Frontend App:    http://localhost:5173
echo API Docs:        http://localhost:8000/docs
echo.
echo Both servers will open in separate windows.
echo You can close this window once both are running.
echo.
echo If you encounter any dependency issues, run:
echo   cd frontend
echo   rmdir /s /q node_modules
echo   del package-lock.json
echo   npm install
echo.
pause