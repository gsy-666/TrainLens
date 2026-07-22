#!/usr/bin/env bash
# ============================================================
#  TrainLens - 一键启动 (Linux / macOS)
#  本机：bash start.sh
#  远程：bash start.sh --host 0.0.0.0 [--port 8000] [--token XXX]
# ============================================================
set -e
cd "$(dirname "$0")"

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "[提示] 未找到 .venv，请先运行：bash setup.sh"
  exit 1
fi

if [ ! -f "web/frontend/dist/index.html" ]; then
  echo "[提示] 缺少前端构建产物，请先运行：bash setup.sh"
  exit 1
fi

( sleep 3
  if command -v xdg-open >/dev/null 2>&1; then xdg-open http://127.0.0.1:8000
  elif command -v open >/dev/null 2>&1; then open http://127.0.0.1:8000
  fi ) &

cd web/backend
exec "../../$PY" start.py "$@"
