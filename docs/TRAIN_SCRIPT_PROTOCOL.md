# TrainLens 训练脚本协议

本文档定义了训练脚本如何接入 TrainLens Dashboard 的标准协议。

## 概述

TrainLens 通过 **命令行参数** 启动训练脚本，并通过 **JSONL 日志文件** 读取训练指标。

## CLI 参数协议

训练脚本必须支持以下命令行参数：

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--train` | string | 训练数据目录 | `./dataset/train` |
| `--val` | string | 验证数据目录 | `./dataset/val` |
| `--epochs` | int | 训练轮数 | `20` |
| `--lr` | float | 学习率 | `0.001` |
| `--batch` | int | 批大小 | `16` |
| `--device` | string | 设备选择 | `auto`, `cpu`, `cuda` |
| `--log` | string | 指标日志文件路径 | `runs/current/metrics.jsonl` |

### 参数解析示例

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", required=True)
    parser.add_argument("--val", required=True)
    parser.add_argument("--epochs", required=True, type=int)
    parser.add_argument("--lr", required=True, type=float)
    parser.add_argument("--batch", required=True, type=int)
    parser.add_argument("--device", required=True)
    parser.add_argument("--log", required=True)
    return parser.parse_args()
```

## JSONL 日志协议

### 格式要求

- 每个 epoch 完成后写入 **一行** JSON
- 使用 UTF-8 编码
- 写入后必须调用 `flush()`

### 必需字段

| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `epoch` | int | 1 ~ total_epoch | 当前 epoch |
| `total_epoch` | int | > 0 | 总 epoch 数 |
| `progress` | float | 0 ~ 100 | 训练进度百分比 |
| `train_loss` | float | ≥ 0 | 训练集损失 |
| `val_loss` | float | ≥ 0 | 验证集损失 |
| `acc` | float | 0 ~ 1 | 验证集准确率 |
| `best_acc` | float | 0 ~ 1 | 历史最佳准确率 |
| `best_loss` | float | ≥ 0 | 历史最佳损失 |

### 写入函数实现

```python
import json

def write_metric(log_path, data):
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
        f.flush()  # 重要：立即刷新
```

### 使用示例

```python
for epoch in range(1, args.epochs + 1):
    train_loss = train_one_epoch(model, train_loader)
    val_loss, val_acc = validate(model, val_loader)
    
    best_acc = max(best_acc, val_acc)
    best_loss = min(best_loss, val_loss)
    
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

## 常见错误

### 错误 1：不支持 --log 参数

**解决：** 在 argparse 中添加
```python
parser.add_argument("--log", required=True)
```

### 错误 2：写入后没有 flush

**解决：** 每次写入后调用
```python
f.flush()
```

### 错误 3：progress 写成 0.2 而不是 20

**错误：**
```python
progress = epoch / args.epochs  # 0.05, 0.10
```

**正确：**
```python
progress = round(epoch / args.epochs * 100, 2)  # 5.0, 10.0
```

### 错误 4：acc 写成 92 而不是 0.92

**错误：**
```python
acc = correct / total * 100  # 92.5
```

**正确：**
```python
acc = correct / total  # 0.925
```

### 错误 5：device 选择 cuda 但 CUDA 不可用

**解决：**
```python
def get_device(device_arg):
    if device_arg == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    elif device_arg == "cuda":
        if not torch.cuda.is_available():
            return "cpu"
        return "cuda"
    else:
        return "cpu"
```

## 最小接入代码

### 1. 添加命令行参数

```python
parser.add_argument("--log", required=True)
```

### 2. 创建日志文件

```python
from pathlib import Path
log_path = Path(args.log)
log_path.parent.mkdir(parents=True, exist_ok=True)
```

### 3. 训练循环中写入指标

```python
import json

for epoch in range(1, args.epochs + 1):
    # 训练代码
    train_loss = train_one_epoch(...)
    val_loss, val_acc = validate(...)
    
    best_acc = max(best_acc, val_acc)
    best_loss = min(best_loss, val_loss)
    
    metrics = {
        'epoch': epoch,
        'total_epoch': args.epochs,
        'progress': round(epoch / args.epochs * 100, 2),
        'train_loss': round(train_loss, 6),
        'val_loss': round(val_loss, 6),
        'acc': round(val_acc, 6),
        'best_acc': round(best_acc, 6),
        'best_loss': round(best_loss, 6),
    }
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(metrics) + '\n')
        f.flush()
```

## 完整示例

参考项目中的示例脚本：

- **scripts/mock_train.py** - 轻量级模拟脚本
- **examples/example_cv_train.py** - 完整的 PyTorch CV 训练脚本

## 测试清单

1. 点击 Start Training 能启动训练
2. Dashboard 1-2 秒内显示进度轮盘
3. 进度轮盘从 0% 增长到 100%
4. Current Acc / Best Acc 正确显示
5. Loss 和 Accuracy 曲线实时绘制
6. Training History 表格显示所有 epoch
7. 训练结束后生成 summary.json

## 框架兼容性

TrainLens 协议与框架无关，支持：

- PyTorch
- TensorFlow / Keras
- JAX / Flax
- PaddlePaddle
- 任何能写 JSON 文件的语言和框架

## 总结

遵守 TrainLens 协议只需要：

1. 支持 7 个命令行参数
2. 每个 epoch 写一行 JSON 到日志文件
3. 写入后 flush
4. progress 是 0-100，acc 是 0-1
