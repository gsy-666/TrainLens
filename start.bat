@echo off
rem ============================================================
rem  TrainLens - 一键启动
rem  本机：双击 start.bat
rem  远程：start.bat --host 0.0.0.0 [--port 8000] [--token XXX]
rem ============================================================
setlocal
cd /d %~dp0
set "PY=%~dp0.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo [提示] 未找到 .venv，请先双击运行 setup.bat 完成环境安装
  pause
  exit /b 1
)

if not exist "%~dp0web\frontend\dist\index.html" (
  echo [提示] 缺少前端构建产物，请先双击运行 setup.bat
  pause
  exit /b 1
)

echo 启动 TrainLens（按 Ctrl+C 停止）...
echo %* | findstr /i "0.0.0.0" >nul || start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000"
cd /d "%~dp0web\backend"
"%PY%" start.py %*
