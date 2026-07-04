# Start Training 按钮修复测试

## ✅ 已修复的问题

### 1. mock_train.py progress 字段
**修改前：**
```python
progress = epoch / args.epochs  # 输出 0.0 ~ 1.0
"progress": round(progress, 6)  # 例如 0.2
```

**修改后：**
```python
progress = round(epoch / args.epochs * 100, 2)  # 输出 0.0 ~ 100.0
"progress": progress  # 例如 20.0
```

### 2. Webview progress 兼容处理
**修改后：**
```javascript
function updateProgress(latest) {
  let ratio = 0;
  if (latest && typeof latest.progress === 'number') {
    const prog = latest.progress;
    ratio = prog <= 1 ? prog : prog / 100;  // 兼容两种格式
  } else if (epoch && totalEpoch) {
    ratio = epoch / totalEpoch;
  }
  ratio = clamp(ratio, 0, 1);
  // ...
}
```

### 3. 通信链路检查
✅ Webview JavaScript 正确：
- `const vscode = acquireVsCodeApi()` ✅
- Start 按钮绑定了 click 事件 ✅
- `vscode.postMessage({ type: 'start', state: readFormState() })` ✅
- Stop 按钮: `vscode.postMessage({ type: 'stop' })` ✅
- `window.addEventListener('message', ...)` 处理返回消息 ✅

✅ Extension.ts 正确：
- `panel.webview.onDidReceiveMessage(...)` ✅
- `handleWebviewMessage` 处理 'start' 和 'stop' ✅
- `startTraining(message.state)` 被调用 ✅
- `spawn('python', args, { cwd: this.workspaceRoot, ... })` ✅
- stdout/stderr 通过 `postToWebview({ type: 'log', entry: ... })` 发送 ✅

---

## 🧪 测试步骤

### 第一步：清理旧的 metrics 文件
```bash
rm -rf runs/current/metrics.jsonl
```

### 第二步：启动调试
1. 在主 VS Code 窗口按 **Ctrl+F5**（无调试模式）
2. 等待 Extension Development Host 启动

### 第三步：打开 Dashboard
1. 在 Extension Development Host 中按 **Ctrl+Shift+P**
2. 输入 `TrainLens: Open Dashboard`
3. 如果提示需要 workspace，打开 `C:\Users\gsy_666\Desktop\TrainLens`

### 第四步：检查默认值
Dashboard 应该显示：
- Training script: `scripts/mock_train.py` ✅
- Train set: `./dataset/train`
- Val set: `./dataset/val`
- Epochs: `20`
- Learning rate: `0.001`
- Batch size: `16`
- Device: `auto`

### 第五步：点击 Start Training
**预期行为：**
1. 状态从 `Idle` 变为 `Starting` → `Running`
2. Start Training 按钮变灰，Stop Training 按钮可用
3. Training Logs 区域显示：
   ```
   Launching: python scripts/mock_train.py --train ./dataset/train ...
   Workspace: C:\Users\gsy_666\Desktop\TrainLens
   Metrics: runs/current/metrics.jsonl
   Mock training started
   train=./dataset/train
   val=./dataset/val
   epochs=20 lr=0.001 batch=16 device=auto
   log=runs\current\metrics.jsonl
   epoch 1/20 | acc=0.4700 | val_loss=0.9500 | device=auto
   epoch 2/20 | acc=0.5200 | val_loss=0.7800 | device=auto
   ...
   ```
4. 进度轮盘开始转动（从 0% → 5% → 10% → ...）
5. Current acc / Best acc / Current loss / Best loss 实时更新
6. Accuracy 和 Loss 曲线实时绘制

### 第六步：查看 Extension Host 日志
在主 VS Code 窗口：
1. 打开 **查看 → 输出**
2. 选择 **Extension Host**
3. 应该看到：
   ```
   TrainLens extension activated
   TrainLens command registered: trainlens.openDashboard
   TrainLens dashboard command triggered
   TrainLens openDashboard called
   TrainLens workspace root: C:\Users\gsy_666\Desktop\TrainLens
   TrainLens: Creating new webview panel
   TrainLens: Webview panel created successfully
   TrainLens received message from webview: ready
   TrainLens handleWebviewMessage: ready
   TrainLens: Webview ready
   TrainLens received message from webview: start
   TrainLens handleWebviewMessage: start
   TrainLens: Start training requested
   TrainLens: startTraining called with state: { scriptPath: 'scripts/mock_train.py', ... }
   TrainLens: Spawning Python process
   TrainLens: Command: python scripts/mock_train.py --train ./dataset/train ...
   TrainLens: Working directory: C:\Users\gsy_666\Desktop\TrainLens
   ```

---

## 📋 修改文件清单

### 1. `scripts/mock_train.py`
- 修改 progress 计算：从 0~1 改为 0~100
- 修改 train_loss/acc 计算：使用 `epoch / args.epochs` 代替 `progress`

### 2. `src/extension.ts`
- 修改 `updateProgress()` 函数：兼容两种 progress 格式（0~1 和 0~100）

### 3. 已编译
- `npm run compile` 成功 ✅

---

## ✅ 验收标准

修复成功的标志：
1. ✅ 点击 Start Training 后，状态立即从 Idle 变为 Starting
2. ✅ 日志区域显示 "Launching: python scripts/mock_train.py ..."
3. ✅ 1~2 秒后日志显示 "Mock training started"
4. ✅ 每 0.5 秒日志滚动显示 "epoch 1/20 | acc=... | val_loss=..."
5. ✅ 进度轮盘实时旋转
6. ✅ 指标卡片实时更新
7. ✅ 曲线图实时绘制
8. ✅ 点击 Stop Training 能立即停止训练

现在可以测试了！
