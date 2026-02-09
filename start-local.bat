@echo off
REM ============================================================
REM Aarya Clothing - Local Development Startup Script
REM ============================================================
REM This script starts all services for local development
REM 
REM Prerequisites:
REM 1. Docker Desktop running (for PostgreSQL and Redis)
REM 2. Python 3.11+ installed
REM 3. Node.js 18+ installed
REM 4. Virtual environments created (run setup_compatible_env.bat first)
REM ============================================================

echo.
echo ========================================
echo   Aarya Clothing - Local Development
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

REM Set environment variables for local development
set DATABASE_URL=postgresql://postgres:change_this_password_in_production@localhost:5432/aarya_clothing
set REDIS_URL=redis://localhost:6379/0
set JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
set SECRET_KEY=your-encryption-secret-key-change-in-production
set COOKIE_SECURE=false
set ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8001"]
set ENVIRONMENT=development
set DEBUG=true

echo [Step 1/5] Starting PostgreSQL and Redis containers...
docker-compose up -d postgres redis

REM Wait for containers to be healthy
echo Waiting for containers to be ready...
timeout /t 5 /nobreak >nul

REM Check PostgreSQL
docker-compose exec -T postgres pg_isready -U postgres >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL not ready yet, waiting...
    timeout /t 5 /nobreak >nul
)

echo.
echo [Step 2/5] Starting Core Service (Port 8001)...
echo.
start "Core Service - Port 8001" cmd /k "venv_core\Scripts\activate && cd services\core && set DATABASE_URL=postgresql://postgres:change_this_password_in_production@localhost:5432/aarya_clothing && set REDIS_URL=redis://localhost:6379/0 && set COOKIE_SECURE=false && set ENVIRONMENT=development && python main.py"

echo Waiting for core service to start...
timeout /t 3 /nobreak >nul

echo.
echo [Step 3/5] Starting Commerce Service (Port 8010)...
echo.
start "Commerce Service - Port 8010" cmd /k "venv_commerce\Scripts\activate && cd services\commerce && set DATABASE_URL=postgresql://postgres:change_this_password_in_production@localhost:5432/aarya_clothing && set REDIS_URL=redis://localhost:6379/0 && set CORE_PLATFORM_URL=http://localhost:8001 && set SECRET_KEY=your-super-secret-jwt-key-change-in-production && set ENVIRONMENT=development && python main.py"

echo Waiting for commerce service to start...
timeout /t 3 /nobreak >nul

echo.
echo [Step 4/5] Starting Payment Service (Port 8020)...
echo.
start "Payment Service - Port 8020" cmd /k "venv_payment\Scripts\activate && cd services\payment && set DATABASE_URL=postgresql://postgres:change_this_password_in_production@localhost:5432/aarya_clothing && set REDIS_URL=redis://localhost:6379/0 && set CORE_PLATFORM_URL=http://localhost:8001 && set SECRET_KEY=your-super-secret-jwt-key-change-in-production && set ENVIRONMENT=development && python main.py"

echo Waiting for payment service to start...
timeout /t 3 /nobreak >nul

echo.
echo [Step 5/5] Starting Frontend (Port 3000)...
echo.
start "Frontend - Port 3000" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   All services are starting!
echo ========================================
echo.
echo Services:
echo   - PostgreSQL:    localhost:5432
echo   - Redis:         localhost:6379
echo   - Core API:      http://localhost:8001
echo   - Commerce API:  http://localhost:8010
echo   - Payment API:   http://localhost:8020
echo   - Frontend:      http://localhost:3000
echo.
echo Test Commands:
echo   curl http://localhost:8001/health
echo   curl http://localhost:8010/health
echo   curl http://localhost:8020/health
echo.
echo Default Admin Login:
echo   Email:    admin@aarya.com
echo   Password: admin123
echo.
echo Press any key to open the frontend in your browser...
pause >nul
start http://localhost:3000
