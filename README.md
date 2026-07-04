# TrainLens

TrainLens 是一个面向本地计算机视觉训练任务的可视化 Dashboard。

它不负责实现训练算法，而是负责启动训练脚本、实时读取训练指标、显示训练曲线、保存实验记录，并检查 ImageFolder 格式数据集。

TrainLens is a local visual dashboard for computer vision training tasks.  
It does not implement training algorithms. Instead, it launches your training script, monitors metrics, visualizes curves, saves experiment records, and inspects ImageFolder-style datasets.

---

# 中文说明

## 1. 项目简介

TrainLens 的核心定位是：

> 训练算法由你的 `train.py` 负责。  
> TrainLens 负责启动它、观察它、记录它。

它可以帮助你：

- 启动本地训练脚本
- 实时读取 `metrics.jsonl`
- 显示训练进度、Accuracy 曲线、Loss 曲线
- 自动保存每次实验记录
- 查看历史实验结果
- 检查 ImageFolder 格式数据集
- 更直观地观察计算机视觉训练过程

---

## 2. 项目结构

```text
TrainLens/
├─ setup_trainlens.bat          # 第一次安装环境用
├─ start_trainlens.bat          # 启动 TrainLens 用
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
│  ├─ README_dataset_format.txt # 数据集格式说明
│  ├─ train/                    # 示例训练集
│  └─ val/                      # 示例验证集
├─ runs/                        # 实验记录目录
├─ README.md
└─ RELEASE_CHECKLIST.md
```

---

## 3. 第一次使用

### 第一步：安装 Python

推荐使用：

```text
Python 3.10 或 Python 3.11
```

安装 Python 时请勾选：

```text
Add Python to PATH
```

如果没有安装 Python，可以从官网下载：

```text
https://www.python.org/downloads/
```

---

### 第二步：安装 TrainLens 环境

解压项目后，双击运行：

```text
setup_trainlens.bat
```

它会自动完成：

- 检查 Python
- 创建 `.venv` 虚拟环境
- 安装 Streamlit、Plotly、Pandas、NumPy、Pillow 等依赖

安装完成后会看到类似提示：

```text
TrainLens setup finished.
You can now run start_trainlens.bat
```

---

## 4. 启动 TrainLens

以后每次使用，双击运行：

```text
start_trainlens.bat
```

正常情况下浏览器会自动打开：

```text
http://localhost:8501
```

如果浏览器没有自动打开，可以手动复制该地址到浏览器。

---

## 5. 快速测试

第一次打开 Dashboard 后，可以直接使用默认模拟训练脚本测试。

侧边栏保持默认设置：

```text
Training Script: scripts/mock_train.py
Train Directory: ./dataset/train
Validation Directory: ./dataset/val
Epochs: 5
Learning Rate: 0.001
Batch Size: 16
Device: auto
```

点击：

```text
Start Training
```

正常现象：

- 状态变为 Running
- 进度轮盘开始增长
- Accuracy / Loss 曲线开始更新
- 训练结束后状态变为 Finished
- `runs/exp_001`、`runs/exp_002` 等实验目录自动生成

---

## 6. 主要功能

### 6.1 Training Dashboard

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

## 7. 接入自己的训练脚本

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

### 7.1 必须支持的命令行参数

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

### 7.2 必须输出 metrics.jsonl

训练脚本需要每个 epoch 向 `--log` 指定的文件写入一行 JSON。

示例：

```json
{"epoch":1,"total_epoch":20,"progress":5.0,"train_loss":0.823,"val_loss":0.756,"acc":0.612,"best_acc":0.612,"best_loss":0.756,"lr":0.001,"batch":16,"device":"auto"}
```

每一行都是一个 JSON 对象，这种格式叫 JSONL。

---

### 7.3 字段说明

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

### 7.4 写入 metrics 示例

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

## 8. 常见问题

### 8.1 双击 setup_trainlens.bat 后提示找不到 Python

原因：

- 没有安装 Python
- 安装 Python 时没有勾选 Add Python to PATH

解决：

重新安装 Python 3.10 或 3.11，并勾选 Add Python to PATH。

---

### 8.2 setup_trainlens.bat 安装依赖失败

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

### 8.3 start_trainlens.bat 提示没有 .venv

原因：

还没有运行初始化脚本。

解决：

先双击运行：

```text
setup_trainlens.bat
```

---

### 8.4 浏览器打不开 http://localhost:8501

可能原因：

- Streamlit 没启动成功
- 8501 端口被占用
- bat 窗口里有报错

解决：

- 查看黑色命令行窗口中的报错
- 关闭其他 Streamlit 程序
- 重新运行 `start_trainlens.bat`

---

### 8.5 点击 Start Training 后没有曲线

请检查：

- 训练脚本路径是否正确
- 训练脚本是否支持 `--log`
- 是否生成了 `metrics.jsonl`
- `metrics.jsonl` 每一行是否都是合法 JSON
- 写入文件后是否执行了 `flush`

---

## 9. 如何清空实验记录

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

## 10. 当前限制

当前版本限制：

- 暂不支持目标检测 bbox 可视化
- 暂不支持分割 mask 可视化
- 暂不内置 YOLO、ResNet、UNet 等算法
- 暂不支持云端同步
- 暂不支持多人协作
- 暂不支持数据库
- 暂未打包成 exe
- 用户训练脚本需要遵守 CLI + JSONL 协议

---

## 11. 推荐使用流程

普通用户：

```text
1. 解压 TrainLens
2. 双击 setup_trainlens.bat
3. 双击 start_trainlens.bat
4. 先用 scripts/mock_train.py 测试
5. 再接入自己的 train.py
6. 用 Dataset Inspector 检查数据集
7. 用 Experiment History 查看历史实验
```

开发者：

```text
1. 修改 trainlens_app/app.py
2. 修改 examples/example_cv_train.py
3. 修改 docs 文档
4. 用 start_trainlens.bat 测试
5. 发布前清理 .venv、runs、__pycache__
```

---

# English Guide

## 1. Introduction

TrainLens is a local visual dashboard for computer vision training tasks.

It does not implement training algorithms. Instead, it helps you launch, monitor, record, and inspect your training process.

In simple terms:

> Your `train.py` is responsible for model training.  
> TrainLens is responsible for launching, monitoring, and recording it.

TrainLens helps you:

- Start local training scripts
- Read `metrics.jsonl` in real time
- Display training progress, accuracy curves, and loss curves
- Save experiment records automatically
- View experiment history
- Inspect ImageFolder-style datasets
- Observe computer vision training more clearly

---

## 2. Project Structure

```text
TrainLens/
├─ setup_trainlens.bat          # First-time setup
├─ start_trainlens.bat          # Start TrainLens
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

## 3. First-Time Setup

### Step 1: Install Python

Recommended version:

```text
Python 3.10 or Python 3.11
```

When installing Python, make sure to check:

```text
Add Python to PATH
```

Download Python from:

```text
https://www.python.org/downloads/
```

---

### Step 2: Install TrainLens Environment

After extracting the project folder, double-click:

```text
setup_trainlens.bat
```

It will automatically:

- Check Python
- Create the `.venv` virtual environment
- Install dependencies such as Streamlit, Plotly, Pandas, NumPy, and Pillow

When setup is complete, you will see:

```text
TrainLens setup finished.
You can now run start_trainlens.bat
```

---

## 4. Start TrainLens

After setup, double-click:

```text
start_trainlens.bat
```

The browser should open automatically:

```text
http://localhost:8501
```

If the browser does not open, copy the address manually into your browser.

---

## 5. Quick Test

After opening the Dashboard for the first time, test it with the default mock training script.

Keep the sidebar settings as default:

```text
Training Script: scripts/mock_train.py
Train Directory: ./dataset/train
Validation Directory: ./dataset/val
Epochs: 5
Learning Rate: 0.001
Batch Size: 16
Device: auto
```

Click:

```text
Start Training
```

Expected behavior:

- Status changes to Running
- Progress gauge starts increasing
- Accuracy and Loss curves start updating
- Status becomes Finished after training ends
- Experiment folders such as `runs/exp_001` are created automatically

---

## 6. Main Features

### 6.1 Training Dashboard

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

### 6.2 Experiment History

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

### 6.3 Dataset Inspector

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

## 7. Using Your Own Training Script

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

### 7.1 Required Command-Line Arguments

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

### 7.2 Required metrics.jsonl Output

Your training script should write one JSON line to the file specified by `--log` after each epoch.

Example:

```json
{"epoch":1,"total_epoch":20,"progress":5.0,"train_loss":0.823,"val_loss":0.756,"acc":0.612,"best_acc":0.612,"best_loss":0.756,"lr":0.001,"batch":16,"device":"auto"}
```

Each line must be a valid JSON object. This format is called JSONL.

---

### 7.3 Field Definitions

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

### 7.4 Example Metric Writing Code

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

## 8. FAQ

### 8.1 setup_trainlens.bat says Python was not found

Reason:

- Python is not installed
- Add Python to PATH was not checked during installation

Solution:

Install Python 3.10 or 3.11 and check Add Python to PATH.

---

### 8.2 setup_trainlens.bat fails to install dependencies

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

### 8.3 start_trainlens.bat says .venv was not found

Reason:

The setup script has not been run yet.

Solution:

Run:

```text
setup_trainlens.bat
```

---

### 8.4 Browser cannot open http://localhost:8501

Possible reasons:

- Streamlit did not start successfully
- Port 8501 is already in use
- There is an error in the bat window

Solutions:

- Check the error message in the command window
- Close other Streamlit programs
- Run `start_trainlens.bat` again

---

### 8.5 No curves appear after clicking Start Training

Check:

- Whether the training script path is correct
- Whether the training script supports `--log`
- Whether `metrics.jsonl` is generated
- Whether every line in `metrics.jsonl` is valid JSON
- Whether the file is flushed after each write

---

## 9. Clear Experiment Records

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

## 10. Current Limitations

Current limitations:

- Object detection bbox visualization is not supported yet
- Segmentation mask visualization is not supported yet
- YOLO, ResNet, UNet, and other algorithms are not built in
- Cloud sync is not supported
- Multi-user collaboration is not supported
- Database storage is not supported
- EXE packaging is not available yet
- User training scripts must follow the CLI + JSONL protocol

---

## 11. Recommended Workflow

For normal users:

```text
1. Extract TrainLens
2. Double-click setup_trainlens.bat
3. Double-click start_trainlens.bat
4. Test with scripts/mock_train.py first
5. Connect your own train.py
6. Use Dataset Inspector to check your dataset
7. Use Experiment History to review training runs
```

For developers:

```text
1. Modify trainlens_app/app.py
2. Modify examples/example_cv_train.py
3. Modify docs if needed
4. Test with start_trainlens.bat
5. Clean .venv, runs, and __pycache__ before release
```

---

## 12. Summary

TrainLens does not train models for you.

It makes your training process more visible:

- Launch
- Monitor
- Record
- Compare
- Inspect datasets