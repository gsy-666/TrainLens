# TrainLens

A real-time training dashboard for computer vision and deep learning projects.

## 🚀 Quick Start

1. **Double-click `start_trainlens.bat`** to launch the dashboard
2. The dashboard will open in your browser at `http://localhost:8501`
3. Configure your training parameters in the sidebar
4. Click **Start Training** to begin

## 📋 Requirements

- Python 3.8+
- Dependencies (auto-installed on first run):
  - streamlit >= 1.28.0
  - pandas >= 2.0.0
  - plotly >= 5.17.0
  - psutil >= 5.9.0

## 🎯 Features

### Core Functionality
- **Real-time Monitoring**: Live updates of training metrics (loss, accuracy, progress)
- **Interactive Charts**: Plotly-powered loss and accuracy curves
- **Process Management**: Start/Stop training with one click
- **Configuration Persistence**: Automatically saves your last training configuration
- **Training History**: View all metrics in a sortable data table

### Dashboard Layout
- **Sidebar**: Training configuration (script path, data directories, hyperparameters)
- **Metrics Cards**: Quick view of current progress, epoch, accuracy, and loss
- **Charts**: Side-by-side loss and accuracy curves
- **Data Table**: Complete training history

## 📁 Project Structure

```
TrainLens/
├── start_trainlens.bat          # One-click launcher
├── trainlens_app/
│   ├── app.py                   # Streamlit dashboard
│   └── requirements.txt         # Python dependencies
├── scripts/
│   └── mock_train.py            # Example training script
├── metrics.jsonl                # Training metrics output (auto-generated)
└── trainlens_config.json        # Saved configuration (auto-generated)
```

## 🔧 Training Script Integration

Your training script should write metrics to `metrics.jsonl` in JSONL format:

```python
import json

# After each epoch
metrics = {
    'epoch': epoch,
    'train_loss': train_loss,
    'train_acc': train_acc,
    'val_loss': val_loss,
    'val_acc': val_acc,
    'progress': (epoch / total_epochs) * 100,
    'timestamp': datetime.now().isoformat()
}

with open('metrics.jsonl', 'a') as f:
    f.write(json.dumps(metrics) + '\n')
    f.flush()
```

### Expected Command-line Arguments

TrainLens passes these arguments to your training script:

- `--train-dir`: Training data directory
- `--val-dir`: Validation data directory
- `--epochs`: Number of epochs
- `--lr`: Learning rate
- `--batch-size`: Batch size
- `--device`: Device (auto/cpu/cuda)

## 📊 Metrics Format

Each line in `metrics.jsonl` should be a JSON object with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `epoch` | int | Current epoch number |
| `train_loss` | float | Training loss |
| `train_acc` | float | Training accuracy (0-1 range) |
| `val_loss` | float | Validation loss |
| `val_acc` | float | Validation accuracy (0-1 range) |
| `progress` | float | Training progress (0-100 range) |
| `timestamp` | string | ISO timestamp (optional) |

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

1. Launch dashboard: `start_trainlens.bat`
2. Configure in sidebar:
   - Script: `scripts/mock_train.py`
   - Train dir: `./dataset/train`
   - Val dir: `./dataset/val`
   - Epochs: `20`
   - Learning rate: `0.001`
   - Batch size: `16`
3. Click **Start Training**
4. Watch real-time metrics and charts update

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
