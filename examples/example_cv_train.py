#!/usr/bin/env python3
"""
Example Computer Vision Training Script for TrainLens
A realistic PyTorch-style training script that works without PyTorch installed.
"""

import argparse
import json
import sys
import time
import random
import math
from pathlib import Path
from datetime import datetime

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("=" * 60)
    print("WARNING: PyTorch not installed. Running in fake mode.")
    print("Install with: pip install torch torchvision")
    print("=" * 60)


def parse_args():
    """Parse command line arguments following TrainLens protocol"""
    parser = argparse.ArgumentParser(description="Example CV training for TrainLens")
    parser.add_argument("--train", required=True, help="Training data directory")
    parser.add_argument("--val", required=True, help="Validation data directory")
    parser.add_argument("--epochs", required=True, type=int, help="Number of epochs")
    parser.add_argument("--lr", required=True, type=float, help="Learning rate")
    parser.add_argument("--batch", required=True, type=int, help="Batch size")
    parser.add_argument("--device", required=True, help="Device: auto, cpu, cuda")
    parser.add_argument("--log", required=True, help="Path to metrics.jsonl output")
    return parser.parse_args()


def get_device(device_arg):
    """Get PyTorch device from argument"""
    if not TORCH_AVAILABLE:
        return "cpu"

    if device_arg == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    elif device_arg == "cuda":
        if not torch.cuda.is_available():
            print("WARNING: CUDA requested but not available. Using CPU.")
            return "cpu"
        return "cuda"
    else:
        return "cpu"


def write_metric(log_path, data):
    """Write one line of metrics to JSONL file"""
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
        f.flush()


# ============ PyTorch Components (only if torch available) ============

if TORCH_AVAILABLE:
    class FakeImageDataset(Dataset):
        """Fake dataset that generates random images and labels"""
        def __init__(self, num_samples=1000, num_classes=10):
            self.num_samples = num_samples
            self.num_classes = num_classes

        def __len__(self):
            return self.num_samples

        def __getitem__(self, idx):
            # Generate fake 3x32x32 image and random label
            image = torch.randn(3, 32, 32)
            label = torch.randint(0, self.num_classes, (1,)).item()
            return image, label


    class SimpleCNN(nn.Module):
        """Simple CNN for demonstration"""
        def __init__(self, num_classes=10):
            super(SimpleCNN, self).__init__()
            self.conv1 = nn.Conv2d(3, 16, 3, padding=1)
            self.conv2 = nn.Conv2d(16, 32, 3, padding=1)
            self.pool = nn.MaxPool2d(2, 2)
            self.fc1 = nn.Linear(32 * 8 * 8, 128)
            self.fc2 = nn.Linear(128, num_classes)
            self.relu = nn.ReLU()

        def forward(self, x):
            x = self.pool(self.relu(self.conv1(x)))
            x = self.pool(self.relu(self.conv2(x)))
            x = x.view(-1, 32 * 8 * 8)
            x = self.relu(self.fc1(x))
            x = self.fc2(x)
            return x


    def train_one_epoch(model, loader, criterion, optimizer, device):
        """Train for one epoch"""
        model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for batch_idx, (inputs, targets) in enumerate(loader):
            inputs, targets = inputs.to(device), targets.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()

        avg_loss = total_loss / len(loader)
        accuracy = correct / total
        return avg_loss, accuracy


    def validate(model, loader, criterion, device):
        """Validate model"""
        model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for batch_idx, (inputs, targets) in enumerate(loader):
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)

                total_loss += loss.item()
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()

        avg_loss = total_loss / len(loader)
        accuracy = correct / total
        return avg_loss, accuracy


# ============ Fake Training Mode (when PyTorch is not available) ============

def fake_train_one_epoch(epoch, total_epochs):
    """Simulate training when PyTorch is not available"""
    # Simulate realistic training behavior
    progress_ratio = epoch / total_epochs

    # Loss decreases over time with noise
    train_loss = max(0.05, 1.2 * math.exp(-progress_ratio * 2.5) + random.uniform(-0.1, 0.1))
    val_loss = max(0.05, train_loss + 0.05 + random.uniform(-0.05, 0.05))

    # Accuracy increases over time with noise
    acc = min(0.99, 0.3 + 0.65 * progress_ratio + random.uniform(-0.03, 0.03))

    # Simulate processing time
    time.sleep(0.5)

    return train_loss, acc, val_loss


# ============ Main Training Loop ============

def main():
    args = parse_args()

    # Prepare log file
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TrainLens Example CV Training Script")
    print("=" * 60)
    print(f"Mode: {'PyTorch' if TORCH_AVAILABLE else 'Fake (PyTorch not installed)'}")
    print(f"Train dir: {args.train}")
    print(f"Val dir: {args.val}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning rate: {args.lr}")
    print(f"Batch size: {args.batch}")
    print(f"Device: {args.device}")
    print(f"Log file: {log_path}")
    print("=" * 60)

    best_acc = 0.0
    best_loss = float('inf')

    if TORCH_AVAILABLE:
        # Real PyTorch training
        device = get_device(args.device)
        print(f"Using device: {device}")

        # Create datasets and loaders
        train_dataset = FakeImageDataset(num_samples=500)
        val_dataset = FakeImageDataset(num_samples=100)

        train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=args.batch, shuffle=False)

        # Create model, loss, optimizer
        model = SimpleCNN(num_classes=10).to(device)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=args.lr)

        # Training loop
        for epoch in range(1, args.epochs + 1):
            print(f"\nEpoch {epoch}/{args.epochs}")

            # Train
            train_loss, train_acc = train_one_epoch(
                model, train_loader, criterion, optimizer, device
            )

            # Validate
            val_loss, val_acc = validate(model, val_loader, criterion, device)

            # Update best
            if val_acc > best_acc:
                best_acc = val_acc
            if val_loss < best_loss:
                best_loss = val_loss

            # Calculate progress
            progress = round(epoch / args.epochs * 100, 2)

            # Write metrics following TrainLens protocol
            metrics = {
                'epoch': epoch,
                'total_epoch': args.epochs,
                'progress': progress,  # 0-100 percentage
                'train_loss': round(train_loss, 6),
                'val_loss': round(val_loss, 6),
                'acc': round(val_acc, 6),  # 0-1 range, not 0-100
                'best_acc': round(best_acc, 6),
                'best_loss': round(best_loss, 6),
                'lr': args.lr,
                'batch': args.batch,
                'device': device,
            }

            write_metric(log_path, metrics)

            print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
            print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
            print(f"Best Acc: {best_acc:.4f} | Best Loss: {best_loss:.4f}")

    else:
        # Fake training mode (no PyTorch)
        print("\nRunning in FAKE mode (PyTorch not installed)")
        print("To use real PyTorch training: pip install torch torchvision\n")

        for epoch in range(1, args.epochs + 1):
            print(f"\nEpoch {epoch}/{args.epochs}")

            # Simulate training
            train_loss, acc, val_loss = fake_train_one_epoch(epoch, args.epochs)

            # Update best
            if acc > best_acc:
                best_acc = acc
            if val_loss < best_loss:
                best_loss = val_loss

            # Calculate progress
            progress = round(epoch / args.epochs * 100, 2)

            # Write metrics following TrainLens protocol
            metrics = {
                'epoch': epoch,
                'total_epoch': args.epochs,
                'progress': progress,  # 0-100 percentage
                'train_loss': round(train_loss, 6),
                'val_loss': round(val_loss, 6),
                'acc': round(acc, 6),  # 0-1 range
                'best_acc': round(best_acc, 6),
                'best_loss': round(best_loss, 6),
                'lr': args.lr,
                'batch': args.batch,
                'device': args.device,
            }

            write_metric(log_path, metrics)

            print(f"Train Loss: {train_loss:.4f}")
            print(f"Val Loss: {val_loss:.4f} | Val Acc: {acc:.4f}")
            print(f"Best Acc: {best_acc:.4f} | Best Loss: {best_loss:.4f}")

    print("\n" + "=" * 60)
    print("Training completed!")
    print(f"Metrics saved to: {log_path}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
        sys.exit(130)
