@echo off
echo ========================================
echo TrainLens Dashboard Launcher
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Checking Python...
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
) else (
    echo [2/4] Virtual environment already exists.
    echo.
)

REM Activate virtual environment
echo [3/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [4/4] Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r trainlens_app\requirements.txt

echo.
echo ========================================
echo Starting TrainLens Dashboard...
echo ========================================
echo.
echo Dashboard URL: http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

REM Start Streamlit
streamlit run trainlens_app\app.py --server.port 8501 --server.headless true

pause
