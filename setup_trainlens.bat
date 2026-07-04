@echo off
chcp 65001 >nul
setlocal

REM Get project root directory
set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

echo ========================================
echo TrainLens 初始化安装
echo ========================================
echo.

REM Check if Python is available
echo [1/6] 检查 Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python！
    echo.
    echo 请先安装 Python 3.10 或 3.11：
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载 Python 3.10 或 3.11
    echo 3. 安装时勾选 "Add Python to PATH"
    echo 4. 安装完成后重新运行此脚本
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM Check if venv exists
if exist "%PROJECT_ROOT%\.venv" (
    echo [警告] 虚拟环境 .venv 已存在
    echo 是否删除并重新安装？
    choice /C YN /M "删除重装 (Y) 或跳过安装 (N)"
    if errorlevel 2 (
        echo.
        echo 跳过安装，使用现有虚拟环境
        echo.
        pause
        exit /b 0
    )
    echo.
    echo [2/6] 删除旧虚拟环境...
    rmdir /s /q "%PROJECT_ROOT%\.venv"
)

REM Create virtual environment
echo [2/6] 创建虚拟环境 .venv...
python -m venv "%PROJECT_ROOT%\.venv"
if errorlevel 1 (
    echo.
    echo [错误] 虚拟环境创建失败！
    echo 请检查：
    echo - Python 是否正确安装
    echo - 磁盘空间是否充足
    echo - 杀毒软件是否拦截
    echo.
    pause
    exit /b 1
)
echo.

REM Activate virtual environment
echo [3/6] 激活虚拟环境...
call "%PROJECT_ROOT%\.venv\Scripts\activate.bat"
if errorlevel 1 (
    echo.
    echo [错误] 虚拟环境激活失败！
    echo.
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo [4/6] 升级 pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo [5/6] 安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.
pip install -r "%PROJECT_ROOT%\trainlens_app\requirements.txt"
if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败！
    echo 请检查：
    echo - 网络连接是否正常
    echo - 防火墙是否拦截
    echo - 尝试使用国内镜像：
    echo   pip install -r trainlens_app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    pause
    exit /b 1
)
echo.

REM Create directories
echo [6/6] 创建必要目录...
if not exist "%PROJECT_ROOT%\runs\current" mkdir "%PROJECT_ROOT%\runs\current"
if not exist "%PROJECT_ROOT%\dataset\train" mkdir "%PROJECT_ROOT%\dataset\train"
if not exist "%PROJECT_ROOT%\dataset\val" mkdir "%PROJECT_ROOT%\dataset\val"
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下次启动 TrainLens：
echo   双击 start_trainlens.bat
echo.
echo 或手动启动：
echo   1. 激活虚拟环境: .venv\Scripts\activate.bat
echo   2. 启动 Dashboard: streamlit run trainlens_app\app.py
echo.
pause
