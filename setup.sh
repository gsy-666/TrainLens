#!/usr/bin/env bash
# ============================================================
#  TrainLens - 一键环境检测与安装 (Linux / macOS)
# ============================================================
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "  TrainLens 环境检测与安装"
echo "=========================================="

# ---- 1. Python >= 3.11 ----
PY=""
for cand in python3.13 python3.12 python3.11 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
      PY="$cand"
      break
    fi
  fi
done
if [ -z "$PY" ]; then
  echo "[错误] 需要 Python 3.11 或更高版本，请先安装。"
  exit 1
fi

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/5] 创建虚拟环境 .venv（使用 $PY）..."
  "$PY" -m venv .venv
fi
VENV_PY=".venv/bin/python"
echo "[1/5] Python 环境：$("$VENV_PY" --version)"

# ---- 2. pip 依赖 ----
echo "[2/5] 安装/检查 Python 依赖（首次较慢，请耐心等待）..."
"$VENV_PY" -m pip install --upgrade pip -q
"$VENV_PY" -m pip install -r requirements.txt

# ---- 3. 前端 ----
if [ -f "web/frontend/dist/index.html" ]; then
  echo "[3/5] 前端已就绪（web/frontend/dist）"
else
  echo "[3/5] 构建前端..."
  if ! command -v npm >/dev/null 2>&1; then
    echo "[错误] 缺少前端构建产物且未找到 npm。请安装 Node.js 后重新运行本脚本。"
    exit 1
  fi
  cd web/frontend
  [ -d node_modules ] || npm install
  npm run build
  cd ../..
fi

# ---- 4. 自检 ----
echo "[4/5] 自检..."
"$VENV_PY" -c "import fastapi, uvicorn, onnxruntime, ultralytics; from PyQt6 import QtCore; import anylabeling.app_info; print('  核心依赖 OK, X-AnyLabeling', anylabeling.app_info.__version__)"

# ---- 5. 完成 ----
echo "[5/5] 环境就绪！"
echo ""
echo "  本机使用：bash start.sh"
echo "  云服务器：bash start.sh --host 0.0.0.0（会生成远程访问令牌）"
echo ""
