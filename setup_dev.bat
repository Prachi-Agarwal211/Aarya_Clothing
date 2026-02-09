@echo off
REM Aarya Clothing - Development Setup Script
REM This script sets up all virtual environments and installs dependencies

echo ========================================
echo Aarya Clothing - Development Setup
echo ========================================
echo.
echo This script sets up the development environment
echo All services are now configured for Python 3.11
echo.

REM Check if Docker is running
echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not running
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo Docker is installed
echo.

REM Start database containers
echo Starting PostgreSQL and Redis containers...
docker-compose up -d postgres redis

REM Wait for databases to be ready
echo Waiting for databases to initialize...
timeout /t 10 /nobreak >nul

REM Check if containers are running
) else (
    echo WARNING: Redis may still be initializing...
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Copy .env.example to .env and configure your settings
echo 2. Start services in separate terminals:
echo    - Core Service: venv_core\Scripts\activate && cd services\core && python main.py
echo    - Commerce Service: venv_commerce\Scripts\activate && cd services\commerce && python main.py
echo    - Payment Service: venv_payment\Scripts\activate && cd services\payment && python main.py
echo    - Frontend: cd frontend && npm install && npm run dev
echo.
echo Services will be available at:
echo - Core API: http://localhost:8001
echo - Commerce API: http://localhost:8010
echo - Payment API: http://localhost:8020
echo - Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause >nul
