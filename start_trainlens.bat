@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Starting TrainLens
echo ========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment was not found.
    echo Please run setup_trainlens.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "trainlens_app\app.py" (
    echo trainlens_app\app.py was not found.
    echo Please make sure you are running this file from the TrainLens root folder.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    echo Please run setup_trainlens.bat again.
    pause
    exit /b 1
)

echo Starting Streamlit dashboard...
echo Open in browser: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server.
echo.

python -m streamlit run "trainlens_app\app.py"

if errorlevel 1 (
    echo.
    echo Failed to start Streamlit.
    echo.
    echo Possible solutions:
    echo - Port 8501 may be in use. Try: streamlit run trainlens_app\app.py --server.port 8502
    echo - Re-run setup_trainlens.bat to reinstall dependencies.
    echo.
)

pause
