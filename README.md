# TrainLens V1.3

A real-time training dashboard for computer vision and deep learning projects with automatic experiment tracking and dataset inspection.

## 🚀 Quick Start

1. **Double-click `start_trainlens.bat`** to launch the dashboard
2. The dashboard will open in your browser at `http://localhost:8501`
3. Configure your training parameters in the sidebar
4. Click **Start Training** to begin
5. Each training run is automatically saved as exp_001, exp_002, etc.

## 📋 Requirements

- Python 3.8+
- Dependencies (auto-installed on first run):
  - streamlit >= 1.28.0
  - pandas >= 2.0.0
  - plotly >= 5.17.0
  - psutil >= 5.9.0
  - numpy < 2.0.0

## 🎯 Features

### V1.3 - Dataset Inspector
- **Dataset Statistics**: Automatic scanning of ImageFolder datasets
- **Class Distribution**: Visual charts showing train/val distribution per class
- **Imbalance Detection**: Calculate and display class imbalance ratio
- **Image Preview**: Random sampling of 8 training images with class labels
- **Real-time Refresh**: Update statistics without restarting dashboard

### V1.2 - Training Script Integration
- **Example CV Script**: Complete PyTorch training script template
- **Protocol Documentation**: Detailed CLI and JSONL format specification
- **Dual Mode Support**: Works with or without PyTorch installed
- **Easy Integration**: Simple guide for connecting custom training scripts

### V1.1 - Experiment Tracking
- **Automatic Experiment IDs**: Each training run gets a unique ID (exp_001, exp_002...)
- **Experiment History**: View all past experiments with metrics comparison
- **Config Archiving**: Every experiment saves its configuration
- **Training Logs**: Full stdout/stderr saved to train.log
- **Summary Reports**: Automatic generation of experiment summaries

### Core Functionality
- **Real-time Monitoring**: Live updates of training metrics (loss, accuracy, progress)
- **Progress Wheel**: Circular gauge showing 0-100% training progress
- **Interactive Charts**: Plotly-powered loss and accuracy curves
- **Process Management**: Start/Stop training with one click
- **Configuration Persistence**: Automatically saves your last training configuration

### Dashboard Layout
- **Current Training Tab**: Real-time monitoring with progress wheel and curves
- **Experiment History Tab**: Compare all experiments, view details and logs
- **Dataset Inspector Tab**: Check dataset quality, class distribution, and preview images
- **Sidebar**: Training configuration with live experiment info
- **Metrics Cards**: Current/Best Acc, Current/Best Loss
- **Charts**: Loss curves (Train/Val/Best) and Accuracy curves

## 📁 Project Structure

```
TrainLens/
├── start_trainlens.bat          # One-click launcher
├── venv/                        # Virtual environment (auto-created)
├── trainlens_app/
│   ├── app.py                   # Streamlit dashboard V1.1
│   └── requirements.txt         # Python dependencies
├── scripts/
│   └── mock_train.py            # Example training script
├── runs/
│   ├── current/
│   │   └── metrics.jsonl        # Real-time metrics
│   ├── exp_001/
│   │   ├── config.json          # Experiment config
│   │   ├── metrics.jsonl        # Archived metrics
│   │   ├── train.log            # Training output
│   │   └── summary.json         # Results summary
│   ├── exp_002/
│   └── exp_003/
└── trainlens_config.json        # Last used configuration
```

## 🔧 接入自己的训练脚本

### 快速开始

TrainLens 使用简单的 **CLI + JSONL** 协议与训练脚本通信。

**示例脚本：**
- `scripts/mock_train.py` - 轻量级模拟脚本
- `examples/example_cv_train.py` - 完整的 PyTorch CV 训练脚本（支持无 torch 运行）

### 必需的命令行参数

你的训练脚本必须支持这 7 个参数：

```bash
python train.py \
  --train ./dataset/train \
  --val ./dataset/val \
  --epochs 20 \
  --lr 0.001 \
  --batch 16 \
  --device auto \
  --log runs/current/metrics.jsonl
```

### 必需的 JSONL 输出

每个 epoch 后写入一行 JSON：

```python
import json

def write_metric(log_path, data):
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data) + '\n')
        f.flush()  # 重要：立即刷新

# 训练循环
for epoch in range(1, args.epochs + 1):
    train_loss = train_one_epoch(...)
    val_loss, val_acc = validate(...)
    
    metrics = {
        'epoch': epoch,
        'total_epoch': args.epochs,
        'progress': round(epoch / args.epochs * 100, 2),  # 0-100
        'train_loss': round(train_loss, 6),
        'val_loss': round(val_loss, 6),
        'acc': round(val_acc, 6),  # 0-1
        'best_acc': round(best_acc, 6),
        'best_loss': round(best_loss, 6),
    }
    
    write_metric(args.log, metrics)
```

### 字段规范

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `epoch` | int | 1+ | 当前 epoch |
| `total_epoch` | int | 1+ | 总 epoch 数 |
| `progress` | float | 0-100 | 训练进度百分比 |
| `train_loss` | float | ≥0 | 训练损失 |
| `val_loss` | float | ≥0 | 验证损失 |
| `acc` | float | 0-1 | 验证准确率 |
| `best_acc` | float | 0-1 | 历史最佳准确率 |
| `best_loss` | float | ≥0 | 历史最佳损失 |

### 完整协议文档

详见 **[docs/TRAIN_SCRIPT_PROTOCOL.md](docs/TRAIN_SCRIPT_PROTOCOL.md)**，包括：
- CLI 参数详细说明
- JSONL 格式要求
- 常见错误及解决方案
- 最小接入代码
- 框架兼容性说明

## 🎨 Dashboard Features

### Configuration Panel
- **Script Path**: Path to your training script
- **Data Directories**: Training and validation data locations
- **Hyperparameters**: Epochs, learning rate, batch size, device selection
- **Auto-save**: Last configuration is saved to `trainlens_config.json`

### Real-time Updates
- Dashboard auto-refreshes every second during training
- No manual refresh needed
- Process status indicator shows running/idle state

### Process Control
- **Start Training**: Launches your script with configured parameters
- **Stop Training**: Gracefully terminates the training process
- Process PID display for advanced monitoring

## 🛠️ Manual Installation

If you prefer not to use the batch file:

```bash
# Install dependencies
pip install -r trainlens_app/requirements.txt

# Start dashboard
streamlit run trainlens_app/app.py
```

## 📝 Example Usage

### Basic Training Workflow

1. Launch dashboard: `start_trainlens.bat`
2. Configure in sidebar:
   - Script: `scripts/mock_train.py`
   - Train dir: `./dataset/train`
   - Val dir: `./dataset/val`
   - Epochs: `20`
   - Learning rate: `0.001`
   - Batch size: `16`
3. **(Optional) Check your dataset first:**
   - Click **Dataset Inspector** tab
   - Review class distribution and imbalance ratio
   - Preview random training images
   - Verify dataset quality before training
4. Click **Start Training**
5. Watch real-time metrics and charts update

### Dataset Inspector Usage

1. Configure dataset paths in sidebar (Train Directory, Validation Directory)
2. Navigate to **🔍 Dataset Inspector** tab
3. View dataset statistics:
   - Total images (train/val)
   - Number of classes
   - Class imbalance ratio
4. Check class distribution table and chart
5. Preview random training images
6. Click **🔄 Refresh Dataset Stats** to rescan or get new samples

**详细文档:** [docs/DATASET_INSPECTOR.md](docs/DATASET_INSPECTOR.md)

## 🔍 Troubleshooting

### Dashboard won't start
- Check Python is installed: `python --version`
- Verify you're in the TrainLens directory
- Try manual installation steps above

### Training won't start
- Verify your script path exists
- Check that data directories exist
- Review terminal output for Python errors

### Metrics not showing
- Ensure your script writes to `metrics.jsonl`
- Check JSONL format matches expected schema
- Verify file permissions

### Process won't stop
- Use Task Manager to manually kill the process
- Check PID shown in dashboard status

### Dataset Inspector issues
- **Classes = 0**: Check if dataset follows ImageFolder format (dataset/train/class_name/*.jpg)
- **Images not loading**: Verify image file permissions and formats (jpg, png, bmp, gif supported)
- **High imbalance ratio**: Consider data augmentation or weighted sampling in training script
- **Path not found**: Use relative paths from TrainLens root or absolute paths

## 🚧 VS Code Extension (Coming Soon)

A simplified VS Code extension will be added as a launcher:
- Command: `TrainLens: Open Dashboard`
- Opens browser to dashboard automatically
- No complex Webview or embedded UI
- Pure launcher functionality

## 📄 License

MIT License - feel free to modify and distribute.

## 🤝 Contributing

This is a local development tool. Modify `trainlens_app/app.py` to customize the dashboard for your needs.
