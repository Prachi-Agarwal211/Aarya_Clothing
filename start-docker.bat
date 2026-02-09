@echo off
REM Aarya Clothing - Docker Development Environment Starter (Windows)
REM This script starts the complete e-commerce platform with Docker

setlocal enabledelayedexpansion

echo ========================================
echo Aarya Clothing Docker Setup
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)
echo [INFO] Docker is running ✓

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] docker-compose is not installed. Please install docker-compose first.
    pause
    exit /b 1
)
echo [INFO] docker-compose is available ✓

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "docker\postgres" mkdir "docker\postgres"
if not exist "docker\redis" mkdir "docker\redis"
if not exist "docker\nginx" mkdir "docker\nginx"
if not exist "logs" mkdir "logs"
echo [INFO] Directories created ✓

REM Create init.sql if it doesn't exist
if not exist "docker\postgres\init.sql" (
    echo [INFO] Creating PostgreSQL initialization script...
    (
        echo -- Aarya Clothing Database Initialization
        echo -- This script creates the initial database schema
        echo.
        echo -- Create extensions
        echo CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        echo CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        echo.
        echo -- Create indexes for better performance
        echo -- These will be created by the services automatically
    ) > "docker\postgres\init.sql"
    echo [INFO] PostgreSQL init script created ✓
)

REM Create redis.conf if it doesn't exist
if not exist "docker\redis\redis.conf" (
    echo [INFO] Creating Redis configuration...
    (
        echo # Redis Configuration for Aarya Clothing
        echo bind 0.0.0.0
        echo port 6379
        echo timeout 0
        echo save 900 1
        echo save 300 10
        echo save 60 10000
        echo dbfilename dump.rdb
        echo dir /data
        echo appendonly yes
        echo appendfsync everysec
        echo maxmemory 256mb
        echo maxmemory-policy allkeys-lru
    ) > "docker\redis\redis.conf"
    echo [INFO] Redis configuration created ✓
)

REM Create nginx config for development
if not exist "docker\nginx\nginx.dev.conf" (
    echo [INFO] Creating Nginx configuration...
    (
        echo events {
        echo     worker_connections 1024;
        echo }
        echo.
        echo http {
        echo     upstream frontend {
        echo         server frontend:3000;
        echo     }
        echo.
        echo     upstream core_api {
        echo         server core:8001;
        echo     }
        echo.
        echo     upstream commerce_api {
        echo         server commerce:8010;
        echo     }
        echo.
        echo     upstream payment_api {
        echo         server payment:8020;
        echo     }
        echo.
        echo     server {
        echo         listen 80;
        echo         server_name localhost;
        echo.
        echo         # Frontend
        echo         location / {
        echo             proxy_pass http://frontend;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo.
        echo         # Core API
        echo         location /api/auth/ {
        echo             proxy_pass http://core_api;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo.
        echo         # Commerce API
        echo         location /api/products/ {
        echo             proxy_pass http://commerce_api;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo.
        echo         location /api/cart/ {
        echo             proxy_pass http://commerce_api;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo.
        echo         location /api/orders/ {
        echo             proxy_pass http://commerce_api;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo.
        echo         # Payment API
        echo         location /api/payments/ {
        echo             proxy_pass http://payment_api;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        echo             proxy_set_header X-Forwarded-Proto $scheme;
        echo         }
        echo     }
        echo }
    ) > "docker\nginx\nginx.dev.conf"
    echo [INFO] Nginx configuration created ✓
)

REM Stop existing containers
echo [INFO] Stopping existing containers...
docker-compose -f docker-compose.dev.yml down --remove-orphans >nul 2>&1
echo [INFO] Existing containers stopped ✓

REM Build and start services
echo.
echo ========================================
echo Starting Aarya Clothing E-Commerce Platform
echo ========================================

echo [INFO] Building Docker images...
docker-compose -f docker-compose.dev.yml build --no-cache

echo [INFO] Starting all services...
docker-compose -f docker-compose.dev.yml up -d

echo [INFO] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check service health
echo [INFO] Checking service health...

REM Check PostgreSQL
docker exec aarya_postgres_dev pg_isready -U postgres >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] PostgreSQL is healthy ✓
) else (
    echo [ERROR] PostgreSQL is not healthy
)

REM Check Redis
docker exec aarya_redis_dev redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Redis is healthy ✓
) else (
    echo [ERROR] Redis is not healthy
)

REM Check Core Service
curl -s http://localhost:8001/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Core Service is healthy ✓
) else (
    echo [WARNING] Core Service might still be starting...
)

REM Check Commerce Service
curl -s http://localhost:8010/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Commerce Service is healthy ✓
) else (
    echo [WARNING] Commerce Service might still be starting...
)

REM Check Payment Service
curl -s http://localhost:8020/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Payment Service is healthy ✓
) else (
    echo [WARNING] Payment Service might still be starting...
)

REM Check Frontend
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Frontend is healthy ✓
) else (
    echo [WARNING] Frontend might still be starting...
)

echo.
echo ========================================
echo Access URLs
echo ========================================
echo [INFO] Frontend:     http://localhost:3000
echo [INFO] Core API:      http://localhost:8001
echo [INFO] Commerce API:  http://localhost:8010
echo [INFO] Payment API:   http://localhost:8020
echo [INFO] PostgreSQL:    localhost:5432
echo [INFO] Redis:         localhost:6379
echo.
echo [INFO] API Documentation:
echo [INFO] Core:         http://localhost:8001/docs
echo [INFO] Commerce:     http://localhost:8010/docs
echo [INFO] Payment:      http://localhost:8020/docs

echo.
echo [INFO] All services started successfully!
echo [INFO] Use 'start-docker.bat logs' to view logs
echo [INFO] Use 'start-docker.bat stop' to stop all services

REM Check for command line arguments
if "%1"=="logs" (
    echo [INFO] Showing logs (press Ctrl+C to exit)...
    docker-compose -f docker-compose.dev.yml logs -f
) else if "%1"=="stop" (
    echo [INFO] Stopping all services...
    docker-compose -f docker-compose.dev.yml down
    echo [INFO] All services stopped ✓
)

pause
