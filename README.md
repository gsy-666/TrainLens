# TrainLens

<p>
  <img src="web/frontend/public/logo.png" alt="TrainLens" width="200" />
</p>

AI 图像标注 + 训练的 Web 工作台：React 前端 + FastAPI 后端，浏览器完成 **标注 → AI 辅助 → 数据集 → 训练** 全流程。支持本机使用和云服务器远程使用。

![标注效果](web/frontend/public/annotation-preview.jpg)

## 快速开始

```bash
git clone https://github.com/gsy-666/TrainLens.git
cd TrainLens
```

**Windows**：双击 `setup.bat`（环境检测安装），完成后双击 `start.bat`
**Linux / macOS**：

```bash
bash setup.sh   # 检测并安装全部依赖，缺啥装啥
bash start.sh   # 启动并打开浏览器
```

- 访问 **http://127.0.0.1:8000**
- 要求：Python ≥ 3.11；前端已预构建在仓库内，**无需 Node.js**（仅修改前端源码后才需要 Node 重新构建）
- GPU 用户：编辑 `requirements.txt`，把 `onnxruntime` 换成 `onnxruntime-gpu` 后再运行 setup

## 云服务器远程使用

训练在云服务器上跑的场景：

```bash
bash start.sh --host 0.0.0.0        # Windows: start.bat --host 0.0.0.0
```

启动器自动生成**访问令牌**并打印。本地浏览器打开 `http://<服务器IP>:8000`，在欢迎页输入令牌，或直接点「连接远程服务器」填入地址和令牌。标注、推理、训练全部在服务器上执行。

公网环境建议用 SSH 隧道代替（全程加密）：`ssh -L 8000:127.0.0.1:8000 user@server -N`

## 功能

- **标注**：矩形 / 多边形 / 旋转框 / 圆 / 直线 / 点 / 折线 / 立方体；顶点编辑、Ctrl+Z 撤销、快捷键、视频逐帧标注
- **AI 辅助**：190+ ONNX 模型自动预标注（一键撤回）、**SAM 点/框交互式掩码**、视频 MOT 跟踪
- **标注 → 训练闭环**：一键把标注目录转成 YOLO 训练集（自动提取类别、划分 train/val、生成 data.yaml），Ultralytics 引导式训练，预检查 / 实时日志 / 指标曲线 / 历史记录
- **运行监控**：自定义训练脚本启动/停止、控制台实时流、CPU/内存/GPU 曲线
- **数据**：本地目录浏览、上传、YOLO / VOC / COCO / DOTA / Mask / MOT / ODVG 导出（ZIP 下载）
- **兼容**：标注 JSON 与桌面版 X-AnyLabeling 逐字段兼容，可互相打开

## 目录结构

```
├── setup.bat / setup.sh     # 一键环境检测与安装
├── start.bat / start.sh     # 一键启动（支持 --host/--port/--token）
├── requirements.txt         # 全部 Python 依赖
├── anylabeling/             # X-AnyLabeling Python 包（推理/导出/训练服务）
└── web/
    ├── backend/             # FastAPI 后端（start.py 启动器 + app/）
    └── frontend/            # React 前端源码 + dist 预构建产物
```

## 开发

```bash
# 后端热重载
cd web/backend && ../../.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
# 前端热更新（需要 Node.js）
cd web/frontend && npm install && npm run dev   # http://localhost:5173
```

前端改动后 `npm run build` 并提交 `web/frontend/dist`。

## License

GPLv3（继承自 X-AnyLabeling）
