#!/usr/bin/env python3
"""Mock training script for TrainLens V0."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mock train loop for TrainLens")
    parser.add_argument("--train", required=True)
    parser.add_argument("--val", required=True)
    parser.add_argument("--epochs", required=True, type=int)
    parser.add_argument("--lr", required=True, type=float)
    parser.add_argument("--batch", required=True, type=int)
    parser.add_argument("--device", required=True)
    parser.add_argument("--log", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rng = random.Random(42)
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print("Mock training started", flush=True)
    print(f"train={args.train}", flush=True)
    print(f"val={args.val}", flush=True)
    print(f"epochs={args.epochs} lr={args.lr} batch={args.batch} device={args.device}", flush=True)
    print(f"log={log_path}", flush=True)

    best_acc = 0.0
    best_loss = float("inf")

    with log_path.open("w", encoding="utf-8", newline="\n") as handle:
      for epoch in range(1, args.epochs + 1):
          progress = round(epoch / args.epochs * 100, 2)
          noise = rng.uniform(-0.5, 0.5)
          train_loss = max(0.05, 1.15 * math.exp(-epoch / args.epochs * 2.2) + 0.06 * noise)
          val_loss = max(0.05, train_loss + 0.03 + 0.04 * rng.uniform(-0.5, 0.5))
          acc = min(0.999, 0.45 + 0.52 * (epoch / args.epochs) + 0.02 * rng.uniform(-0.5, 0.5))
          best_acc = max(best_acc, acc)
          best_loss = min(best_loss, val_loss)

          record = {
              "epoch": epoch,
              "total_epoch": args.epochs,
              "progress": progress,
              "train_loss": round(train_loss, 6),
              "val_loss": round(val_loss, 6),
              "acc": round(acc, 6),
              "best_acc": round(best_acc, 6),
              "best_loss": round(best_loss, 6),
              "lr": args.lr,
              "device": args.device,
          }
          handle.write(json.dumps(record, ensure_ascii=False) + "\n")
          handle.flush()

          print(
              f"epoch {epoch}/{args.epochs} | acc={record['acc']:.4f} | "
              f"val_loss={record['val_loss']:.4f} | device={args.device}",
              flush=True,
          )
          time.sleep(0.5)

    print("Mock training finished", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Mock training interrupted", flush=True)
        raise SystemExit(130)
