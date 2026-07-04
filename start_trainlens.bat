@echo off
chcp 65001 >nul
setlocal

REM Get project root directory
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================
echo TrainLens Dashboard 启动中...
echo ========================================
echo.

REM Check if .venv exists
if not exist "%PROJECT_ROOT%\.venv" (
    echo [错误] 虚拟环境 .venv 不存在！
    echo.
    echo 请先运行 setup_trainlens.bat 进行安装
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/2] 激活虚拟环境...
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo.
    echo [错误] 虚拟环境激活失败！
    echo 请重新运行 setup_trainlens.bat 安装
    echo.
    pause
    exit /b 1
)
echo.

REM Start Streamlit
echo [2/2] 启动 Streamlit Dashboard...
echo.
echo Dashboard 将在浏览器中自动打开
echo 地址: http://localhost:8501
echo.
echo 按 Ctrl+C 可停止 Dashboard
echo ========================================
echo.

cd "%PROJECT_ROOT%"
streamlit run trainlens_app\app.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] Dashboard 启动失败！
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 端口 8501 被占用
    echo    解决：关闭其他 Streamlit 应用，或使用命令：
    echo          streamlit run trainlens_app\app.py --server.port 8502
    echo.
    echo 2. 依赖包损坏
    echo    解决：重新运行 setup_trainlens.bat
    echo.
    echo 3. Python 版本不兼容
    echo    解决：使用 Python 3.10 或 3.11
    echo.
    pause
    exit /b 1
)
