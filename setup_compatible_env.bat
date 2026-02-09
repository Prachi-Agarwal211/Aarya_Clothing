@echo off
echo ============================================
echo Aarya Clothing - Compatible Python Setup
echo ============================================
echo All Docker issues have been resolved!
echo Recommended: Use docker-compose up -d
echo.

REM Check if Python 3.11 is available
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python 3.11 found!
    echo Creating compatible virtual environment...
    
    REM Create virtual environment
    py -3.11 -m venv venv_core_compatible
    
    REM Activate and install dependencies
    call venv_core_compatible\Scripts\activate.bat
    pip install --upgrade pip
    
    echo Installing FastAPI and dependencies...
    pip install fastapi==0.109.0 uvicorn[standard]==0.27.0
    pip install pydantic==2.12.5 pydantic-settings==2.1.0
    pip install python-multipart==0.0.6 sqlalchemy==2.0.25
    pip install psycopg2==2.9.11 redis==5.0.1
    pip install python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4
    pip install bcrypt==4.1.2 email-validator==2.1.0
    pip install python-dotenv==1.2.1 httpx==0.26.0
    
    echo.
    echo ============================================
    echo Compatible environment ready!
    echo ============================================
    echo.
    echo To use this environment:
    echo   venv_core_compatible\Scripts\activate
    echo   cd services\core
    echo   python main.py
    echo.
    echo Services will be available at:
    echo   - Core API: http://localhost:8001
    echo   - Health Check: http://localhost:8001/health
    echo.
    
) else (
    echo Python 3.11 not found on this system.
    echo.
    echo Please install Python 3.11 from:
    echo https://www.python.org/downloads/release/python-3119/
    echo.
    echo OR use Docker Compose (recommended):
    echo   docker-compose up -d
    echo.
    echo Docker will handle all dependencies automatically!
    echo All build issues have been fixed.
)

echo Press any key to exit...
pause >nul
