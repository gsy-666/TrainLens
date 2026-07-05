@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo TrainLens EXE Builder
echo ========================================
echo.

REM Check if .venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found.
    echo Please run setup_trainlens.bat first.
    echo.
    pause
    exit /b 1
)

echo Activating virtual environment...
call ".venv\Scripts\activate.bat"
echo.

echo Installing PyInstaller...
python -m pip install pyinstaller
echo.

echo Cleaning old build artifacts...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo.

echo Building TrainLens.exe with PyInstaller...
echo This may take several minutes...
echo.
pyinstaller TrainLens.spec

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build failed!
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Output location: dist\TrainLens\
echo Executable: dist\TrainLens\TrainLens.exe
echo.
echo To test:
echo 1. Create a test project folder
echo 2. Copy dist\TrainLens folder into it
echo 3. Double-click TrainLens\TrainLens.exe
echo.
pause
