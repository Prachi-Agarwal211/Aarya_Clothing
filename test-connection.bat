@echo off
REM ============================================================
REM Aarya Clothing - Connection Test Script
REM ============================================================
REM This script tests if all services are running and can connect
REM ============================================================

echo.
echo ========================================
echo   Aarya Clothing - Connection Test
echo ========================================
echo.

REM Check if Docker containers are running
echo [1] Checking Docker containers...
docker-compose ps postgres redis 2>nul | findstr "Up" >nul
if errorlevel 1 (
    echo [FAIL] Docker containers not running
    echo        Run: docker-compose up -d postgres redis
) else (
    echo [OK] Docker containers are running
)

echo.

REM Test PostgreSQL connection
echo [2] Testing PostgreSQL connection...
docker-compose exec -T postgres pg_isready -U postgres -d aarya_clothing 2>nul | findstr "accepting" >nul
if errorlevel 1 (
    echo [FAIL] PostgreSQL not ready
) else (
    echo [OK] PostgreSQL is accepting connections
)

echo.

REM Test Redis connection
echo [3] Testing Redis connection...
docker-compose exec -T redis redis-cli ping 2>nul | findstr "PONG" >nul
if errorlevel 1 (
    echo [FAIL] Redis not ready
) else (
    echo [OK] Redis is responding
)

echo.

REM Test Core Service
echo [4] Testing Core Service (Port 8001)...
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Core service not responding
    echo        Start with: venv_core\Scripts\activate && cd services\core && python main.py
) else (
    echo [OK] Core service is healthy
)

echo.

REM Test Commerce Service
echo [5] Testing Commerce Service (Port 8010)...
curl -s http://localhost:8010/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Commerce service not responding
    echo        Start with: venv_commerce\Scripts\activate && cd services\commerce && python main.py
) else (
    echo [OK] Commerce service is healthy
)

echo.

REM Test Payment Service
echo [6] Testing Payment Service (Port 8020)...
curl -s http://localhost:8020/health >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Payment service not responding
    echo        Start with: venv_payment\Scripts\activate && cd services\payment && python main.py
) else (
    echo [OK] Payment service is healthy
)

echo.

REM Test Frontend
echo [7] Testing Frontend (Port 3000)...
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Frontend not responding
    echo        Start with: cd frontend && npm run dev
) else (
    echo [OK] Frontend is running
)

echo.

REM Test Login API
echo [8] Testing Login API...
curl -s -X POST "http://localhost:8001/api/v1/auth/login" -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}" 2>nul | findstr "access_token" >nul
if errorlevel 1 (
    echo [FAIL] Login API test failed
    echo        Check if core service is running and admin user exists
) else (
    echo [OK] Login API is working
)

echo.
echo ========================================
echo   Test Complete
echo ========================================
echo.
echo If all tests pass, your setup is ready!
echo Open http://localhost:3000 in your browser.
echo.
echo Default login: admin@aarya.com / admin123
echo.
pause
