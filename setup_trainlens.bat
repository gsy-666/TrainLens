@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo TrainLens Setup
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    echo Please install Python 3.10 or 3.11 and check "Add Python to PATH".
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Please check your Python installation.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
) else (
    echo Virtual environment already exists.
    echo.
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Installing requirements...
echo This may take a few minutes...
echo.
python -m pip install -r "trainlens_app\requirements.txt"

if errorlevel 1 (
    echo.
    echo Failed to install requirements.
    echo Please check your network connection.
    echo.
    echo You can try with a mirror:
    echo pip install -r trainlens_app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    pause
    exit /b 1
)

echo.
echo Creating necessary directories...
if not exist "runs\current" mkdir "runs\current"
if not exist "dataset\train" mkdir "dataset\train"
if not exist "dataset\val" mkdir "dataset\val"

echo.
echo ========================================
echo TrainLens setup finished.
echo You can now run start_trainlens.bat
echo ========================================
echo.
pause
