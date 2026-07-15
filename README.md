# TrainLens

TrainLens 是一个面向本地计算机视觉训练任务的可视化 Dashboard。

它不负责实现训练算法，而是负责启动训练脚本、实时读取训练指标、显示训练曲线、保存实验记录，并检查 ImageFolder 格式数据集。

TrainLens is a local visual dashboard for computer vision training tasks.  
It does not implement training algorithms. Instead, it launches your training script, monitors metrics, visualizes curves, saves experiment records, and inspects ImageFolder-style datasets.

---

TrainLens 目前支持两种运行模式：

1. **Portable EXE 模式**：推荐普通用户使用。
2. **源码 BAT 模式**：推荐开发者使用。

TrainLens currently supports two running modes:

1. **Portable EXE Mode**: recommended for normal users.
2. **Source BAT Mode**: recommended for developers.

---

## Quick Start / 快速开始

### 方式一：Portable EXE 模式（推荐普通用户）

普通用户推荐使用 Portable EXE 模式。你只需要把 `TrainLens` 文件夹放到自己的计算机视觉项目根目录，然后双击 `TrainLens.exe` 即可。

推荐项目结构：

```text
MyCVProject/                      # 你的 CV 项目根目录
├─ .venv/                         # 你的 Python 训练环境
│  └─ Scripts/
│     └─ python.exe
├─ train.py                       # 你的训练脚本
├─ dataset/
│  ├─ train/
│  │  ├─ class_1/
│  │  └─ class_2/
│  └─ val/
│     ├─ class_1/
│     └─ class_2/
├─ TrainLens/                     # TrainLens 工具目录
│  ├─ TrainLens.exe              # 主程序（双击启动）
│  └─ _internal/                 # 依赖库
└─ runs/                         # 训练记录（自动生成）
```

**使用步骤：**

1. 从 Release 页面下载 `TrainLens_Portable.zip`
2. 解压，将 `TrainLens` 文件夹复制到你的项目根目录（与 `train.py` 同级）
3. 双击 `TrainLens/TrainLens.exe`
4. 浏览器自动打开 `http://localhost:8501`

**自动检测：**

TrainLens.exe 启动后会自动检测：

- `MyCVProject/train.py` → 训练脚本
- `MyCVProject/dataset/train` 和 `dataset/val` → 数据集
- `MyCVProject/.venv/Scripts/python.exe` → 训练 Python 环境
- 训练记录自动保存到 `MyCVProject/runs/exp_001`、`exp_002` ...

**优点：**

- 无需安装 Python 即可启动 Dashboard
- 自动检测项目中的 Python 训练环境（`.venv`、`venv`、`env`）
- 可同时用于多个项目（每个项目复制一份 `TrainLens` 文件夹）
- 训练记录保存在各自项目目录，互不干扰

**Python 环境说明：**

TrainLens.exe 本身是独立运行的，不需要用户安装 Python。但运行 `train.py` 时需要项目中有可用的 Python 环境。TrainLens 会按以下顺序自动检测：

1. `MyCVProject/.venv/Scripts/python.exe`
2. `MyCVProject/venv/Scripts/python.exe`
3. `MyCVProject/env/Scripts/python.exe`
4. 系统 PATH 中的 `python`

如果自动检测失败，可以在 Dashboard 的 Advanced Settings 中手动指定 Python 路径。

---

### 方式二：源码 BAT 模式（推荐开发者）

适合需要修改 Dashboard 源码、调试、或参与开发的用户。

**前置条件：** 需要安装 Python 3.10 或 3.11，并勾选 "Add Python to PATH"。

**第一次安装：**

```bash
双击 setup_trainlens.bat
```

脚本会自动创建 `.venv` 虚拟环境并安装 Streamlit、Plotly、Pandas、NumPy、Pillow 等依赖。

**以后启动：**

```bash
双击 start_trainlens.bat
```

浏览器自动打开 `http://localhost:8501`。

**快速测试（源码模式）：**

直接使用默认的 `scripts/mock_train.py` 模拟训练脚本进行测试。

---

## 项目结构

```text
TrainLens/
├─ setup_trainlens.bat          # 源码模式：首次安装环境
├─ start_trainlens.bat          # 源码模式：启动 TrainLens
├─ trainlens_app/
│  ├─ app.py                    # Dashboard 主程序
│  └─ requirements.txt          # Python 依赖
├─ scripts/
│  └─ mock_train.py             # 默认模拟训练脚本
├─ examples/
│  └─ example_cv_train.py       # 训练脚本接入示例
├─ docs/
│  ├─ TRAIN_SCRIPT_PROTOCOL.md  # 训练脚本协议说明
│  └─ DATASET_INSPECTOR.md      # 数据集检查说明
├─ dataset/
│  ├─ README_dataset_format.txt
│  ├─ train/                    # 训练集
│  └─ val/                      # 验证集
├─ annotations/                 # 标注输出目录（自动生成）
├─ runs/                        # 实验记录目录
├─ README.md
└─ RELEASE_CHECKLIST.md
```

---

## 主要功能

### Training Dashboard

显示当前训练状态，包括：

- 当前 Epoch
- 训练进度
- 当前 Accuracy
- 最佳 Accuracy
- 当前 Loss
- 最佳 Loss
- Accuracy 曲线
- Loss 曲线
- 训练日志
- 最近 metrics 数据

---

### 6.2 Experiment History

每次训练都会自动保存一个实验目录，例如：

```text
runs/exp_001
runs/exp_002
runs/exp_003
```

每个实验目录通常包含：

```text
config.json      # 本次训练配置
metrics.jsonl    # 每个 epoch 的训练指标
summary.json     # 训练结果摘要
train.log        # 训练输出日志
```

---

### 6.3 Dataset Inspector

用于检查 ImageFolder 格式的数据集。

支持格式：

```text
dataset/
├─ train/
│  ├─ cat/
│  │  ├─ 001.jpg
│  │  └─ 002.jpg
│  └─ dog/
│     ├─ 001.jpg
│     └─ 002.jpg
└─ val/
   ├─ cat/
   └─ dog/
```

Dataset Inspector 可以显示：

- 训练集图片数量
- 验证集图片数量
- 类别数量
- 每个类别的图片数量
- 类别分布柱状图
- 随机图片预览

支持图片格式：

```text
.jpg
.jpeg
.png
.bmp
.webp
```

---

## 接入自己的训练脚本

TrainLens 不限制你使用什么模型或框架。

你可以使用：

- PyTorch
- TensorFlow
- PaddlePaddle
- YOLO 项目
- 自己写的训练代码
- 分类、检测、分割项目

但你的训练脚本需要遵守 TrainLens 的 CLI 参数协议和 JSONL 日志协议。

---

### 必须支持的命令行参数

你的训练脚本至少需要支持：

```text
--train     训练集路径
--val       验证集路径
--epochs    训练轮数
--lr        学习率
--batch     Batch Size
--device    运行设备
--log       metrics.jsonl 输出路径
```

TrainLens 启动训练时大概会执行：

```bash
python train.py --train ./dataset/train --val ./dataset/val --epochs 20 --lr 0.001 --batch 16 --device auto --log runs/current/metrics.jsonl
```

---

### 必须输出 metrics.jsonl

训练脚本需要每个 epoch 向 `--log` 指定的文件写入一行 JSON。

示例：

```json
{"epoch":1,"total_epoch":20,"progress":5.0,"train_loss":0.823,"val_loss":0.756,"acc":0.612,"best_acc":0.612,"best_loss":0.756,"lr":0.001,"batch":16,"device":"auto"}
```

每一行都是一个 JSON 对象，这种格式叫 JSONL。

---

### 字段说明

| 字段 | 含义 |
|---|---|
| epoch | 当前 epoch |
| total_epoch | 总 epoch 数 |
| progress | 训练进度，范围 0 到 100 |
| train_loss | 训练集 loss |
| val_loss | 验证集 loss |
| acc | 当前验证集准确率，推荐范围 0 到 1 |
| best_acc | 到目前为止最高准确率 |
| best_loss | 到目前为止最低验证 loss |
| lr | 当前学习率 |
| batch | Batch Size |
| device | 当前运行设备，例如 auto、cpu、cuda:0 |

注意：

```text
acc 推荐使用 0 到 1，例如 0.92 表示 92%。
progress 推荐使用 0 到 100，例如 50.0 表示 50%。
```

---

### 写入 metrics 示例

```python
import json
from pathlib import Path

def write_metric(log_path, data):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
        f.flush()
```

训练循环中写入：

```python
metric = {
    "epoch": epoch,
    "total_epoch": epochs,
    "progress": round(epoch / epochs * 100, 2),
    "train_loss": round(train_loss, 6),
    "val_loss": round(val_loss, 6),
    "acc": round(acc, 6),
    "best_acc": round(best_acc, 6),
    "best_loss": round(best_loss, 6),
    "lr": lr,
    "batch": batch,
    "device": device
}

write_metric(args.log, metric)
```

完整协议请查看：

```text
docs/TRAIN_SCRIPT_PROTOCOL.md
```

示例脚本请查看：

```text
examples/example_cv_train.py
```

---

## 常见问题

### 双击 setup_trainlens.bat 后提示找不到 Python

原因：

- 没有安装 Python
- 安装 Python 时没有勾选 Add Python to PATH

解决：

重新安装 Python 3.10 或 3.11，并勾选 Add Python to PATH。

---

### setup_trainlens.bat 安装依赖失败

可能原因：

- 网络不好
- pip 下载失败
- Python 版本不合适
- 杀毒软件拦截

解决：

- 换一个网络
- 重新运行 `setup_trainlens.bat`
- 确认 Python 版本为 3.10 或 3.11

---

### start_trainlens.bat 提示没有 .venv

原因：

还没有运行初始化脚本。

解决：

先双击运行：

```text
setup_trainlens.bat
```

---

### 浏览器打不开 http://localhost:8501

可能原因：

- Streamlit 没启动成功
- 8501 端口被占用
- bat 窗口里有报错

解决：

- 查看黑色命令行窗口中的报错
- 关闭其他 Streamlit 程序
- 重新运行 `start_trainlens.bat`

---

### 点击 Start Training 后没有曲线

请检查：

- 训练脚本路径是否正确
- 训练脚本是否支持 `--log`
- 是否生成了 `metrics.jsonl`
- `metrics.jsonl` 每一行是否都是合法 JSON
- 写入文件后是否执行了 `flush`

---

## 如何清空实验记录

实验记录保存在：

```text
runs/
```

如果只是测试，可以删除：

```text
runs/exp_001
runs/exp_002
runs/current
```

Git Bash：

```bash
rm -rf runs
mkdir runs
touch runs/.gitkeep
```

Windows CMD：

```bat
rmdir /s /q runs
mkdir runs
type nul > runs\.gitkeep
```

PowerShell：

```powershell
Remove-Item -Recurse -Force .\runs
New-Item -ItemType Directory .\runs
New-Item -ItemType File .\runs\.gitkeep
```

---

## 当前限制

当前版本限制：

- 暂不支持分割 mask 可视化
- 暂不内置 YOLO、ResNet、UNet 等算法
- 暂不支持云端同步
- 暂不支持多人协作
- 暂不支持数据库
- 用户训练脚本需要遵守 CLI + JSONL 协议

---

## Image Annotator（图片标注器）🆕

直接在图片上拖拽画框，支持目标检测标注，YOLO 格式输出。

### 操作方式

| 操作 | 方式 |
|------|------|
| 画框 | 🖱️ 拖拽 |
| 切图 | ⌨️ **A** 上一张 / **D** 下一张（预加载，秒切） |
| 删框 | 点击选中 → **Delete** |
| 撤销 | **右键** |
| 保存 | 💾 Save Annotations 按钮 |
| 跳转 | 📁 下拉框选图 |
| 类别 | 下拉框切换（新画的框自动归入当前类） |

### 标注格式

保存到 `annotations/` 目录，YOLO 归一化格式：

```text
annotations/
├─ classes.txt          # 类别列表（一行一个）
├─ cat_0.txt            # cat_0.jpg 的标注
├─ dog_1.txt            # dog_1.jpg 的标注
└─ visualizations/      # 自动生成的可视化预览图
    └─ gallery/         # 按类别分类的预览图
```

---

## Browse Annotations（标注浏览）🆕

三栏布局查看所有标注结果。

| 左列 | 中列 | 右列 |
|------|------|------|
| 📋 图片列表 | 🖼️ 带框预览图 | 📊 Class Stats |
| 点击秒切 | A/D 秒切 | 各类别框数统计 |

- 🖼️ **Generate All Visualizations**：一键批量生成标注预览图
- 📊 **Gallery**：按 Class 分类浏览
- 📦 **Export Summary**：标注总数统计

---

## 推荐使用流程

**普通用户（Portable EXE 模式）：**

```text
1. 从 Release 下载 TrainLens_Portable.zip
2. 解压，将 TrainLens 文件夹放到项目根目录
3. 双击 TrainLens/TrainLens.exe
4. 用 Dataset Inspector 检查数据集
5. 用 Image Annotator 标注图片（可选）
6. 用 Browse Annotations 查看标注结果
7. 点击 Start Training 开始训练
8. 用 Experiment History 查看历史实验
```

**开发者（源码 BAT 模式）：**

```text
1. 修改 trainlens_app/app.py
2. 修改 examples/example_cv_train.py
3. 修改 docs 文档
4. 用 start_trainlens.bat 测试
5. 发布前清理 .venv、runs、__pycache__
```

---

# English Guide

## Quick Start

TrainLens currently supports two running modes:

1. **Portable EXE Mode**: recommended for normal users.
2. **Source BAT Mode**: recommended for developers.

---

## Option 1: Portable EXE Mode (Recommended for Normal Users)

This is the recommended way to use TrainLens.

Users do not need to understand the TrainLens source code structure. They only need to copy the `TrainLens` folder into the root directory of their computer vision project and double-click `TrainLens.exe`.

TrainLens.exe can start the Dashboard without requiring users to install Python for TrainLens itself. However, running the user's `train.py` still requires a valid Python training environment in the user's project.

Recommended project structure:

```text
MyCVProject/
├─ .venv/
│  └─ Scripts/
│     └─ python.exe
├─ train.py
├─ dataset/
│  ├─ train/
│  │  ├─ class_1/
│  │  └─ class_2/
│  └─ val/
│     ├─ class_1/
│     └─ class_2/
├─ TrainLens/
│  ├─ TrainLens.exe
│  └─ _internal/
└─ runs/
```

**Steps:**

1. Download `TrainLens_Portable.zip` from the Release page
2. Extract and place the `TrainLens` folder in your project root (same level as `train.py`)
3. Double-click `TrainLens/TrainLens.exe`
4. The browser opens automatically at `http://localhost:8501`

**Auto-detection:**

When TrainLens.exe starts, it automatically detects:

- `MyCVProject/train.py` → training script
- `MyCVProject/dataset/train` and `dataset/val` → datasets
- Python training environment, searched in this order:
  1. `MyCVProject/.venv/Scripts/python.exe`
  2. `MyCVProject/venv/Scripts/python.exe`
  3. `MyCVProject/env/Scripts/python.exe`
  4. `python` in system PATH

If auto-detection fails, you can manually specify the Python path in the Dashboard's Advanced Settings.

**Where experiment records are saved:**

Experiment records are saved to `MyCVProject/runs/` (the project root), not to `MyCVProject/TrainLens/runs/`.

**Advantages:**

- No need to install Python just to launch the Dashboard
- Automatically detects the Python training environment in your project
- Can be used for multiple projects (copy the `TrainLens` folder into each project)
- Experiment records stay in each project directory — no mix-ups

---

## Option 2: Source BAT Mode (Recommended for Developers)

For users who need to modify the Dashboard source code, debug, or contribute to development.

**Prerequisites:** Python 3.10 or 3.11 with "Add Python to PATH" checked during installation.

**First-time setup:**

```bash
Double-click setup_trainlens.bat
```

This script automatically creates a `.venv` virtual environment and installs dependencies such as Streamlit, Plotly, Pandas, NumPy, and Pillow.

**Start TrainLens:**

```bash
Double-click start_trainlens.bat
```

The browser opens automatically at `http://localhost:8501`.

**Quick test (Source BAT Mode):**

Use the default `scripts/mock_train.py` to verify everything works.

---

## Project Structure

```text
TrainLens/
├─ setup_trainlens.bat          # Source BAT Mode: first-time setup
├─ start_trainlens.bat          # Source BAT Mode: start TrainLens
├─ trainlens_app/
│  ├─ app.py                    # Main Dashboard application
│  └─ requirements.txt          # Python dependencies
├─ scripts/
│  └─ mock_train.py             # Default mock training script
├─ examples/
│  └─ example_cv_train.py       # Example training script
├─ docs/
│  ├─ TRAIN_SCRIPT_PROTOCOL.md  # Training script protocol
│  └─ DATASET_INSPECTOR.md      # Dataset Inspector guide
├─ dataset/
│  ├─ README_dataset_format.txt # Dataset format guide
│  ├─ train/                    # Example training set
│  └─ val/                      # Example validation set
├─ runs/                        # Experiment records
├─ README.md
└─ RELEASE_CHECKLIST.md
```

---

## Main Features

### Training Dashboard

Displays:

- Current epoch
- Training progress
- Current accuracy
- Best accuracy
- Current loss
- Best loss
- Accuracy curve
- Loss curve
- Training logs
- Recent metrics

---

### Experiment History

Each training run is saved as an experiment folder:

```text
runs/exp_001
runs/exp_002
runs/exp_003
```

Each experiment folder usually contains:

```text
config.json      # Training configuration
metrics.jsonl    # Metrics for each epoch
summary.json     # Training summary
train.log        # Training output log
```

---

### Dataset Inspector

Used to inspect ImageFolder-style datasets.

Supported structure:

```text
dataset/
├─ train/
│  ├─ cat/
│  │  ├─ 001.jpg
│  │  └─ 002.jpg
│  └─ dog/
│     ├─ 001.jpg
│     └─ 002.jpg
└─ val/
   ├─ cat/
   └─ dog/
```

Dataset Inspector shows:

- Number of training images
- Number of validation images
- Number of classes
- Number of images per class
- Class distribution bar chart
- Random image previews

Supported image formats:

```text
.jpg
.jpeg
.png
.bmp
.webp
```

---

## Using Your Own Training Script

TrainLens does not restrict your model or framework.

You may use:

- PyTorch
- TensorFlow
- PaddlePaddle
- YOLO projects
- Custom training code
- Classification, detection, or segmentation projects

However, your training script must follow the TrainLens CLI and JSONL logging protocol.

---

### Required Command-Line Arguments

Your training script should support at least:

```text
--train     Training dataset path
--val       Validation dataset path
--epochs    Number of epochs
--lr        Learning rate
--batch     Batch size
--device    Running device
--log       Output path for metrics.jsonl
```

TrainLens will run a command similar to:

```bash
python train.py --train ./dataset/train --val ./dataset/val --epochs 20 --lr 0.001 --batch 16 --device auto --log runs/current/metrics.jsonl
```

---

### Required metrics.jsonl Output

Your training script should write one JSON line to the file specified by `--log` after each epoch.

Example:

```json
{"epoch":1,"total_epoch":20,"progress":5.0,"train_loss":0.823,"val_loss":0.756,"acc":0.612,"best_acc":0.612,"best_loss":0.756,"lr":0.001,"batch":16,"device":"auto"}
```

Each line must be a valid JSON object. This format is called JSONL.

---

### Field Definitions

| Field | Description |
|---|---|
| epoch | Current epoch |
| total_epoch | Total number of epochs |
| progress | Training progress, from 0 to 100 |
| train_loss | Training loss |
| val_loss | Validation loss |
| acc | Current validation accuracy, recommended range 0 to 1 |
| best_acc | Best accuracy so far |
| best_loss | Best validation loss so far |
| lr | Current learning rate |
| batch | Batch size |
| device | Current running device, such as auto, cpu, cuda:0 |

Note:

```text
acc should be between 0 and 1. For example, 0.92 means 92%.
progress should be between 0 and 100. For example, 50.0 means 50%.
```

---

### Example Metric Writing Code

```python
import json
from pathlib import Path

def write_metric(log_path, data):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")
        f.flush()
```

Inside your training loop:

```python
metric = {
    "epoch": epoch,
    "total_epoch": epochs,
    "progress": round(epoch / epochs * 100, 2),
    "train_loss": round(train_loss, 6),
    "val_loss": round(val_loss, 6),
    "acc": round(acc, 6),
    "best_acc": round(best_acc, 6),
    "best_loss": round(best_loss, 6),
    "lr": lr,
    "batch": batch,
    "device": device
}

write_metric(args.log, metric)
```

For the complete protocol, see:

```text
docs/TRAIN_SCRIPT_PROTOCOL.md
```

For an example script, see:

```text
examples/example_cv_train.py
```

---

## FAQ

### setup_trainlens.bat says Python was not found

Reason:

- Python is not installed
- Add Python to PATH was not checked during installation

Solution:

Install Python 3.10 or 3.11 and check Add Python to PATH.

---

### setup_trainlens.bat fails to install dependencies

Possible reasons:

- Poor network connection
- pip download failure
- Incompatible Python version
- Antivirus software blocking installation

Solutions:

- Try another network
- Run `setup_trainlens.bat` again
- Make sure Python version is 3.10 or 3.11

---

### start_trainlens.bat says .venv was not found

Reason:

The setup script has not been run yet.

Solution:

Run:

```text
setup_trainlens.bat
```

---

### Browser cannot open http://localhost:8501

Possible reasons:

- Streamlit did not start successfully
- Port 8501 is already in use
- There is an error in the bat window

Solutions:

- Check the error message in the command window
- Close other Streamlit programs
- Run `start_trainlens.bat` again

---

### No curves appear after clicking Start Training

Check:

- Whether the training script path is correct
- Whether the training script supports `--log`
- Whether `metrics.jsonl` is generated
- Whether every line in `metrics.jsonl` is valid JSON
- Whether the file is flushed after each write

---

## Clear Experiment Records

Experiment records are stored in:

```text
runs/
```

For testing, you can delete:

```text
runs/exp_001
runs/exp_002
runs/current
```

Git Bash:

```bash
rm -rf runs
mkdir runs
touch runs/.gitkeep
```

Windows CMD:

```bat
rmdir /s /q runs
mkdir runs
type nul > runs\.gitkeep
```

PowerShell:

```powershell
Remove-Item -Recurse -Force .\runs
New-Item -ItemType Directory .\runs
New-Item -ItemType File .\runs\.gitkeep
```

---

## Current Limitations

Current limitations:

- Object detection bbox visualization is not supported yet
- Segmentation mask visualization is not supported yet
- YOLO, ResNet, UNet, and other algorithms are not built in
- Cloud sync is not supported
- Multi-user collaboration is not supported
- Database storage is not supported
- User training scripts must follow the CLI + JSONL protocol

---

## Recommended Workflow

**For normal users (Portable EXE Mode):**

```text
1. Download TrainLens_Portable.zip from the Release page
2. Extract and place the TrainLens folder in your project root
3. Double-click TrainLens/TrainLens.exe
4. Use Dataset Inspector to check your dataset
5. Click Start Training to begin training
6. Use Experiment History to review training runs
```

**For developers (Source BAT Mode):**

```text
1. Modify trainlens_app/app.py
2. Modify examples/example_cv_train.py
3. Modify docs if needed
4. Test with start_trainlens.bat
5. Clean .venv, runs, and __pycache__ before release
```

---

## Summary

TrainLens does not train models for you.

It makes your training process more visible:

- Launch
- Monitor
- Record
- Compare
- Inspect datasets