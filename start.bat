@echo off
setlocal enabledelayedexpansion

echo === Checking prerequisites ===

:: Check Python 3.10+
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VER=%%v
echo OK Python %PYTHON_VER%

:: Check Node.js 18+
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install from https://nodejs.org
    exit /b 1
)
for /f "tokens=1" %%v in ('node --version') do set NODE_VER=%%v
echo OK Node.js %NODE_VER%

:: Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm not found
    exit /b 1
)
for /f "tokens=1" %%v in ('npm --version') do set NPM_VER=%%v
echo OK npm %NPM_VER%
echo.

:: Find available backend port (Windows)
set BACKEND_PORT=9000
:find_backend_port
netstat -an | find ":%BACKEND_PORT% " >nul 2>&1
if not errorlevel 1 (
    echo Port %BACKEND_PORT% in use, trying next...
    set /a BACKEND_PORT+=1
    goto find_backend_port
)

:: Find available frontend port
set FRONTEND_PORT=5173
:find_frontend_port
netstat -an | find ":%FRONTEND_PORT% " >nul 2>&1
if not errorlevel 1 (
    echo Port %FRONTEND_PORT% in use, trying next...
    set /a FRONTEND_PORT+=1
    goto find_frontend_port
)

echo === Configuration ===
echo   Backend port:  %BACKEND_PORT%
echo   Frontend port: %FRONTEND_PORT%
echo.

:: Update shared_config.json with detected ports using PowerShell
if exist "shared_config.json" (
    echo Updating shared_config.json with detected ports...
    powershell -Command "$cfg = Get-Content 'shared_config.json' | ConvertFrom-Json; $cfg.ports.backend = %BACKEND_PORT%; $cfg.ports.frontend_web = %FRONTEND_PORT%; $cfg.cors_origins = @('http://localhost:%FRONTEND_PORT%', 'http://localhost:3000'); $cfg | ConvertTo-Json -Depth 10 | Set-Content 'shared_config.json'" 2>nul || echo Warning: Could not update shared_config.json
)

:: === Backend Setup ===
set BACKEND_DIR=backend
echo === Setting up backend ===
cd %BACKEND_DIR%

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install dependencies
echo Installing backend dependencies...
pip install . -q

:: Database setup — default to SQLite
if not defined DATABASE_URL (
    if not exist "..\storage" mkdir ..\storage
    set DATABASE_URL=sqlite:///../storage/app.db
)
echo   Database: %DATABASE_URL%

:: Update backend CORS_ORIGINS
set CORS_ORIGINS=http://localhost:%FRONTEND_PORT%,http://localhost:3000

:: Run database migrations
echo Running database migrations...
alembic upgrade head 2>nul || echo Warning: Migration warning (may be expected for first run)

:: Seed database
echo Seeding database...
python app\seed.py 2>nul || python -c "from app.seed import seed_database; seed_database()" 2>nul

:: Start backend
echo Starting backend on http://localhost:%BACKEND_PORT%
start /b uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT%

:: Save backend PID (approximate — Windows doesn't have direct PID tracking like Unix)
for /f "skip=3 tokens=2" %%p in ('tasklist /fi "imagename eq python.exe"') do (
    echo %%p >> ..\pids.txt
    goto backend_started
)
:backend_started

cd ..

:: === Frontend Setup ===
if exist "frontend\package.json" (
    echo.
    echo === Setting up frontend ===
    cd frontend

    :: Install dependencies
    echo Installing frontend dependencies...
    call npm install --silent 2>nul || call npm install

    :: Update frontend .env with backend API URL
    echo VITE_API_URL=http://localhost:%BACKEND_PORT% > .env
    echo Updated frontend .env with backend URL

    :: Start frontend
    echo Starting frontend on http://localhost:%FRONTEND_PORT%
    start /b npm run dev -- --port %FRONTEND_PORT% --host

    cd ..
)

:: Wait for services to start
echo.
echo Waiting for services to start...
timeout /t 3 /nobreak >nul

echo.
echo ==========================================
echo   Multi-team Knowledge Assistant
echo ==========================================
echo.
echo Services running:
echo   * Backend API:  http://localhost:%BACKEND_PORT%
echo   * API Docs:     http://localhost:%BACKEND_PORT%/docs
echo   * Frontend Web: http://localhost:%FRONTEND_PORT%
echo.
echo Default Credentials:
echo   * Email:    admin@example.com
echo   * Password: admin123
echo.
echo Press Ctrl+C to stop, or run: stop.bat
echo ==========================================
echo.

pause
