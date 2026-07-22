@echo off
rem ============================================================
rem  TrainLens - 一键环境检测与安装
rem  检查并安装所有依赖，缺啥装啥
rem ============================================================
setlocal
cd /d %~dp0

echo ==========================================
echo   TrainLens 环境检测与安装
echo ==========================================

rem ---- 1. Python 虚拟环境 ----
set "PY=%~dp0.venv\Scripts\python.exe"
if exist "%PY%" goto :venv_ok

echo [1/5] 未检测到虚拟环境，正在创建...
set "BASE_PY="
where py >/dev/null 2>&1
if %errorlevel%==0 (
  py -3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1
  if not errorlevel 1 set "BASE_PY=py -3"
)
if not defined BASE_PY (
  python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1
  if not errorlevel 1 set "BASE_PY=python"
)
if not defined BASE_PY (
  echo [错误] 需要 Python 3.11 或更高版本：https://www.python.org/downloads/
  echo         （注意：请勿使用 Anaconda 自带的旧版 Python，Qt 库会加载失败）
  goto :error
)
echo       使用 %BASE_PY% 创建 .venv
%BASE_PY% -m venv "%~dp0.venv"
if errorlevel 1 goto :error

:venv_ok
echo [1/5] Python 环境：%PY%

rem ---- 2. pip 依赖 ----
echo [2/5] 安装/检查 Python 依赖（首次较慢，请耐心等待）...
"%PY%" -m pip install --upgrade pip >/dev/null 2>&1
"%PY%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :error

rem ---- 3. 前端构建产物 ----
if exist "%~dp0web\frontend\dist\index.html" (
  echo [3/5] 前端已就绪（web\frontend\dist）
) else (
  echo [3/5] 构建前端...
  where npm >/dev/null 2>&1
  if errorlevel 1 (
    echo [错误] 缺少前端构建产物且未找到 npm，请安装 Node.js 后重新运行本脚本
    goto :error
  )
  pushd "%~dp0web\frontend"
  if not exist node_modules call npm install
  if errorlevel 1 ( popd & goto :error )
  call npm run build
  if errorlevel 1 ( popd & goto :error )
  popd
)

rem ---- 4. 自检 ----
echo [4/5] 自检...
"%PY%" -c "import fastapi, uvicorn, onnxruntime, ultralytics; from PyQt6 import QtCore; import anylabeling.app_info; print('  核心依赖 OK, X-AnyLabeling', anylabeling.app_info.__version__)"
if errorlevel 1 (
  echo.
  echo [错误] Qt 库加载失败。如果 .venv 是用 Anaconda 的 Python 创建的，
  echo        请删除 .venv 文件夹，安装 python.org 的 Python 3.12+ 后重试。
  goto :error
)

rem ---- 5. 完成 ----
echo [5/5] 环境就绪！
echo.
echo   本机使用：双击 start.bat
echo   云服务器：start.bat --host 0.0.0.0（会生成远程访问令牌）
echo.
pause
exit /b 0

:error
echo.
echo 安装失败，请把上方错误信息截图反馈。
pause
exit /b 1
